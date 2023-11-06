import os
import shutil
from flask import Flask, render_template, request, abort
from audio_ai_utils import AudioProcessor
from twitch_utils import StreamManager

app = Flask(__name__)
app.config['DEBUG'] = True

audio_processor = AudioProcessor()
stream_manager = StreamManager()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        stream_name = request.form.get("stream_name")
        stream_data = stream_manager.get_stream_urls_and_data(stream_name)
        return render_template("result.html", stream_data=stream_data)
    return render_template("index.html")

@app.route('/result2', methods=['GET'])
def result2():
    return render_template('result2.html', response=None)

@app.route('/result3', methods=["POST"])
def result3():
    playlist = request.form.get('playlist')
    start_time = request.form.get('start_time')
    end_time = request.form.get('end_time')

    if not playlist or not start_time or not end_time:
        abort(400, "Error: 'playlist', 'start_time', and 'end_time' fields are required.")

    playlist_url = stream_manager.get_m3u8(playlist, True)
    start_time = float(start_time)
    end_time = float(end_time)

    if not playlist_url:
        abort(400, "Error: Stream not available on Twitch servers.")

    try:
        transcription = audio_processor.process_audio(playlist_url, start_time, end_time)
        if not transcription:
            abort(500, "Error: No transcription was extracted")
        static_dir = "static"
        if not os.path.exists(static_dir):
            os.makedirs(static_dir)
        shutil.copyfile("temp_track.wav", os.path.join(static_dir, "temp_track.wav"))
        summarization = audio_processor.ai_summarize(transcription)
        if not summarization:
            abort(500, "Error: Was not able to recive summarization from ChatGPT")
        response = {'transcription': transcription, 'summarization': summarization}
        return render_template('result3.html', response=response)
    except Exception as e:
        abort(500, f"An error occurred: {str(e)}")

if __name__ == "__main__":
    app.run()
