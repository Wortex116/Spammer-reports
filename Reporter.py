import asyncio
import sys
import random
import json
import os
import time
from datetime import datetime

try:
    from telethon import TelegramClient, errors
    from telethon.tl.functions.messages import ReportSpamRequest
    from telethon.tl.functions.users import GetFullUserRequest
    from telethon.tl.functions.channels import GetChannelsRequest
    from telethon.tl.types import InputPeerUser, InputPeerChat, InputPeerChannel
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("📌 Установите: pip install telethon")
    sys.exit()

# ===== ВАШИ ДАННЫЕ =====
API_ID = 21385447
API_HASH = "298a74a2e136e9f350b4c40b397d39172"

# ===== ВАШИ НОМЕРА (ПО ОЧЕРЕДИ) =====
PHONES = [
    "+13673234619",
    "+963964576162",
    "+967781800173",
    "+919699834880"
]

# ===== ПРИЧИНЫ ДЛЯ ЖАЛОБ =====
REPORT_REASONS = {
    "1": {"name": "Спам", "reason": "spam"},
    "2": {"name": "Насилие", "reason": "violence"},
    "3": {"name": "Детская порнография", "reason": "child_abuse"},
    "4": {"name": "Порнография", "reason": "pornography"},
    "5": {"name": "Другое", "reason": "other"},
    "6": {"name": "Мошенничество", "reason": "fraud"},
    "7": {"name": "Оскорбления", "reason": "insult"},
    "8": {"name": "Фейк-аккаунт", "reason": "fake"},
    "9": {"name": "Терроризм", "reason": "terrorism"},
    "10": {"name": "Наркотики", "reason": "drugs"},
}

# ===== КОНФИГ =====
DELAY_BETWEEN_REPORTS = (3, 8)
MAX_REPORTS_PER_ACCOUNT = 30

# ===== ВЫБОР ТИПА ЦЕЛИ =====
TARGET_TYPES = {
    "1": {"name": "Пользователь", "type": "user"},
    "2": {"name": "Чат", "type": "chat"},
    "3": {"name": "Канал", "type": "channel"},
    "4": {"name": "Бот", "type": "bot"},
}

# ===== ПОЛУЧЕНИЕ ЦЕЛИ =====

async def get_target_entity(client, target_type, target_input):
    """Получает entity цели по типу"""
    try:
        if target_type == "user" or target_type == "bot":
            if target_input.startswith('@'):
                return await client.get_entity(target_input)
            else:
                return await client.get_entity(int(target_input))
        elif target_type == "chat":
            # Для чатов используем ID
            return await client.get_entity(int(target_input))
        elif target_type == "channel":
            if target_input.startswith('@'):
                return await client.get_entity(target_input)
            else:
                return await client.get_entity(int(target_input))
    except Exception as e:
        print(f"❌ Ошибка получения цели: {e}")
        return None

# ===== ОТПРАВКА ЖАЛОБЫ =====

async def report_target(client, target_entity, reason):
    """Отправка жалобы на цель"""
    try:
        result = await client(ReportSpamRequest(
            peer=target_entity,
            id=[],
            reason=reason
        ))
        return True, None
    except errors.FloodWaitError as e:
        return False, f"Флуд: ждём {e.seconds}с"
    except errors.UserNotMutualContactError:
        return False, "Не в контактах"
    except Exception as e:
        return False, str(e)

# ===== ВОРКЕР ДЛЯ ОДНОГО АККАУНТА =====

async def reporter_worker(phone, target_input, target_type, reason_code, stats):
    """Один аккаунт отправляет жалобы"""
    client = TelegramClient(
        f"sessions/{phone.replace('+', '')}",
        API_ID,
        API_HASH,
        device_model="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        system_version="Windows 10",
        app_version="5.9.0",
        lang_code="en"
    )
    
    print(f"[*] Подключение {phone}...")
    await client.connect()
    
    # Авторизация
    if not await client.is_user_authorized():
        print(f"[!] {phone} требует авторизации")
        await client.send_code_request(phone)
        code = input(f"🔑 Введите код для {phone}: ")
        try:
            await client.sign_in(phone, code)
        except errors.SessionPasswordNeededError:
            password = input(f"🔐 2FA пароль для {phone}: ")
            await client.sign_in(password=password)
    
    print(f"[+] {phone} авторизован")
    
    # Получаем цель
    target_entity = await get_target_entity(client, target_type, target_input)
    if not target_entity:
        print(f"[-] {phone} не удалось найти цель")
        await client.disconnect()
        return 0, 1
    
    # Получаем название причины
    reason = REPORT_REASONS.get(reason_code, {}).get("reason", "spam")
    
    sent = 0
    failed = 0
    
    for i in range(MAX_REPORTS_PER_ACCOUNT):
        try:
            success, error = await report_target(client, target_entity, reason)
            
            if success:
                sent += 1
                stats['total'] += 1
                stats['success'] += 1
                print(f"[+] {phone} жалоба #{sent} ({REPORT_REASONS[reason_code]['name']})")
            else:
                failed += 1
                stats['failed'] += 1
                print(f"[-] {phone} ошибка: {error}")
            
            if i < MAX_REPORTS_PER_ACCOUNT - 1:
                delay = random.uniform(*DELAY_BETWEEN_REPORTS)
                await asyncio.sleep(delay)
                
        except Exception as e:
            print(f"[-] {phone} критическая ошибка: {e}")
            failed += 1
            stats['failed'] += 1
    
    await client.disconnect()
    print(f"[+] {phone} завершил: {sent} успешно, {failed} ошибок")
    return sent, failed

