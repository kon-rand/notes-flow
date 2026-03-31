"""Скрипт для ежедневного backup задач и архива"""
import os
import shutil
from datetime import datetime
from pathlib import Path


def backup_user_data(user_data_dir: str, backup_dir: str):
    """Создать backup всех данных пользователя"""
    today = datetime.now()
    backup_date = today.strftime('%Y%m%d_%H%M%S')
    
    if not os.path.exists(user_data_dir):
        print(f"User directory {user_data_dir} not found")
        return
    
    # Создаём директорию backup
    user_backup_dir = Path(backup_dir) / str(today.year) / str(today.month) / backup_date
    
    try:
        user_backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Копируем все файлы пользователя
        for item in os.listdir(user_data_dir):
            src = os.path.join(user_data_dir, item)
            dst = os.path.join(user_backup_dir, item)
            
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        
        print(f"✅ Backup создан: {user_backup_dir}")
        
    except Exception as e:
        print(f"❌ Error creating backup: {e}")


def main():
    """Основная функция backup"""
    data_dir = "/app/data"
    backup_dir = "/app/backup"
    
    if not os.path.exists(data_dir):
        print(f"Data directory {data_dir} not found")
        return
    
    # Находим всех пользователей
    for user_id in os.listdir(data_dir):
        user_data_dir = os.path.join(data_dir, user_id)
        if os.path.isdir(user_data_dir):
            print(f"Backing up user {user_id}...")
            backup_user_data(user_data_dir, backup_dir)
    
    print("✅ Backup completed")


if __name__ == "__main__":
    main()
