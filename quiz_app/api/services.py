import json

import yt_dlp

URL = 'https://www.youtube.com/watch?v=YE7VzlLtp-4'
tmp_filename ="placeholder"
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
    print(json.dumps(ydl.sanitize_info(info)))
    
#Bitte beachte ebenfalls, dass die Adresse der URL, die wir speichern, exakt so aussehen muss. Du musst wie im Video erwähnt die ID extrahieren und den URL- Pfad so aufbauen. Denn wie im Video erwähnt, weißt du nie, wie das Frontend die zu verwendende URL empfängt.
#https://www.youtube.com/watch?v=ID-DES-VIDEOS
    