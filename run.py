import subprocess
import sys
import time

print("🚀 ЗАПУСК СИСТЕМЫ АВТО-РЕСТАРТА...")

while True:
    print("\n🔄 Запуск бота...")

    # Запускаем main.py
    p = subprocess.Popen([sys.executable, "main.py"])
    p.wait()

    # Если бот упал или выключился
    print("⚠️ Бот выключился! Перезапуск через 3 секунды...")
    time.sleep(3)