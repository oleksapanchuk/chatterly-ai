# 🚀 Інструкція з встановлення та використання Chatterly AI

## 📋 Передумови

### Системні вимоги
- Python 3.8+ 
- pip або conda
- Git

### API ключі (обов'язково)
- **OpenAI API Key** - для Layer 2 аналізу (GPT-4o та Omni)
- **Deepgram API Key** - для транскрипції аудіо (опціонально)

## 🔧 Встановлення

### 1. Клонування репозиторію
```bash
cd /home/panchuk/Documents/chatterly/chatterly-ai
```

### 2. Встановлення залежностей
```bash
pip install -r requirements.txt
```

### 3. Конфігурація

Створіть файл `.env` на основі `config.env.example`:
```bash
cp config.env.example .env
```

Відредагуйте `.env` файл:
```env
# ОБОВ'ЯЗКОВО: OpenAI API Key
OPENAI_API_KEY=sk-your-real-openai-key-here

# ОПЦІОНАЛЬНО: Deepgram для аудіо
DEEPGRAM_API_KEY=your-deepgram-key-here

# Налаштування за замовчуванням
DEFAULT_MODEL=gpt-4o
HOST=localhost
PORT=8000
```

### 4. Перевірка встановлення
```bash
python -c "from services.enhanced_moderation_service import EnhancedModerationService; print('✅ Встановлення успішне!')"
```

## 🏃‍♂️ Запуск

### Запуск сервера
```bash
python app.py
```

Або з uvicorn:
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### Перевірка роботи
Відкрийте браузер: http://localhost:8000/docs

## 📡 API Endpoints

### 🔍 Перевірка системи

**GET /v2/health** - статус здоров'я системи
```bash
curl http://localhost:8000/v2/health
```

**GET /v2/capabilities** - можливості системи
```bash
curl http://localhost:8000/v2/capabilities
```

### 📝 Модерація тексту

**POST /v2/moderate-text**
```bash
curl -X POST "http://localhost:8000/v2/moderate-text" \
  -F "text=Це тестовий текст" \
  -F "harm_threshold=70.0" \
  -F "salt=your_salt"
```

### 🖼️ Модерація зображень

**POST /v2/moderate-image**
```bash
curl -X POST "http://localhost:8000/v2/moderate-image" \
  -F "image=@/path/to/image.jpg" \
  -F "harm_threshold=70.0" \
  -F "salt=your_salt"
```

### 🎵 Модерація аудіо

**POST /v2/moderate-audio**
```bash
curl -X POST "http://localhost:8000/v2/moderate-audio" \
  -F "audio=@/path/to/audio.wav" \
  -F "harm_threshold=70.0" \
  -F "salt=your_salt"
```

### 🎯 Універсальна модерація

**POST /v2/moderate** - мультимодальна модерація
```bash
curl -X POST "http://localhost:8000/v2/moderate" \
  -F "text=Текст для аналізу" \
  -F "image=@image.jpg" \
  -F "audio=@audio.wav" \
  -F "harm_threshold=60.0" \
  -F "enable_layer1=true" \
  -F "enable_layer2=true" \
  -F "salt=your_salt"
```

## 📊 Формат Response

### Приклад успішної відповіді:
```json
{
  "request_id": null,
  "overall_result": {
    "overall_harm_score": 85.2,
    "is_harmful": true,
    "harm_categories": ["hate_speech", "violence"],
    "confidence": 0.923,
    "layer_scores": {
      "text": "L1: 45.0, L2: 82.3, Combined: 70.1"
    },
    "calculation_details": "=== HARM SCORE CALCULATION ===\nFinal Score: 85.20/100..."
  },
  "layer1_results": {
    "text": {
      "content_type": "text",
      "fast_filter_result": {
        "is_harmful": true,
        "confidence": 0.8,
        "categories": ["hate_speech"],
        "details": "Banned words found: hate, nazi"
      },
      "banned_words_found": ["hate", "nazi"]
    }
  },
  "layer2_results": {
    "text": {
      "content_type": "text",
      "ai_analysis_result": {
        "is_harmful": true,
        "confidence": 0.95,
        "categories": ["hate_speech", "violence"]
      },
      "model_used": "gpt-4o-enhanced"
    }
  },
  "processing_time_ms": 1247.3,
  "errors": [],
  "warnings": [],
  "timestamp": 1703123456.789
}
```

## 🎛️ Параметри конфігурації

### Основні параметри:
- **harm_threshold** (0-100): поріг шкідливості (за замовчуванням 70.0)
- **confidence_threshold** (0-1): поріг впевненості (за замовчуванням 0.6)
- **enable_layer1**: увімкнути швидкі фільтри
- **enable_layer2**: увімкнути AI аналіз

### Ваги контенту (автоматично нормалізуються):
- **text_weight**: 0.4 (40%)
- **image_weight**: 0.35 (35%) 
- **audio_weight**: 0.25 (25%)

### Ваги шарів:
- **layer1_weight**: 0.3 (30% - швидкі фільтри)
- **layer2_weight**: 0.7 (70% - AI аналіз)

## 🧪 Тестування

### Запуск прикладів:
```bash
cd examples
python usage_examples.py
```

### Тести юніт:
```bash
pytest tests/ -v
```

## 🏗️ Архітектура системи

### Layer 1: Швидкі фільтри
- ✅ Заборонені слова (better-profanity)
- ✅ Хеші зображень (imagehash)  
- ✅ Транскрипція аудіо (Deepgram)

### Layer 2: AI аналіз
- ✅ GPT-4o для тексту/аудіо
- ✅ Omni для зображень
- ✅ Покращені промпти
- ✅ Контекстний аналіз

### Layer 3: Математична модель
- ✅ Зважене оцінювання
- ✅ Категоріальна ампліфікація
- ✅ Детальні пояснення
- ✅ Налаштовувані ваги

## 🔐 Безпека

### API Salt
Всі endpoints вимагають параметр `salt` для автентифікації.

### Обмеження розмірів:
- Текст: до 100,000 символів
- Зображення: до 20MB
- Аудіо: до 50MB

## 🐛 Виправлення помилок

### Поширені проблеми:

**1. OpenAI API Key не працює**
```bash
export OPENAI_API_KEY="your-real-key"
python -c "from openai import OpenAI; client = OpenAI(); print('✅ Key works')"
```

**2. Deepgram не доступний**
- Система працюватиме без аудіо транскрипції
- Або встановіть Deepgram ключ

**3. Помилки імпорту**
```bash
pip install -r requirements.txt --upgrade
```

**4. Проблеми з портом**
```bash
# Змініть порт у .env
PORT=8001
```

## 📈 Моніторинг

### Статистика системи:
```bash
curl http://localhost:8000/v2/health
```

### Логи:
```bash
tail -f app.log  # якщо налаштовано логування
```

## 🔄 Оновлення

### Оновлення залежностей:
```bash
pip install -r requirements.txt --upgrade
```

### Перезапуск сервісу:
```bash
pkill -f "python app.py"
python app.py
```

## 💡 Поради з оптимізації

1. **Продуктивність**: Налаштуйте пул з'єднань для OpenAI
2. **Масштабування**: Використовуйте Redis для кешування результатів
3. **Моніторинг**: Додайте Prometheus метрики
4. **Безпека**: Використовуйте HTTPS в продакшені

## 📞 Підтримка

- 📧 Питання: створіть issue в репозиторії
- 📖 Документація: `/docs` endpoint
- 🔧 API схема: `/openapi.json` 