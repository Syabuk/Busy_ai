from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for
from functools import wraps
import json
import os
import uuid
import hashlib
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['TEMPLATES_FOLDER'] = 'data/templates'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Создаем необходимые папки
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['TEMPLATES_FOLDER'], exist_ok=True)

# Файлы для хранения данных
DATA_FILE = 'data/current_status.json'
HISTORY_FILE = 'data/media_history.json'
USERS_FILE = 'data/users.json'
API_KEY_FILE = 'data/api_key.json'

# Генерация API ключа при старте


def get_or_create_api_key():
    if os.path.exists(API_KEY_FILE):
        with open(API_KEY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)['api_key']
    api_key = str(uuid.uuid4())
    with open(API_KEY_FILE, 'w', encoding='utf-8') as f:
        json.dump({'api_key': api_key}, f, ensure_ascii=False, indent=2)
    return api_key


API_KEY = get_or_create_api_key()

# Начальные данные
DEFAULT_DATA = {
    "user_name": "Алексей Петров",
    "status": "available",
    "status_text": "Доступен",
    "current_activity": "Готов к работе",
    "custom_message": "",
    "media_file": "",
    "media_type": "none",
    "color_scheme": "blue",
    "last_updated": datetime.now().strftime("%d.%m.%Y %H:%M:%S")
}

DEFAULT_TEMPLATES = [
    {
        "id": 1,
        "name": "На встрече",
        "status": "meeting",
        "status_text": "На встрече",
        "current_activity": "Обсуждаю проект с командой",
        "custom_message": "Вернусь через 30 минут",
        "color_scheme": "yellow"
    },
    {
        "id": 2,
        "name": "Не беспокоить",
        "status": "busy",
        "status_text": "Не беспокоить",
        "current_activity": "Сосредоточенная работа",
        "custom_message": "Пожалуйста, не отвлекайте",
        "color_scheme": "red"
    },
    {
        "id": 3,
        "name": "Обеденный перерыв",
        "status": "away",
        "status_text": "Отошёл",
        "current_activity": "Обеденный перерыв",
        "custom_message": "Вернусь в 14:00",
        "color_scheme": "gray"
    }
]


def init_data_folder():
    """Инициализация папки данных"""
    os.makedirs('data', exist_ok=True)


def load_data():
    """Загрузка текущего статуса"""
    init_data_folder()
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return DEFAULT_DATA
    return DEFAULT_DATA


def save_data(data):
    """Сохранение текущего статуса"""
    data['last_updated'] = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_media_history():
    """Загрузка истории медиа"""
    init_data_folder()
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"media": []}
    return {"media": []}


def save_media_history(history):
    """Сохранение истории медиа"""
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def load_templates():
    """Загрузка шаблонов"""
    template_file = os.path.join(
        app.config['TEMPLATES_FOLDER'], 'templates.json')
    if os.path.exists(template_file):
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return DEFAULT_TEMPLATES
    return DEFAULT_TEMPLATES


def save_templates(templates):
    """Сохранение шаблонов"""
    template_file = os.path.join(
        app.config['TEMPLATES_FOLDER'], 'templates.json')
    with open(template_file, 'w', encoding='utf-8') as f:
        json.dump(templates, f, ensure_ascii=False, indent=2)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {
               'png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm'}


def load_users():
    """Загрузка пользователей"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"users": []}
    return {"users": []}


def save_users(users_data):
    """Сохранение пользователей"""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users_data, f, ensure_ascii=False, indent=2)


def create_user(username, password):
    """Создание пользователя"""
    users_data = load_users()
    if any(u['username'] == username for u in users_data['users']):
        return False

    salt = str(uuid.uuid4())
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()

    users_data['users'].append({
        'username': username,
        'password_hash': password_hash,
        'salt': salt,
        'created_at': datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    })
    save_users(users_data)
    return True


def verify_user(username, password):
    """Проверка пользователя"""
    users_data = load_users()
    user = next((u for u in users_data['users']
                if u['username'] == username), None)
    if not user:
        return False

    password_hash = hashlib.sha256(
        (password + user['salt']).encode()).hexdigest()
    return user['password_hash'] == password_hash


def login_required(f):
    """Декоратор для защиты маршрутов"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    """Главная страница для планшета"""
    data = load_data()
    return render_template('index.html', **data)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if verify_user(username, password):
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('admin'))
        return render_template('login.html', error='Неверное имя пользователя или пароль')

    return render_template('login.html', error=None)


@app.route('/logout')
def logout():
    """Выход из системы"""
    session.clear()
    return redirect(url_for('login'))


@app.route('/admin')
@login_required
def admin():
    """Страница администрирования"""
    data = load_data()
    media_history = load_media_history()
    templates = load_templates()
    return render_template('admin.html',
                           current_data=data,
                           media_history=media_history['media'],
                           templates=templates,
                           api_key=API_KEY)


@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    """Отдача загруженных файлов"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/api/status')
def get_status():
    """API для получения текущего статуса"""
    data = load_data()
    return jsonify(data)


