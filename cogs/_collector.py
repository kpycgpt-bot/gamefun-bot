import os

# Настройки
OUTPUT_FILE = "FULL_BOT_CODE.txt"

# 🔥 ОБНОВЛЕНО: Добавили 'backups' (чтобы не читать копии БД)
IGNORE_FOLDERS = ["venv", "__pycache__", ".git", ".idea", ".vscode", "backups"]

# 🔥 ОБНОВЛЕНО: Добавили сам OUTPUT_FILE (чтобы скрипт не читал свой же отчет)
IGNORE_FILES = ["database.db", ".env", "poetry.lock", "package-lock.json", ".gitignore", "_collector.py", "history.txt", OUTPUT_FILE]

EXTENSIONS = [".py", ".json", ".txt", ".md"]

def collect_code():
    with open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:
        # Пишем заголовок
        outfile.write("=== ПОЛНЫЙ КОД БОТА ===\n")
        outfile.write("Этот файл создан автоматически для проверки ИИ.\n\n")

        # Проходим по всем папкам
        for root, dirs, files in os.walk("."):
            # Исключаем ненужные папки
            dirs[:] = [d for d in dirs if d not in IGNORE_FOLDERS]
            
            for file in files:
                if file in IGNORE_FILES: continue
                if not any(file.endswith(ext) for ext in EXTENSIONS): continue

                file_path = os.path.join(root, file)
                
                # Красивый разделитель
                outfile.write(f"\n{'='*50}\n")
                outfile.write(f"📂 ФАЙЛ: {file_path}\n")
                outfile.write(f"{'='*50}\n")
                
                try:
                    # Пытаемся читать в UTF-8
                    with open(file_path, "r", encoding="utf-8") as infile:
                        content = infile.read()
                        
                        # Если это конфиг, скрываем токен (Безопасность!)
                        if "config.py" in file_path and "TOKEN" in content:
                            try:
                                # Простая защита токена
                                part1 = content.split("TOKEN")[0]
                                outfile.write(part1 + 'TOKEN = "СКРЫТО_ДЛЯ_БЕЗОПАСНОСТИ"\n')
                                continue # Переходим к следующему файлу, чтобы не писать дважды
                            except:
                                pass # Если не вышло скрыть, пишем как есть (но лучше следи за этим)

                        outfile.write(content + "\n")
                        
                except UnicodeDecodeError:
                    # Если файл в кодировке Windows (бывает на VPS)
                    try:
                        with open(file_path, "r", encoding="cp1251") as infile:
                            outfile.write(infile.read() + "\n")
                    except:
                        outfile.write(f"[Ошибка: Неизвестная кодировка файла]\n")
                except Exception as e:
                    outfile.write(f"[Ошибка чтения файла: {e}]\n")

    print(f"✅ Готово! Весь код собран в файл: {OUTPUT_FILE}")
    print("Теперь просто перетяни этот файл в чат с ИИ.")

if __name__ == "__main__":
    collect_code()