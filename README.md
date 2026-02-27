# Busy Status System

Система управления статусом сотрудника для отображения на планшете/мониторе.

## 🚀 Быстрый старт

```bash
python app.py
```

После запуска:
- Откройте `http://localhost:5000` — страница статуса (для планшета)
- Откройте `http://localhost:5000/login` — вход в админ-панель

**Учётные данные по умолчанию:**
- Логин: `admin`
- Пароль: `admin123`

⚠️ **Смените пароль после первого входа!**

---

## 🔐 Аутентификация

Админ-панель защищена паролем. При первом запуске автоматически создаётся пользователь `admin`.

Пользователи хранятся в `data/users.json` с хешированными паролями (SHA-256 + salt).

---

## 🔑 API Документация

### Аутентификация API

Все API эндпоинты требуют API ключ. Получите его в админ-панели или из файла `data/api_key.json`.

**Способы передачи ключа:**
1. Заголовок: `X-API-Key: ваш_ключ`
2. Query параметр: `?api_key=ваш_ключ`

---

### Эндпоинты

#### 📋 Получить все пресеты
```http
GET /api/presets
X-API-Key: ваш_ключ
```

**Ответ:**
```json
{
  "success": true,
  "presets": [
    {
      "id": 1,
      "name": "На встрече",
      "status": "meeting",
      "status_text": "На встрече",
      "current_activity": "Обсуждаю проект с командой",
      "custom_message": "Вернусь через 30 минут",
      "color_scheme": "yellow"
    }
  ]
}
```

---

#### ➕ Создать пресет
```http
POST /api/presets
X-API-Key: ваш_ключ
Content-Type: application/json

{
  "name": "Новый пресет",
  "status": "busy",
  "status_text": "Не беспокоить",
  "current_activity": "Сосредоточенная работа",
  "custom_message": "Пожалуйста, не отвлекайте",
  "color_scheme": "red"
}
```

---

#### 🗑️ Удалить пресет
```http
DELETE /api/presets/<id>
X-API-Key: ваш_ключ
```

---

#### ✅ Применить пресет
```http
POST /api/presets/<id>/apply
X-API-Key: ваш_ключ
```

**Ответ:**
```json
{
  "success": true,
  "data": {
    "user_name": "...",
    "status": "busy",
    "status_text": "Не беспокоить",
    ...
  }
}
```

---

#### 🔄 Быстрая смена статуса
```http
POST /api/status
X-API-Key: ваш_ключ
Content-Type: application/json

{
  "status": "meeting",
  "status_text": "На встрече",
  "current_activity": "Обсуждение",
  "custom_message": "Вернусь через 30 минут",
  "color_scheme": "yellow"
}
```

Можно передавать только изменяемые поля.

---

#### 📖 Получить текущий статус (без ключа)
```http
GET /api/status
```

---

### Примеры использования

#### cURL
```bash
# Применить пресет
curl -X POST http://localhost:5000/api/presets/1/apply \
  -H "X-API-Key: ваш_ключ"

# Сменить статус
curl -X POST http://localhost:5000/api/status \
  -H "X-API-Key: ваш_ключ" \
  -H "Content-Type: application/json" \
  -d '{"status": "busy", "status_text": "Занят"}'

# Получить все пресеты
curl http://localhost:5000/api/presets \
  -H "X-API-Key: ваш_ключ"
```

#### Python
```python
import requests

API_KEY = "ваш_ключ"
BASE_URL = "http://localhost:5000"

headers = {"X-API-Key": API_KEY}

# Применить пресет
response = requests.post(
    f"{BASE_URL}/api/presets/1/apply",
    headers=headers
)

# Сменить статус
response = requests.post(
    f"{BASE_URL}/api/status",
    headers=headers,
    json={"status": "meeting", "status_text": "На встрече"}
)
```

#### JavaScript (fetch)
```javascript
const API_KEY = "ваш_ключ";
const BASE_URL = "http://localhost:5000";

// Применить пресет
fetch(`${BASE_URL}/api/presets/1/apply`, {
  method: 'POST',
  headers: {
    'X-API-Key': API_KEY
  }
});

// Сменить статус
fetch(`${BASE_URL}/api/status`, {
  method: 'POST',
  headers: {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    status: 'busy',
    status_text: 'Занят'
  })
});
```

---

## 📁 Структура данных

### Файлы
- `data/current_status.json` — текущий статус
- `data/media_history.json` — история медиа файлов
- `data/templates/templates.json` — шаблоны/пресеты
- `data/users.json` — пользователи
- `data/api_key.json` — API ключ

### Статусы
- `available` — доступен 🟢
- `busy` — занят 🔴
- `meeting` — на встрече 🟡
- `away` — отошёл ⚪

### Цветовые схемы
- `blue`, `red`, `green`, `yellow`, `purple`, `gray`

---

## 🔒 Безопасность

1. **Смените SECRET_KEY** в `app.py` для продакшена
2. **Смените пароль admin** после первого входа
3. **Не передавайте API ключ** в публичных репозиториях
4. **Используйте HTTPS** в продакшене

---

## 🎯 Сценарии использования

### Автоматизация через Home Assistant
```yaml
rest_command:
  set_busy_status:
    url: http://localhost:5000/api/status
    method: POST
    headers:
      X-API-Key: !secret busy_api_key
    content_type: application/json
    payload: '{"status": "busy", "status_text": "Не беспокоить"}'
```

### Расписание через cron
```bash
# Установить "На встрече" в 10:00
0 10 * * * curl -X POST http://localhost:5000/api/presets/1/apply -H "X-API-Key: ключ"

# Установить "Обед" в 13:00
0 13 * * * curl -X POST http://localhost:5000/api/presets/3/apply -H "X-API-Key: ключ"
```

---

## 🛠️ Расширение

### Добавить нового пользователя
```python
# В Python консоли с импортом из app.py
create_user('newuser', 'password123')
```

### Интеграция с календарём
Используйте API для автоматической смены статуса на основе событий календаря.

---

## 📝 Changelog

### Версия 2.0
- ✅ Добавлена аутентификация для админ-панели
- ✅ API ключ для автоматизации
- ✅ Эндпоинты для управления пресетами
- ✅ Быстрая смена статуса через API

---

## 📄 Лицензия

MIT