@app.route('/api/update_status', methods=['POST'])
def update_status():
    """API для обновления статуса"""
    data = load_data()

    # Обновляем текстовые данные
    if request.form.get('user_name'):
        data['user_name'] = request.form.get('user_name')
    if request.form.get('status'):
        data['status'] = request.form.get('status')
    if request.form.get('status_text'):
        data['status_text'] = request.form.get('status_text')
    if request.form.get('current_activity'):
        data['current_activity'] = request.form.get('current_activity')
    if request.form.get('custom_message'):
        data['custom_message'] = request.form.get('custom_message')
    if request.form.get('color_scheme'):
        data['color_scheme'] = request.form.get('color_scheme')

    # Обрабатываем загрузку файла
    if 'media_file' in request.files:
        file = request.files['media_file']
        if file and file.filename != '' and allowed_file(file.filename):
            # Сохраняем новый файл
            filename = str(uuid.uuid4()) + '_' + secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            data['media_file'] = filename

            # Определяем тип медиа
            ext = filename.rsplit('.', 1)[1].lower()
            if ext in ['gif']:
                data['media_type'] = 'gif'
            elif ext in ['mp4', 'webm']:
                data['media_type'] = 'video'
            else:
                data['media_type'] = 'image'

            # Добавляем в историю
            history = load_media_history()
            history['media'].append({
                'filename': filename,
                'original_name': file.filename,
                'upload_time': datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
                'file_type': data['media_type']
            })
            save_media_history(history)

    save_data(data)
    return jsonify({'success': True, 'data': data})


@app.route('/api/use_media', methods=['POST'])
def use_media():
    """API для использования медиа из истории"""
    data = load_data()
    media_file = request.json.get('media_file')

    # Проверяем существование файла
    if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], media_file)):
        data['media_file'] = media_file

        # Определяем тип файла
        ext = media_file.rsplit('.', 1)[1].lower()
        if ext in ['gif']:
            data['media_type'] = 'gif'
        elif ext in ['mp4', 'webm']:
            data['media_type'] = 'video'
        else:
            data['media_type'] = 'image'

        save_data(data)
        return jsonify({'success': True})

    return jsonify({'success': False, 'error': 'File not found'})


@app.route('/api/clear_media', methods=['POST'])
def clear_media():
    """API для очистки медиа"""
    data = load_data()
    data['media_file'] = ""
    data['media_type'] = "none"
    save_data(data)
    return jsonify({'success': True})


@app.route('/api/save_template', methods=['POST'])
def save_template():
    """API для сохранения шаблона"""
    template_data = request.json
    templates = load_templates()

    # Генерируем ID для нового шаблона
    new_id = max([t['id'] for t in templates], default=0) + 1
    template_data['id'] = new_id

    templates.append(template_data)
    save_templates(templates)

    return jsonify({'success': True})


@app.route('/api/apply_template', methods=['POST'])
def apply_template():
    """API для применения шаблона"""
    template_id = request.json.get('template_id')
    templates = load_templates()

    template = next((t for t in templates if t['id'] == template_id), None)
    if template:
        data = load_data()
        # Обновляем только определенные поля
        data['status'] = template['status']
        data['status_text'] = template['status_text']
        data['current_activity'] = template['current_activity']
        data['custom_message'] = template.get('custom_message', '')
        data['color_scheme'] = template.get('color_scheme', 'blue')
        data['media_file'] = template.get('media_file', '')
        data['media_type'] = template.get('media_type', 'none')

        save_data(data)
        return jsonify({'success': True, 'data': data})

    return jsonify({'success': False, 'error': 'Template not found'})


