import json

import yt_dlp
from google import genai

from core.settings import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)

interaction = client.interactions.create(
    model="gemini-3.8-flash", input="say 1"
)
print(interaction.output_text)

client.close()

""" URL = "https://www.youtube.com/watch?v=YE7VzlLtp-4"
tmp_filename = "placeholder"
# ℹ️ See help(yt_dlp.YoutubeDL) for a list of available options and public functions
ydl_opts = {
    "format": "bestaudio/best",
    "outtmpl": tmp_filename,
    "quiet": True,
    "noplaylist": True,
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(URL, download=False)

    # ℹ️ ydl.sanitize_info makes the info json-serializable
    print(json.dumps(ydl.sanitize_info(info))) """

# Bitte beachte ebenfalls, dass die Adresse der URL, die wir speichern, exakt so aussehen muss. Du musst wie im Video erwähnt die ID extrahieren und den URL- Pfad so aufbauen. Denn wie im Video erwähnt, weißt du nie, wie das Frontend die zu verwendende URL empfängt.
# https://www.youtube.com/watch?v=ID-DES-VIDEOS


""" Based on the following transcript, generate a quiz in valid JSON format.

The quiz must follow this exact structure:

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
