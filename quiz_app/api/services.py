"""Placeholder fil for various code snippets. In the end this file is responsible for getting the quiz data from yt into whipser and then transforming it to an actual quiz"""

import json
import time
import os
import tempfile
import uuid
import yt_dlp
import whisper
from functools import lru_cache
from google import genai
from google.genai import errors
from django.conf import settings

QUIZ_KEYS = {
    "title",
    "description",
    "video_url",
    "questions",
}

QUESTION_KEYS = {
    "question_title",
    "question_options",
    "answer",
}

AGENT_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
]

RETRY_DELAY_SECONDS = 5


class QuizGenerationError(Exception):
    pass


QUIZ_PROMPT = """Based on the following transcript, generate a quiz in valid JSON format. The quiz must follow this exact structure:
                {{ 
                      "title": "Create a concise quiz title based on the topic of the transcript.",
                      "description": "Summarize the transcript in no more than 150 characters. Do not include any quiz questions or answers.",
                      "questions": [
                        {{
                          "question_title": "The question goes here.",
                          "question_options": ["Option A", "Option B", "Option C", "Option D"],
                          "answer": "The correct answer from the above options"
                        }},
                        ...
                        (exactly 10 questions)
                      ]                  
                    }}                 
                    Requirements:                 
                    - Each question must have exactly 4 distinct answer options.                 
                    - Only one correct answer is allowed per question, and it must be present in 'question_options'.
                    - The output must be valid JSON and parsable as-is (e.g., using Python's json.loads).
                    - Do not include explanations, comments, or any text outside the JSON. 
                    
                    Transcript: {transcript}
                    """


@lru_cache(maxsize=1)
def get_whisper_model():
    """Load the Whisper "turbo" model once and cache it.

    Returns:
        whisper.Whisper: The loaded Whisper model instance.
    """
    return whisper.load_model("turbo")


def download_audio(url):
    """Download the audio track of a YouTube video into the temp directory.

    Args:
        url (str): The url of the YouTube video.

    Returns:
        str: The file path of the downloaded audio file.

    Raises:
        QuizGenerationError: If the audio could not be downloaded.
    """
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(tempfile.gettempdir(), f"{uuid.uuid4().hex}.%(ext)s"),
        "quiet": True,
        "noplaylist": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            audio_path = ydl.prepare_filename(info)

        return audio_path
    except yt_dlp.utils.DownloadError as error:
        raise QuizGenerationError(
            "Could not download audio from youtube url"
        ) from error


def transcribe_audio(path):
    """Transcribe an audio file with Whisper and delete the file afterwards.

    Args:
        path (str): The file path of the audio file.

    Returns:
        str: The transcribed text of the audio file.

    Raises:
        QuizGenerationError: If Whisper fails to transcribe the audio.
    """
    try:
        result = get_whisper_model().transcribe(path)
        return result["text"]
    except Exception as error:
        raise QuizGenerationError("Whisper failed transcribing the audio") from error
    finally:
        os.remove(path)


def generate_quiz_by_agent(transcript):
    """Generate a quiz as a JSON string from a transcript using Gemini.

    The models in AGENT_MODELS are tried one after another. Between the
    attempts the function waits with an increasing delay.

    Args:
        transcript (str): The transcript of the video.

    Returns:
        str: The raw JSON string of the generated quiz.

    Raises:
        QuizGenerationError: If all models failed or returned an empty response.
    """
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    prompt = QUIZ_PROMPT.format(transcript=transcript)
    last_error = None
    try:
        for attempt, model in enumerate(AGENT_MODELS, start=1):
            try:
                interaction = client.interactions.create(
                    model=model,
                    input=prompt,
                    response_format={
                        "type": "text",
                        "mime_type": "application/json",
                    },
                )
                quiz = interaction.output_text
                if quiz:
                    return quiz
                last_error = QuizGenerationError(f"Empty response from {model}")
            except errors.APIError as error:
                last_error = error
            if attempt < len(AGENT_MODELS):
                time.sleep(RETRY_DELAY_SECONDS * attempt)
    finally:
        client.close()

    raise QuizGenerationError(
        f"Quiz generation failed after {len(AGENT_MODELS)} attempts"
    ) from last_error


def transform_quiz(raw, url):
    """Parse the raw JSON string into a dict and add the video url.

    Args:
        raw (str): The raw JSON string returned by the agent.
        url (str): The url of the YouTube video.

    Returns:
        dict: The quiz data including the "video_url" key.

    Raises:
        QuizGenerationError: If the string is not valid JSON.
    """
    try:
        quiz = json.loads(raw)
        quiz["video_url"] = url
        return quiz
    except json.JSONDecodeError as error:
        raise QuizGenerationError(
            "Could not generate valid JSON from string"
        ) from error


def validate_question(question):
    """Validate the structure of a single generated question.

    Args:
        question (dict): The question data to validate.

    Raises:
        QuizGenerationError: If the question is not a dict, has missing or
            additional keys, does not have exactly 4 distinct options or the
            answer is not one of the options.
    """
    if not isinstance(question, dict):
        raise QuizGenerationError("Question is not a dictionary")
    if set(question.keys()) != QUESTION_KEYS:
        raise QuizGenerationError("The questions didn't have all properties required")
    options = question["question_options"]
    if not isinstance(options, list):
        raise QuizGenerationError("Question options were not in list format")
    if len(options) != 4 or len(set(options)) != 4:
        raise QuizGenerationError("Not all questions had 4 distinct answers")
    if question["answer"] not in options:
        raise QuizGenerationError(
            "Not all questions had answer included in the choices"
        )


def validate_quiz(data):
    """Validate the structure of the generated quiz and all of its questions.

    Args:
        data (dict): The quiz data to validate.

    Returns:
        dict: The validated quiz data.

    Raises:
        QuizGenerationError: If the quiz is not a dict, has missing or
            additional keys, does not contain exactly 10 questions or a
            question is invalid.
    """
    if not isinstance(data, dict):
        raise QuizGenerationError("Data is not a dictionary")
    if set(data.keys()) != QUIZ_KEYS:
        raise QuizGenerationError("The quiz didn't have all properties required")
    if not isinstance(data["questions"], list):
        raise QuizGenerationError("Questions were not in list format")
    if len(data["questions"]) != 10:
        raise QuizGenerationError("There were not exactly 10 questions generated")
    for question in data["questions"]:
        validate_question(question)
    return data


def generate_quiz_from_url(url):
    """Run the whole workflow to generate a quiz from a YouTube url.

    Downloads the audio, transcribes it, lets the agent generate the quiz,
    parses the result and validates it.

    Args:
        url (str): The url of the YouTube video.

    Returns:
        dict: The validated quiz data.

    Raises:
        QuizGenerationError: If any step of the workflow fails.
    """
    path = download_audio(url)
    transcript = transcribe_audio(path)
    raw_quiz = generate_quiz_by_agent(transcript)
    quiz = transform_quiz(raw_quiz, url)
    quiz = validate_quiz(quiz)
    return quiz
