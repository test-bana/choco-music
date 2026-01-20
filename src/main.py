import sys
import os
from flask import Flask, render_template, request, redirect, url_for, send_file, flash, Response
from flask_sqlalchemy import SQLAlchemy
import io
from datetime import datetime
from werkzeug.utils import secure_filename

# Add current directory to path to ensure local imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_config import get_sqlalchemy_uri

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'choco-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = get_sqlalchemy_uri()

app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB limit

db = SQLAlchemy(app)

class Music(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)  # MP3 data stored as BLOB
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    music_list = Music.query.order_by(Music.uploaded_at.desc()).all()
    return render_template('index.html', music_list=music_list)

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        flash('ファイルがありません')
        return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '':
        flash('ファイルが選択されていません')
        return redirect(url_for('index'))
    
    allowed_extensions = {'.mp3', '.mp4'}
    if file and file.filename:
        filename_str = str(file.filename)
        file_ext = os.path.splitext(filename_str)[1].lower()
        
        if file_ext in allowed_extensions:
            safe_filename = secure_filename(filename_str)
            file_data = file.read()
            new_music = Music()
            new_music.filename = safe_filename
            new_music.title = filename_str
            new_music.data = file_data
            db.session.add(new_music)
            db.session.commit()
            flash('アップロード成功！')
        else:
            flash('MP3またはMP4ファイルのみ対応しています')
    else:
        flash('ファイル名が無効です')
    return redirect(url_for('index'))

@app.route('/stream/<int:music_id>')
def stream(music_id):
    music = Music.query.get_or_404(music_id)
    data = music.data
    size = len(data)
    mimetype = 'video/mp4' if music.filename.lower().endswith('.mp4') else 'audio/mpeg'

    range_header = request.headers.get('Range', None)
    if not range_header:
        return Response(data, mimetype=mimetype)

    # Simple Range header parsing (e.g., "bytes=0-100")
    try:
        byte_range = range_header.replace('bytes=', '').split('-')
        start = int(byte_range[0])
        end = int(byte_range[1]) if byte_range[1] else size - 1
    except (ValueError, IndexError):
        return Response(data, mimetype=mimetype)

    if start >= size:
        return Response(status=416)

    end = min(end, size - 1)
    chunk_data = data[start:end+1]
    
    rv = Response(chunk_data, 206, mimetype=mimetype, content_type=mimetype, direct_passthrough=True)
    rv.headers.add('Content-Range', f'bytes {start}-{end}/{size}')
    rv.headers.add('Accept-Ranges', 'bytes')
    rv.headers.add('Content-Length', str(len(chunk_data)))
    return rv

@app.route('/download/<int:music_id>')
def download(music_id):
    music = Music.query.get_or_404(music_id)
    mimetype = 'video/mp4' if music.filename.lower().endswith('.mp4') else 'audio/mpeg'
    return send_file(
        io.BytesIO(music.data),
        mimetype=mimetype,
        as_attachment=True,
        download_name=music.filename
    )

@app.route('/delete/<int:music_id>', methods=['POST'])
def delete(music_id):
    password = request.form.get('password')
    if password != 'choco-banana-':
        flash('パスワードが間違っています')
        return redirect(url_for('index'))
        
    music = Music.query.get_or_404(music_id)
    db.session.delete(music)
    db.session.commit()
    flash('削除しました')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
