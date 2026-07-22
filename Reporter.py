import asyncio
import random
from telethon import TelegramClient
from telethon.tl.functions.messages import ReportSpamRequest
from telethon.sessions import MemorySession

API_ID = 31709003
API_HASH = "f984479a3498f5389748b22ff0201b88"

AUTH_KEY_HEX = "8e00885b4ee7985d1b22bb23ad1d6f1799b525e6d767beb856a77bda14cf3b28f7460c99cb4d3e0aa2d7996f22b12514865c3ea0a1a36ae6b231b57e76e3919291d0ff82317b9702a84fef558d2c2056b6a8db79998b2de441a6c988bf5c8e635cd90edfc2b66242a85a210a219be7c80b5d74dec04d921095bc4d26daaa4ebcdd9ec18df8be0bd04dd13b834d523a43ec69c599c24934cffd84fc9a6107b00d7b72eb8c80a4e71bf66fb8485d9be4c66307e8b2c5f2b1e9e8529f9142cbb8e0bfd96078335ff65d6661b23028f777723a7624849213e0759aa8d3516f9f7e75c6816ce1b59a57ddfb967272c36bf73dc6640ca51c2356e706a3b886573c8185"

AUTH_KEY = bytes.fromhex(AUTH_KEY_HEX)

async def main():
    session = MemorySession()
    session._auth_key = AUTH_KEY
    
    client = TelegramClient(session, API_ID, API_HASH)
    await client.connect()
    
    try:
        me = await client.get_me()
        print(f"✅ Авторизован: {me.first_name}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return
    
    target = input("\n🎯 Введите @username или ID: ").strip()
    if not target:
        return
    
    try:
        entity = await client.get_entity(target) if target.startswith('@') else await client.get_entity(int(target))
    except Exception as e:
        print(f"❌ Цель не найдена: {e}")
        return
    
    reasons = {
        "1": "spam", "2": "violence", "3": "child_abuse",
        "4": "pornography", "5": "other", "6": "fraud",
        "7": "insult", "8": "fake", "9": "terrorism", "10": "drugs"
    }
    
    print("\n📌 ПРИЧИНЫ:")
    for k, v in reasons.items():
        print(f"  {k}. {v}")
    
    choice = input("👉 Номер причины: ").strip()
    reason = reasons.get(choice, "spam")
    
    count_input = input("📊 Сколько жалоб? (по умолчанию 50): ").strip()
    count = int(count_input) if count_input.isdigit() else 50
    
    print(f"\n🚀 Отправка {count} жалоб...\n")
    
    success = 0
    for i in range(count):
        try:
            await client(ReportSpamRequest(peer=entity, id=[], reason=reason))
            success += 1
            print(f"[+] Жалоба #{i+1} отправлена")
        except Exception as e:
            print(f"[-] Ошибка: {e}")
        
        if i < count - 1:
            await asyncio.sleep(random.uniform(2, 5))
    
    print(f"\n✅ Готово! Отправлено: {success}/{count}")
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
