"""Placeholder fil for various code snippets. In the end this file is responsible for getting the quiz data from yt into whipser and then transforming it to an actual quiz"""

import json
import yt_dlp
import whisper
from google import genai 
from django.conf import settings



tmp_filename = "placeholder"
ydl_opts = {
    "format": "bestaudio/best",
    "outtmpl": tmp_filename,
    "quiet": True,
    "noplaylist": True,
}


class QuizGenerationError(Exception):
    pass


QUIZ_DATA = {
    "title": "Quiz Title",
    "description": "Quiz Description",
    "video_url": "https://www.youtube.com/watch?v=example",
    "questions": [
        {
            "question_title": "Question 1",
            "question_options": ["Option A", "Option B", "Option C", "Option D"],
            "answer": "Option A",
        },
        {
            "question_title": "Question 2",
            "question_options": ["Option A", "Option B", "Option C", "Option D"],
            "answer": "Option A",
        },
        {
            "question_title": "Question 3",
            "question_options": ["Option A", "Option B", "Option C", "Option D"],
            "answer": "Option A",
        },
        {
            "question_title": "Question 4",
            "question_options": ["Option A", "Option B", "Option C", "Option D"],
            "answer": "Option A",
        },
        {
            "question_title": "Question 5",
            "question_options": ["Option A", "Option B", "Option C", "Option D"],
            "answer": "Option A",
        },
        {
            "question_title": "Question 6",
            "question_options": ["Option A", "Option B", "Option C", "Option D"],
            "answer": "Option A",
        },
        {
            "question_title": "Question 7",
            "question_options": ["Option A", "Option B", "Option C", "Option D"],
            "answer": "Option A",
        },
        {
            "question_title": "Question 8",
            "question_options": ["Option A", "Option B", "Option C", "Option D"],
            "answer": "Option A",
        },
        {
            "question_title": "Question 9",
            "question_options": ["Option A", "Option B", "Option C", "Option D"],
            "answer": "Option A",
        },
        {
            "question_title": "Question 10",
            "question_options": ["Option A", "Option B", "Option C", "Option D"],
            "answer": "Option A",
        },
    ],
}

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
                    - Do not include explanations, comments, or any text outside the JSON. """

def validate_quiz_data(data):
    pass

def generate_quiz_from_url(url):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    audio_file= json.dumps(ydl.sanitize_info(info))
    model = whisper.load_model("turbo")
    result = model.transcribe(audio_file)
   
    
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    interaction = client.interactions.create(model="gemini-3.8-flash", input=QUIZ_PROMPT,result)
    quiz=interaction.output_text
    
    client.close()
    try:
            validate_quiz_data(quiz)
    except QuizGenerationError:
        return raise()
    
    return quiz
  

     











