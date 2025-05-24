#!/usr/bin/env python3
"""
Тест для перевірки правильності встановлення Chatterly AI
"""

import sys
import os

def test_imports():
    """Тестування імпортів"""
    print("🔍 Перевірка імпортів...")
    
    try:
        from better_profanity import profanity
        print("✅ better-profanity")
    except ImportError as e:
        print(f"❌ better-profanity: {e}")
        return False
    
    try:
        from services.enhanced_moderation_service import EnhancedModerationService
        print("✅ EnhancedModerationService")
    except ImportError as e:
        print(f"❌ EnhancedModerationService: {e}")
        return False
    
    try:
        import app
        print("✅ FastAPI app")
    except ImportError as e:
        print(f"❌ FastAPI app: {e}")
        return False
    
    return True

def test_config():
    """Тестування конфігурації"""
    print("\n🔧 Перевірка конфігурації...")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and openai_key != "your_openai_api_key_here":
        print("✅ OpenAI API key налаштований")
        return True
    else:
        print("⚠️  OpenAI API key НЕ налаштований (потрібен для роботи)")
        print("   Відредагуйте .env файл та додайте ваш справжній ключ")
        return False

def test_service_initialization():
    """Тестування ініціалізації сервісу"""
    print("\n🚀 Перевірка ініціалізації сервісу...")
    
    try:
        from services.enhanced_moderation_service import EnhancedModerationService
        
        # Тест з фейковим ключем
        service = EnhancedModerationService(openai_api_key="test_key")
        print("✅ Сервіс ініціалізується без помилок")
        
        # Перевірка методів
        health = service.get_system_health()
        print(f"✅ Система здорова: {health.get('system_status', 'unknown')}")
        
        capabilities = service.get_processing_capabilities()
        print(f"✅ Можливості завантажені: {len(capabilities)} категорій")
        
        return True
        
    except Exception as e:
        print(f"❌ Помилка ініціалізації: {e}")
        return False

def main():
    """Головна функція тестування"""
    print("🎯 Тестування встановлення Chatterly AI")
    print("=" * 50)
    
    success = True
    
    # Тест імпортів
    if not test_imports():
        success = False
    
    # Тест конфігурації
    config_ok = test_config()
    if not config_ok:
        success = False
    
    # Тест ініціалізації
    if not test_service_initialization():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ВСІ ТЕСТИ ПРОЙШЛИ УСПІШНО!")
        if not config_ok:
            print("\n📝 Наступні кроки:")
            print("1. Відредагуйте .env файл")
            print("2. Додайте ваш справжній OpenAI API ключ")
            print("3. Запустіть сервер: python app.py")
        else:
            print("\n🚀 Система готова до роботи!")
            print("Запустіть сервер: python app.py")
    else:
        print("❌ Знайдено проблеми. Перевірте помилки вище.")
        sys.exit(1)

if __name__ == "__main__":
    main() 