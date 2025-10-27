from flask import Blueprint, request, flash, redirect, url_for, render_template, current_app
from flask_login import login_required
from werkzeug.utils import secure_filename
import os
# Функциональность распознавания по фото отключена — ранее импортировалась функция analyze_image_with_gemini

probe_bp = Blueprint('probe', __name__)

def allowed_file(filename):
    """Проверяет, является ли расширение файла допустимым"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}

@probe_bp.route('/scan', methods=['GET', 'POST'])
@login_required
def scan():
    if request.method == 'POST':
        try:
            if 'photo' not in request.files:
                flash('Фото не предоставлено')
                return redirect(url_for('probe.scan'))
                
            photo = request.files['photo']
            if photo.filename == '':
                flash('Фото не выбрано')
                return redirect(url_for('probe.scan'))
                
            if not photo or not allowed_file(photo.filename):
                flash('Недопустимый тип файла')
                return redirect(url_for('probe.scan'))
                
            if photo.filename is None:
                flash('Некорректное имя файла')
                return redirect(url_for('probe.scan'))
                
            filename = secure_filename(photo.filename)
            photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            photo.save(photo_path)
            
            # Функция распознавания по фото отключена — просто удаляем загруженный файл
            try:
                flash('Функция распознавания по фото отключена', 'info')
            finally:
                try:
                    os.remove(photo_path)
                except OSError:
                    pass
                    
            return redirect(url_for('probe.scan'))
            
        except Exception as e:
            flash(f'Ошибка при обработке запроса: {str(e)}')
            return redirect(url_for('probe.scan'))
            
    return render_template('scan.html')
