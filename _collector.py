import os

# Имя итогового файла
OUTPUT_FILE = "FULL_BOT_CODE.txt"

# Папки, которые скрипт НЕ будет читать (мусор и бэкапы)
IGNORE_FOLDERS = ["venv", "__pycache__", ".git", ".idea", ".vscode", "backups", "build", "dist"]

# Файлы, которые скрипт НЕ будет читать (бинарные, конфиги, логи)
IGNORE_FILES = [
    "database.db", ".env", "poetry.lock", "package-lock.json", 
    ".gitignore", "_collector.py", OUTPUT_FILE, "discord.log"
]

# Расширения файлов, которые мы ищем
EXTENSIONS = [".py", ".json", ".txt", ".md"]

def collect_code():
    current_folder = os.getcwd()
    print(f"📂 Запуск сканирования в папке: {current_folder}")
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:
        outfile.write("=== ПОЛНЫЙ КОД БОТА ===\n")
        outfile.write("Этот файл создан автоматически.\n\n")

        # os.walk(".") проходит по всем подпапкам, начиная с текущей
        for root, dirs, files in os.walk("."):
            # Удаляем игнорируемые папки из списка посещения
            dirs[:] = [d for d in dirs if d not in IGNORE_FOLDERS]
            
            for file in files:
                if file in IGNORE_FILES: continue
                if not any(file.endswith(ext) for ext in EXTENSIONS): continue

                file_path = os.path.join(root, file)
                
                # Пишем красивый разделитель
                outfile.write(f"\n{'='*50}\n")
                outfile.write(f"📂 ФАЙЛ: {file_path}\n")
                outfile.write(f"{'='*50}\n")
                
                try:
                    with open(file_path, "r", encoding="utf-8") as infile:
                        content = infile.read()
                        
                        # Скрываем токен для безопасности
                        if "config.py" in file_path and "TOKEN" in content:
                            try:
                                part1 = content.split("TOKEN")[0]
                                outfile.write(part1 + 'TOKEN = "СКРЫТО_ДЛЯ_БЕЗОПАСНОСТИ"\n')
                            except:
                                outfile.write(content + "\n")
                        else:
                            outfile.write(content + "\n")
                            
                except Exception as e:
                    outfile.write(f"[Ошибка чтения файла: {e}]\n")

    print(f"✅ Готово! Файл создан: {OUTPUT_FILE}")
    print("Теперь перетяни этот файл в чат.")

if __name__ == "__main__":
    collect_code()