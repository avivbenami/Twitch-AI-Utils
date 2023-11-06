import speech_recognition as sr
from pydub import AudioSegment
from pydub.silence import split_on_silence
import subprocess
import openai
import shutil
import os
from pathlib import Path

class AudioProcessor:
    def __init__(self, openai_api_key_path='openaikey.txt'):
        self.r = sr.Recognizer()
        self.openai_api_key_path = openai_api_key_path
        self.track = 'temp_track.wav'

    def _clean(self):
        dirpath = Path('audio-chunks')
        if dirpath.exists() and dirpath.is_dir():
            shutil.rmtree(dirpath)
        if os.path.exists(self.track):
            os.remove(self.track)

    def transcribe_audio(self, path):
        with sr.AudioFile(path) as source:
            audio_listened = self.r.record(source)
            text = self.r.recognize_google(audio_listened)
        return text

    def get_large_audio_transcription_on_silence(self, path):
        sound = AudioSegment.from_file(path)
        chunks = split_on_silence(
            sound,
            min_silence_len=500,
            silence_thresh=sound.dBFS - 14,
            keep_silence=500,
        )
        folder_name = "audio-chunks"
        if not os.path.isdir(folder_name):
            os.mkdir(folder_name)
        whole_text = ""
        for i, audio_chunk in enumerate(chunks, start=1):
            chunk_filename = os.path.join(folder_name, f"chunk{i}.wav")
            audio_chunk.export(chunk_filename, format="wav")
            try:
                text = self.transcribe_audio(chunk_filename)
            except sr.UnknownValueError:
                text = ""
            else:
                text = f"{text.capitalize()}. "
                whole_text += text
        return whole_text

    def process_audio(self, playlist, start_time, end_time):
        self._clean()
        openai.api_key_path = self.openai_api_key_path
        subprocess.run([
            'ffmpeg', '-hide_banner', '-loglevel', 'error',
            '-ss', str(start_time), '-to', str(end_time),
            '-i', playlist, self.track
        ])
        return self.get_large_audio_transcription_on_silence(self.track)

    def ai_summarize(self, text):
        openai.api_key_path = self.openai_api_key_path
        text = 'Can you summarize the following text: {text}'.format(text=text)
        messages = [{"role": "system", "content": "You are an intelligent assistant."}]

        if text:
            messages.append(
                {"role": "user", "content": text},
            )
            chat = openai.ChatCompletion.create(
                model="gpt-3.5-turbo", messages=messages
            )
            reply = chat.choices[0].message.content
            return str(reply)
        return None