@app.route('/api/delete_template', methods=['POST'])
def delete_template():
    """API для удаления шаблона"""
    template_id = request.json.get('template_id')
    templates = load_templates()

    templates = [t for t in templates if t['id'] != template_id]
    save_templates(templates)

    return jsonify({'success': True})


def check_api_key():
    """Проверка API ключа"""
    api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
    if not api_key or api_key != API_KEY:
        return False
    return True


@app.route('/api/presets', methods=['GET'])
def get_presets():
    """API для получения всех пресетов (требуется API ключ)"""
    if not check_api_key():
        return jsonify({'success': False, 'error': 'Invalid or missing API key'}), 401

    templates = load_templates()
    return jsonify({'success': True, 'presets': templates})


@app.route('/api/presets', methods=['POST'])
def create_preset():
    """API для создания пресета (требуется API ключ)"""
    if not check_api_key():
        return jsonify({'success': False, 'error': 'Invalid or missing API key'}), 401

    preset_data = request.json
    if not preset_data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    # Если медиа не указано в пресете, берём текущее из статуса
    if 'media_file' not in preset_data or not preset_data.get('media_file'):
        current_data = load_data()
        preset_data['media_file'] = current_data.get('media_file', '')
        preset_data['media_type'] = current_data.get('media_type', 'none')

    templates = load_templates()
    new_id = max([t['id'] for t in templates], default=0) + 1
    preset_data['id'] = new_id

    templates.append(preset_data)
    save_templates(templates)

    return jsonify({'success': True, 'preset': preset_data})


@app.route('/api/presets/<int:preset_id>', methods=['DELETE'])
def delete_preset(preset_id):
    """API для удаления пресета (требуется API ключ)"""
    if not check_api_key():
        return jsonify({'success': False, 'error': 'Invalid or missing API key'}), 401

    templates = load_templates()
    templates = [t for t in templates if t['id'] != preset_id]
    save_templates(templates)

    return jsonify({'success': True})


@app.route('/api/presets/<int:preset_id>/apply', methods=['POST'])
def apply_preset(preset_id):
    """API для применения пресета (требуется API ключ)"""
    if not check_api_key():
        return jsonify({'success': False, 'error': 'Invalid or missing API key'}), 401

    templates = load_templates()
    template = next((t for t in templates if t['id'] == preset_id), None)

    if not template:
        return jsonify({'success': False, 'error': 'Preset not found'}), 404

    data = load_data()
    data['status'] = template['status']
    data['status_text'] = template['status_text']
    data['current_activity'] = template['current_activity']
    data['custom_message'] = template.get('custom_message', '')
    data['color_scheme'] = template.get('color_scheme', 'blue')
    data['media_file'] = template.get('media_file', '')
    data['media_type'] = template.get('media_type', 'none')
    data['last_updated'] = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

    save_data(data)

    return jsonify({'success': True, 'data': data})


@app.route('/api/status', methods=['POST'])
def set_status():
    """API для быстрой смены статуса (требуется API ключ)"""
    if not check_api_key():
        return jsonify({'success': False, 'error': 'Invalid or missing API key'}), 401

    data = load_data()
    json_data = request.json

    if json_data.get('status'):
        data['status'] = json_data['status']
    if json_data.get('status_text'):
        data['status_text'] = json_data['status_text']
    if json_data.get('current_activity'):
        data['current_activity'] = json_data['current_activity']
    if json_data.get('custom_message'):
        data['custom_message'] = json_data['custom_message']
    if json_data.get('color_scheme'):
        data['color_scheme'] = json_data['color_scheme']

    save_data(data)

    return jsonify({'success': True, 'data': data})


if __name__ == '__main__':
    # Создаем пользователя по умолчанию если нет пользователей
    if not os.path.exists(USERS_FILE) or os.path.getsize(USERS_FILE) == 0:
        print("=" * 50)
        print("WARNING: Creating default user")
        print("   Login: admin")
        print("   Password: admin123")
        print("   Please change password after first login!")
        print("=" * 50)
        create_user('admin', 'admin123')

    print(f"\nAPI Key: {API_KEY}")
    print("For API requests use header: X-API-Key: " + API_KEY)
    print("\nStarting server...\n")

    app.run(host='0.0.0.0', port=5000, debug=True)
