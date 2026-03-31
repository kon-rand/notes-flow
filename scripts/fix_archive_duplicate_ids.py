#!/usr/bin/env python3
"""
Скрипт для переименования дубликатов task ID в архивах.
Используется когда задачи в архиве имеют те же ID что и активные задачи.
"""

import subprocess
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

def run_docker_cmd(cmd: str) -> str:
    """Выполнить команду в Docker контейнере"""
    result = subprocess.run(
        f"docker exec notes-flow-local sh -c '{cmd}'",
        shell=True,
        capture_output=True,
        text=True
    )
    return result.stdout


def get_all_task_ids(user_id: str) -> Dict[str, Set[int]]:
    """
    Получить все task ID по всем файлам.
    Возвращает: {filename: set_of_numbers}
    """
    data = {}
    
    # Читаем active tasks
    tasks_content = run_docker_cmd(f"cat /app/data/{user_id}/tasks.md 2>/dev/null")
    if tasks_content:
        task_ids = set()
        for match in re.finditer(r'^## (task_\d+)', tasks_content, re.MULTILINE):
            num = int(match.group(1).split('_')[1])
            task_ids.add(num)
        data['tasks.md'] = task_ids
    
    # Читаем archive files
    archive_output = run_docker_cmd(f"ls /app/data/{user_id}/archive/*.md 2>/dev/null")
    if archive_output:
        for line in archive_output.strip().split('\n'):
            if line:
                filename = line.strip().split('/')[-1]
                content = run_docker_cmd(f"cat /app/data/{user_id}/archive/{filename} 2>/dev/null")
                if content:
                    task_ids = set()
                    for match in re.finditer(r'^## (task_\d+)', content, re.MULTILINE):
                        num = int(match.group(1).split('_')[1])
                        task_ids.add(num)
                    data[filename] = task_ids
    
    return data


def find_duplicates(all_ids: Dict[str, Set[int]]) -> Dict[int, List[str]]:
    """Найти ID которые встречаются более одного раза"""
    id_to_files: Dict[int, List[str]] = {}
    
    for filename, ids in all_ids.items():
        for num in ids:
            if num not in id_to_files:
                id_to_files[num] = []
            id_to_files[num].append(filename)
    
    # Возвращаем только дубликаты
    return {num: files for num, files in id_to_files.items() if len(files) > 1}


def get_max_id(user_id: str) -> int:
    """Получить максимальный ID среди всех задач"""
    max_num = 0
    
    # Active tasks
    tasks_content = run_docker_cmd(f"cat /app/data/{user_id}/tasks.md 2>/dev/null")
    if tasks_content:
        for match in re.finditer(r'^## (task_\d+)', tasks_content, re.MULTILINE):
            num = int(match.group(1).split('_')[1])
            max_num = max(max_num, num)
    
    # Archive files
    archive_output = run_docker_cmd(f"ls /app/data/{user_id}/archive/*.md 2>/dev/null")
    if archive_output:
        for line in archive_output.strip().split('\n'):
            if line:
                filename = line.strip().split('/')[-1]
                content = run_docker_cmd(f"cat /app/data/{user_id}/archive/{filename} 2>/dev/null")
                if content:
                    for match in re.finditer(r'^## (task_\d+)', content, re.MULTILINE):
                        num = int(match.group(1).split('_')[1])
                        max_num = max(max_num, num)
    
    return max_num


def rename_task_in_file(user_id: str, filename: str, old_id: str, new_id: str) -> bool:
    """Переименовать задачу в файле"""
    old_content = run_docker_cmd(f"cat /app/data/{user_id}/archive/{filename} 2>/dev/null")
    if not old_content:
        return False
    
    new_content = old_content.replace(f'## {old_id}', f'## {new_id}', 1)
    
    # Записываем обратно
    subprocess.run(
        f"docker exec -i notes-flow-local sh -c 'cat > /app/data/{user_id}/archive/{filename}'",
        input=new_content.encode('utf-8'),
        shell=True
    )
    
    return True


def main():
    user_id = "7853438988"
    
    print("=" * 60)
    print("🔧 Миграция: Переименование дубликатов task ID")
    print("=" * 60)
    
    # Получаем все ID
    all_ids = get_all_task_ids(user_id)
    print("\n📊 Найдены задачи:")
    for filename, ids in all_ids.items():
        print(f"  {filename}: {sorted(ids)}")
    
    # Находим дубликаты
    duplicates = find_duplicates(all_ids)
    
    if not duplicates:
        print("\n✅ Дубликатов не найдено")
        return
    
    print(f"\n⚠️  Найдено {len(duplicates)} дубликатов:")
    for num, files in sorted(duplicates.items()):
        print(f"  task_{num:03d}: {', '.join(files)}")
    
    # Получаем максимальный ID
    max_id = get_max_id(user_id)
    print(f"\n📌 Максимальный ID: task_{max_id:03d}")
    
    # Переименовываем дубликаты
    rename_map = {}
    next_num = max_id + 1
    
    for num, files in sorted(duplicates.items()):
        if len(files) > 1:
            # Оставляем первый файл, переименовываем остальные
            for filename in files[1:]:
                old_id = f"task_{num:03d}"
                new_id = f"task_{next_num:03d}"
                
                if rename_task_in_file(user_id, filename, old_id, new_id):
                    rename_map[(old_id, filename)] = new_id
                    next_num += 1
                    print(f"  ✅ {old_id} ({filename}) → {new_id}")
    
    print("\n" + "=" * 60)
    print("✅ Миграция завершена")
    print("=" * 60)
    
    if rename_map:
        print("\n📋 Переименовано:")
        for (old_id, filename), new_id in rename_map.items():
            print(f"  {old_id} ({filename}) → {new_id}")


if __name__ == "__main__":
    main()
