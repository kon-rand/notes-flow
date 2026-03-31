#!/usr/bin/env python3
"""
Скрипт миграции для исправления дубликатов task ID.

Проблема: некоторые задачи имеют одинаковые ID (например, task_002 дважды).
Решение: переименовать дубликаты в новые уникальные ID.
"""

import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple


def extract_task_number(task_id: str) -> int:
    """Извлечь номер задачи из ID (например, task_001 -> 1)"""
    match = re.search(r'task_(\d+)', task_id)
    if match:
        return int(match.group(1))
    return 0


def read_tasks_file(file_path: Path) -> Tuple[str, List[dict]]:
    """Прочитать задачи из файла tasks.md"""
    if not file_path.exists():
        return "", []
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Парсим YAML фронтмат и задачи
    items = []
    parts = content.split("---\n")
    
    if len(parts) < 3:
        return content, []
    
    content_part = parts[2].strip()
    task_blocks = content_part.split("\n## ")
    
    for block in task_blocks:
        block = block.strip()
        if not block:
            continue
        
        lines = block.split("\n")
        if not lines:
            continue
        
        # Удаляем возможное дублирование ##
        task_id = lines[0].strip().replace("## ", "").strip()
        task_data = {}
        
        for line in lines[1:]:
            if ":" in line and not line.startswith(" "):
                key, value = line.split(":", 1)
                task_data[key.strip()] = value.strip()
            elif line.startswith(" "):
                # Продолжение content
                if "content" in task_data:
                    task_data["content"] += "\n" + line.strip()
        
        items.append({
            "id": task_id,
            "data": task_data
        })
    
    return content, items


def find_duplicates(tasks: List[dict]) -> Dict[int, List[dict]]:
    """Найти дубликаты ID"""
    id_map: Dict[int, List[dict]] = {}
    
    for task in tasks:
        num = extract_task_number(task["id"])
        if num not in id_map:
            id_map[num] = []
        id_map[num].append(task)
    
    # Возвращаем только дубликаты (больше 1 задачи с одним ID)
    return {num: tasks for num, tasks in id_map.items() if len(tasks) > 1}


def fix_duplicate_tasks(data_dir: str = "data") -> Dict[str, int]:
    """
    Исправить дубликаты task ID во всех user директориях.
    
    Returns:
        Dict с информацией о миграции:
        {
            "user_id": {
                "duplicates_found": int,
                "tasks_renamed": int,
                "new_ids": {"old_id": "new_id", ...}
            }
        }
    """
    result = {}
    data_path = Path(data_dir)
    
    if not data_path.exists():
        print(f"❌ Директория {data_dir} не найдена")
        return result
    
    for user_dir in data_path.iterdir():
        if not user_dir.is_dir():
            continue
        
        user_id = user_dir.name
        tasks_file = user_dir / "tasks.md"
        
        if not tasks_file.exists():
            continue
        
        print(f"\n📁 Обработка пользователя {user_id}...")
        
        # Читаем задачи
        content, tasks = read_tasks_file(tasks_file)
        
        if not tasks:
            print(f"   ✅ Нет задач")
            continue
        
        # Находим дубликаты
        duplicates = find_duplicates(tasks)
        
        if not duplicates:
            print(f"   ✅ Дубликатов не найдено")
            continue
        
        print(f"   🔍 Найдено {len(duplicates)} дубликатов")
        
        # Собираем все существующие номера
        existing_numbers = set()
        for task in tasks:
            num = extract_task_number(task["id"])
            existing_numbers.add(num)
        
        # Определяем максимальный номер
        max_num = max(existing_numbers) if existing_numbers else 0
        
        # Исправляем дубликаты
        rename_map = {}
        for num, dup_tasks in duplicates.items():
            print(f"   ⚠️  Дубликат task_{num:03d}: {len(dup_tasks)} задач")
            
            # Оставляем первую задачу с этим ID
            # Переименовываем остальные
            for i, task in enumerate(dup_tasks[1:], start=1):
                # Ищем новый уникальный номер
                new_num = max_num + i
                new_id = f"task_{new_num:03d}"
                
                old_id = task["id"]
                rename_map[old_id] = new_id
                task["id"] = new_id
                
                print(f"      → {new_id} (было: {old_id})")
        
        if rename_map:
            # Пересоздаем файл с новыми ID
            new_content_parts = ["---", "type: task", "---"]
            
            for task in tasks:
                new_content_parts.append(f"\n## {task['id']}")
                for key, value in task["data"].items():
                    if key == "content" and "\n" in value:
                        # Content с переносами строк
                        lines = value.split("\n")
                        new_content_parts.append(f"{key}: {lines[0]}")
                        for line in lines[1:]:
                            new_content_parts.append(f"  {line}")
                    else:
                        new_content_parts.append(f"{key}: {value}")
            
            new_content = "\n".join(new_content_parts)
            
            # Сохраняем
            with open(tasks_file, "w", encoding="utf-8") as f:
                f.write(new_content)
            
            result[user_id] = {
                "duplicates_found": sum(len(t) - 1 for t in duplicates.values()),
                "tasks_renamed": len(rename_map),
                "new_ids": rename_map
            }
            
            print(f"   ✅ Исправлено {len(rename_map)} дубликатов")
        else:
            result[user_id] = {
                "duplicates_found": 0,
                "tasks_renamed": 0,
                "new_ids": {}
            }
    
    return result


def main():
    """Точка входа"""
    print("=" * 60)
    print("🔧 Миграция: Исправление дубликатов task ID")
    print("=" * 60)
    
    start_time = datetime.now()
    
    # Выполняем миграцию
    migration_result = fix_duplicate_tasks("data")
    
    # Выводим итог
    print("\n" + "=" * 60)
    print("📊 Итоги миграции:")
    print("=" * 60)
    
    total_renamed = 0
    for user_id, stats in migration_result.items():
        if stats["tasks_renamed"] > 0:
            print(f"\n{user_id}:")
            print(f"  Дубликатов найдено: {stats['duplicates_found']}")
            print(f"  Задач переименовано: {stats['tasks_renamed']}")
            print(f"  Новые ID:")
            for old_id, new_id in stats["new_ids"].items():
                print(f"    {old_id} → {new_id}")
            total_renamed += stats["tasks_renamed"]
    
    if total_renamed == 0:
        print("\n✅ Дубликатов не найдено. Миграция не потребовалась.")
    else:
        print(f"\n✅ Всего переименовано задач: {total_renamed}")
    
    end_time = datetime.now()
    duration = end_time - start_time
    print(f"\n⏱️  Время выполнения: {duration}")
    
    print("\n" + "=" * 60)
    print("✅ Миграция завершена")
    print("=" * 60)


if __name__ == "__main__":
    main()