# ===== ОСНОВНАЯ ФУНКЦИЯ =====

async def main():
    print(f"{'='*70}")
    print(f"  ROCKET TELEGRAM REPORTER v3.0 (МУЛЬТИ-ПРИЧИНЫ + ВСЕ ТИПЫ ЦЕЛЕЙ)")
    print(f"  API_ID: {API_ID}")
    print(f"  Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")
    
    # ===== ВЫБОР ТИПА ЦЕЛИ =====
    print("\n📌 ВЫБЕРИТЕ ТИП ЦЕЛИ:")
    for key, value in TARGET_TYPES.items():
        print(f"  {key}. {value['name']}")
    
    type_choice = input("\n👉 Введите номер типа цели: ").strip()
    if type_choice not in TARGET_TYPES:
        print("❌ Неверный выбор!")
        return
    
    target_type = TARGET_TYPES[type_choice]['type']
    print(f"[*] Выбран тип: {TARGET_TYPES[type_choice]['name']}")
    
    # ===== ВВОД ЦЕЛИ =====
    if target_type in ["user", "bot"]:
        target_input = input("🎯 Введите @username или ID цели: ").strip()
    elif target_type == "chat":
        target_input = input("🎯 Введите ID чата (число): ").strip()
    elif target_type == "channel":
        target_input = input("🎯 Введите @username или ID канала: ").strip()
    
    if not target_input:
        print("❌ Цель не указана!")
        return
    
    # ===== ВЫБОР ПРИЧИНЫ =====
    print("\n📌 ВЫБЕРИТЕ ПРИЧИНУ ЖАЛОБЫ:")
    for key, value in REPORT_REASONS.items():
        print(f"  {key}. {value['name']}")
    
    reason_choice = input("\n👉 Введите номер причины: ").strip()
    if reason_choice not in REPORT_REASONS:
        print("❌ Неверный выбор!")
        return
    
    print(f"[*] Выбрана причина: {REPORT_REASONS[reason_choice]['name']}")
    
    # ===== ПОКАЗЫВАЕМ АККАУНТЫ =====
    print("\n📱 БУДУТ ИСПОЛЬЗОВАНЫ АККАУНТЫ (ПО ОЧЕРЕДИ):")
    for i, phone in enumerate(PHONES, 1):
        print(f"  {i}. {phone}")
    
    print(f"\n[*] Всего аккаунтов: {len(PHONES)}")
    print(f"[*] Жалоб с каждого: {MAX_REPORTS_PER_ACCOUNT}")
    print(f"[*] Всего жалоб: {len(PHONES) * MAX_REPORTS_PER_ACCOUNT}")
    
    input("\n⏎ Нажмите Enter для начала...")
    
    # ===== СОЗДАЁМ ПАПКУ ДЛЯ СЕССИЙ =====
    os.makedirs('sessions', exist_ok=True)
    
    # ===== СТАТИСТИКА =====
    stats = {'total': 0, 'success': 0, 'failed': 0}
    
    # ===== ЗАПУСК ВОРКЕРОВ (ПО ОЧЕРЕДИ) =====
    start_time = time.time()
    
    for phone in PHONES:
        print(f"\n{'='*70}")
        print(f"  ЗАПУСК АККАУНТА: {phone}")
        print(f"{'='*70}")
        
        sent, failed = await reporter_worker(
            phone, 
            target_input, 
            target_type, 
            reason_choice, 
            stats
        )
        
        print(f"[+] {phone} завершил работу")
        
        # Пауза между аккаунтами
        if phone != PHONES[-1]:
            pause = random.uniform(5, 15)
            print(f"⏳ Пауза {pause:.1f}с перед следующим аккаунтом...")
            await asyncio.sleep(pause)
    
    elapsed = time.time() - start_time
    
    # ===== ИТОГИ =====
    print(f"\n{'='*70}")
    print(f"  ИТОГОВЫЕ РЕЗУЛЬТАТЫ")
    print(f"{'='*70}")
    print(f"  📱 Аккаунтов: {len(PHONES)}")
    print(f"  🎯 Цель: {target_input} ({TARGET_TYPES[type_choice]['name']})")
    print(f"  📋 Причина: {REPORT_REASONS[reason_choice]['name']}")
    print(f"  📊 Всего жалоб: {stats['total']}")
    print(f"  ✅ Успешно: {stats['success']}")
    print(f"  ❌ Ошибок: {stats['failed']}")
    print(f"  ⏱️  Время: {elapsed:.1f}с")
    print(f"{'='*70}")

# ===== ЗАПУСК =====

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Прервано пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
