#!/usr/bin/env python3
"""
Приклади використання системи модерації контенту Chatterly AI
"""

import asyncio
import requests
import aiohttp
import json
from typing import Optional

# Конфігурація API
API_BASE_URL = "http://localhost:8000"
API_SALT = "your_api_salt_here"  # Замініть на ваш реальний salt

async def example_text_moderation():
    """Приклад модерації тексту"""
    print("=== ПРИКЛАД МОДЕРАЦІЇ ТЕКСТУ ===")
    
    # Тестові тексти
    test_texts = [
        "Привіт! Як справи?",  # Нормальний текст
        "Ти дурак і я тебе ненавиджу!",  # Образливий текст
        "Давайте вбимо всіх ворогів нашої нації",  # Насильство + ненависть
    ]
    
    async with aiohttp.ClientSession() as session:
        for i, text in enumerate(test_texts, 1):
            print(f"\nТест {i}: {text}")
            
            # Запит до API
            data = {
                "text": text,
                "harm_threshold": 70.0,
                "confidence_threshold": 0.6,
                "salt": API_SALT
            }
            
            async with session.post(f"{API_BASE_URL}/v2/moderate-text", data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    print(f"Результат: {'ШКІДЛИВИЙ' if result['overall_result']['is_harmful'] else 'БЕЗПЕЧНИЙ'}")
                    print(f"Оцінка шкоди: {result['overall_result']['overall_harm_score']}/100")
                    print(f"Впевненість: {result['overall_result']['confidence']:.3f}")
                    print(f"Категорії: {result['overall_result']['harm_categories']}")
                    print(f"Час обробки: {result['processing_time_ms']:.1f}ms")
                else:
                    print(f"Помилка: {response.status}")

async def example_image_moderation():
    """Приклад модерації зображення"""
    print("\n=== ПРИКЛАД МОДЕРАЦІЇ ЗОБРАЖЕННЯ ===")
    
    # Завантажте тестове зображення
    image_path = "test_image.jpg"  # Замініть на шлях до вашого зображення
    
    try:
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field('harm_threshold', '70.0')
            data.add_field('sensitivity_level', 'standard')
            data.add_field('salt', API_SALT)
            
            with open(image_path, 'rb') as f:
                data.add_field('image', f, filename='test.jpg', content_type='image/jpeg')
                
                async with session.post(f"{API_BASE_URL}/v2/moderate-image", data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        print(f"Результат: {'ШКІДЛИВИЙ' if result['overall_result']['is_harmful'] else 'БЕЗПЕЧНИЙ'}")
                        print(f"Оцінка шкоди: {result['overall_result']['overall_harm_score']}/100")
                        print(f"Впевненість: {result['overall_result']['confidence']:.3f}")
                        print(f"Категорії: {result['overall_result']['harm_categories']}")
                        print(f"Час обробки: {result['processing_time_ms']:.1f}ms")
                    else:
                        print(f"Помилка: {response.status}")
                        
    except FileNotFoundError:
        print(f"Файл {image_path} не знайдено. Створіть тестове зображення або змініть шлях.")

async def example_multimodal_moderation():
    """Приклад модерації змішаного контенту"""
    print("\n=== ПРИКЛАД МУЛЬТИМОДАЛЬНОЇ МОДЕРАЦІЇ ===")
    
    text = "Подивіться на це зображення та аудіо"
    
    try:
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field('text', text)
            data.add_field('harm_threshold', '60.0')
            data.add_field('confidence_threshold', '0.5')
            data.add_field('enable_layer1', 'true')
            data.add_field('enable_layer2', 'true')
            data.add_field('salt', API_SALT)
            
            # Додайте файли якщо вони є
            # with open('test_image.jpg', 'rb') as f:
            #     data.add_field('image', f, filename='test.jpg')
            # with open('test_audio.wav', 'rb') as f:
            #     data.add_field('audio', f, filename='test.wav')
            
            async with session.post(f"{API_BASE_URL}/v2/moderate", data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    print(f"Загальний результат: {'ШКІДЛИВИЙ' if result['overall_result']['is_harmful'] else 'БЕЗПЕЧНИЙ'}")
                    print(f"Загальна оцінка: {result['overall_result']['overall_harm_score']}/100")
                    
                    # Результати по шарах
                    print("\nРезультати Layer 1:")
                    for content_type, layer1_result in result['layer1_results'].items():
                        print(f"  {content_type}: {layer1_result['fast_filter_result']['is_harmful']}")
                    
                    print("\nРезультати Layer 2:")
                    for content_type, layer2_result in result['layer2_results'].items():
                        print(f"  {content_type}: {layer2_result['ai_analysis_result']['is_harmful']}")
                    
                    print(f"\nДеталі розрахунку:\n{result['overall_result']['calculation_details']}")
                else:
                    print(f"Помилка: {response.status}")
                    
    except Exception as e:
        print(f"Помилка: {e}")

def sync_example_with_requests():
    """Синхронний приклад з requests"""
    print("\n=== СИНХРОННИЙ ПРИКЛАД ===")
    
    # Модерація тексту
    data = {
        "text": "Це тестовий текст для модерації",
        "salt": API_SALT
    }
    
    response = requests.post(f"{API_BASE_URL}/v2/moderate-text", data=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"Результат: {result['overall_result']['is_harmful']}")
        print(f"Оцінка: {result['overall_result']['overall_harm_score']}/100")
    else:
        print(f"Помилка: {response.status_code}")

async def check_system_health():
    """Перевірка здоров'я системи"""
    print("\n=== ПЕРЕВІРКА СИСТЕМИ ===")
    
    async with aiohttp.ClientSession() as session:
        # Перевірка здоров'я
        async with session.get(f"{API_BASE_URL}/v2/health") as response:
            if response.status == 200:
                health = await response.json()
                print(f"Статус системи: {health['system_status']}")
                print(f"Успішність: {health['success_rate']:.1f}%")
                print(f"Всього запитів: {health['total_requests']}")
            else:
                print(f"Помилка отримання статусу: {response.status}")
        
        # Можливості системи
        async with session.get(f"{API_BASE_URL}/v2/capabilities") as response:
            if response.status == 200:
                capabilities = await response.json()
                print(f"\nПідтримувані формати зображень: {capabilities['image_processing']['supported_formats']}")
                print(f"Максимальний розмір тексту: {capabilities['text_processing']['max_length']} символів")
                print(f"Транскрипція аудіо: {capabilities['audio_processing']['transcription']}")
            else:
                print(f"Помилка отримання можливостей: {response.status}")

async def main():
    """Головна функція з усіма прикладами"""
    print("🚀 Приклади використання Chatterly AI Content Moderation")
    print("=" * 60)
    
    await check_system_health()
    await example_text_moderation()
    
    # Розкоментуйте для тестування зображень та аудіо
    # await example_image_moderation()
    # await example_multimodal_moderation()
    
    sync_example_with_requests()
    
    print("\n✅ Всі приклади завершено!")

if __name__ == "__main__":
    # Запуск прикладів
    asyncio.run(main()) 