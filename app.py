from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import json
from generate_script import create_podcast_script, read_pdf, read_url, read_txt, read_md, clean_podcast_script
from generate_podcast import generate_podcast
import asyncio
from pydub import AudioSegment

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        gemini_api_key = request.form.get('gemini-api-key')
        os.environ['GOOGLE_API_KEY'] = gemini_api_key

        files = request.files.getlist('file-upload')
        urls = request.form.get('url-input')
        if urls:
            try:
                urls = json.loads(urls)
            except json.JSONDecodeError:
                return jsonify({'error': 'Invalid URL format. Please provide a comma-separated list.'}), 400
        else:
            urls = []

        all_content = ""

        for file in files:
            file_ext = os.path.splitext(file.filename)[1].lower()
            if file_ext == '.pdf':
                content = read_pdf(file)
            elif file_ext == '.txt':
                content = read_txt(file)
            elif file_ext == '.md':
                   content = read_md(file)
            elif file_ext == '.mp3':
                try:
                    audio = AudioSegment.from_mp3(file)
                    content = f"MP3 file: {file.filename}"
                except Exception as e:
                    return jsonify({'error': f'Error processing MP3 file: {str(e)}'}), 500
            else:
                return jsonify({'error': 'Invalid file type'}), 400
            all_content += content

        for url in urls:
            content = read_url(url)
            all_content += content

        if all_content:
            podcast_script = create_podcast_script(all_content)
            if podcast_script:
                cleaned_script = clean_podcast_script(podcast_script)
                return jsonify({'script': cleaned_script})
            else:
                return jsonify({'error': 'Failed to generate podcast script'}), 500
        else:
            return jsonify({'error': 'Failed to extract content'}), 500

    return render_template("index.html")

@app.route("/generate-audio", methods=["POST"])
def generate_audio():
    script = request.form.get('script')
    language = request.form.get('language', 'en-US')
    generate_podcast(language, script)
    return jsonify({'status': 'Audio generation complete'}), 200

@app.route('/download-audio')
def download_audio():
    return send_from_directory(app.root_path, 'final_podcast.wav', as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)