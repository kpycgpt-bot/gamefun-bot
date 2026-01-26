#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Умный сборщик кода Discord бота
Создает структурированные файлы для проверки ИИ
"""

import os
from datetime import datetime

# ==========================================
# НАСТРОЙКИ
# ==========================================

# Категории файлов
CATEGORIES = {
    'CORE': {
        'name': '1_BOT_CORE',
        'description': 'Основные файлы бота',
        'files': ['main.py', 'database.py', 'config.py', 'utils.py'],
        'folders': []
    },
    'COGS_1': {
        'name': '2_BOT_COGS_BASIC',
        'description': 'Базовые модули (economy, moderation, voice, setup, help)',
        'files': [],
        'folders': [],
        'cogs': ['economy.py', 'moderation.py', 'voice_manager.py', 'setup.py', 'help.py']
    },
    'COGS_2': {
        'name': '3_BOT_COGS_EXTENDED',
        'description': 'Расширенные модули (tickets, welcome, levels, casino, roles)',
        'files': [],
        'folders': [],
        'cogs': ['tickets.py', 'welcome.py', 'levels.py', 'casino.py', 'roles_panel.py']
    },
    'COGS_3': {
        'name': '4_BOT_COGS_EXTRA',
        'description': 'Дополнительные модули (invites, backup, automod, rules, events)',
        'files': [],
        'folders': [],
        'cogs': ['invites.py', 'backup.py', 'automod.py', 'rules.py', 'random_events.py']
    },
    'CONFIG': {
        'name': '5_BOT_CONFIG',
        'description': 'Конфигурация и документация',
        'files': ['requirements.txt', '.env.example', '.gitignore', 'README.md'],
        'folders': []
    }
}

# Игнорируемые папки
IGNORE_FOLDERS = ['venv', '__pycache__', '.git', '.idea', '.vscode', 'backups', 'build', 'dist', 'node_modules']

# Игнорируемые файлы
IGNORE_FILES = ['database.db', '.env', 'discord.log', 'bot.log', 'poetry.lock', 'package-lock.json']

# ==========================================
# ФУНКЦИИ
# ==========================================

def create_header(category_name, description):
    """Создает красивый заголовок файла"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    header = f"""
{'='*80}
║                    DISCORD БОТ - КОД ДЛЯ ПРОВЕРКИ                        ║
{'='*80}

📦 КАТЕГОРИЯ: {category_name}
📝 ОПИСАНИЕ: {description}
⏰ СОЗДАНО: {timestamp}

{'='*80}

СОДЕРЖАНИЕ:

"""
    return header

def create_file_block(filepath, content):
    """Создает красивый блок для файла"""
    separator = "=" * 80
    
    block = f"""
{separator}
📄 ФАЙЛ: {filepath}
{separator}

{content}

"""
    return block

def read_file_safe(filepath):
    """Безопасное чтение файла"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Скрываем токены для безопасности
        if '.env' in filepath or 'TOKEN' in content:
            lines = content.split('\n')
            safe_lines = []
            for line in lines:
                if 'TOKEN' in line and '=' in line:
                    key = line.split('=')[0]
                    safe_lines.append(f"{key}=СКРЫТО_ДЛЯ_БЕЗОПАСНОСТИ")
                else:
                    safe_lines.append(line)
            return '\n'.join(safe_lines)
        
        return content
        
    except Exception as e:
        return f"[ОШИБКА ЧТЕНИЯ: {e}]"

def collect_category_files(category_info, base_path='.'):
    """Собирает файлы для категории"""
    collected = []
    
    # Собираем обычные файлы
    for filename in category_info.get('files', []):
        filepath = os.path.join(base_path, filename)
        if os.path.exists(filepath):
            content = read_file_safe(filepath)
            collected.append((filename, content))
    
    # Собираем файлы из cogs
    if 'cogs' in category_info:
        cogs_path = os.path.join(base_path, 'cogs')
        if os.path.exists(cogs_path):
            for cog_file in category_info['cogs']:
                filepath = os.path.join(cogs_path, cog_file)
                if os.path.exists(filepath):
                    content = read_file_safe(filepath)
                    collected.append((f"cogs/{cog_file}", content))
    
    return collected

def create_toc(files):
    """Создает оглавление"""
    toc = ""
    for idx, (filename, _) in enumerate(files, 1):
        toc += f"   {idx}. {filename}\n"
    return toc + "\n"

def get_file_stats(content):
    """Получает статистику файла"""
    lines = len(content.split('\n'))
    chars = len(content)
    size_kb = chars / 1024
    return lines, chars, size_kb

def main():
    """Основная функция"""
    print("🤖 Умный сборщик кода Discord бота")
    print("=" * 50)
    
    base_path = '.'
    output_files = []
    
    # Обрабатываем каждую категорию
    for category_key, category_info in CATEGORIES.items():
        output_filename = f"{category_info['name']}.txt"
        
        print(f"\n📦 Обработка: {category_info['description']}")
        
        # Собираем файлы
        files = collect_category_files(category_info, base_path)
        
        if not files:
            print(f"   ⚠️  Нет файлов для этой категории")
            continue
        
        # Создаем выходной файл
        with open(output_filename, 'w', encoding='utf-8') as outfile:
            # Заголовок
            header = create_header(category_info['name'], category_info['description'])
            outfile.write(header)
            
            # Оглавление
            toc = create_toc(files)
            outfile.write(toc)
            
            # Файлы
            total_lines = 0
            for filename, content in files:
                block = create_file_block(filename, content)
                outfile.write(block)
                
                lines, chars, size_kb = get_file_stats(content)
                total_lines += lines
                print(f"   ✅ {filename} ({lines} строк, {size_kb:.1f} KB)")
            
            # Подвал
            footer = f"""
{'='*80}
📊 СТАТИСТИКА КАТЕГОРИИ:
   • Файлов: {len(files)}
   • Строк кода: {total_lines}
   • Размер файла: {os.path.getsize(output_filename) / 1024:.2f} KB
{'='*80}
"""
            outfile.write(footer)
        
        output_files.append(output_filename)
        print(f"   💾 Создан: {output_filename}")
    
    # Итоговая статистика
    print("\n" + "=" * 50)
    print("🎉 ГОТОВО!")
    print("=" * 50)
    print(f"\n📋 Создано файлов: {len(output_files)}")
    print("\nСПИСОК ФАЙЛОВ ДЛЯ ПРОВЕРКИ:")
    
    total_size = 0
    for idx, filename in enumerate(output_files, 1):
        size = os.path.getsize(filename) / 1024
        total_size += size
        print(f"   {idx}. {filename} ({size:.2f} KB)")
    
    print(f"\n💾 Общий размер: {total_size:.2f} KB ({total_size / 1024:.2f} MB)")
    
    print("\n" + "=" * 50)
    print("📤 ЧТО ДАЛЬШЕ:")
    print("   1. Перетащи файлы в чат по порядку")
    print("   2. Попроси ИИ проверить каждый файл")
    print("   3. Исправь найденные ошибки")
    print("=" * 50)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Прервано пользователем")
    except Exception as e:
        print(f"\n\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
