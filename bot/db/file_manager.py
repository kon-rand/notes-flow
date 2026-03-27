import io
import json
import shutil
import tempfile
import yaml  # type: ignore[import-untyped]
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from bot.config.user_settings import SETTINGS_FILE
from bot.db.models import InboxMessage, Task, Note


class FileManager:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)

    def _get_user_dir(self, user_id: int) -> Path:
        user_dir = self.data_dir / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir

    def _generate_id(self, prefix: str, existing_ids: List[str]) -> str:
        counter = 1
        while True:
            id = f"{prefix}_{counter:03d}"
            if id not in existing_ids:
                return id
            counter += 1

    def _read_file(self, file_path: Path) -> Optional[dict]:
        if not file_path.exists():
            return None
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return self._parse_file(content)

    def _parse_file(self, content: str) -> dict:
        parts = content.split("---\n")
        if len(parts) < 3:
            return {"type": None, "items": []}
        try:
            metadata = yaml.safe_load(parts[1])
        except yaml.YAMLError:
            metadata = {}
        items = []
        # Split by both formats: '\n---\n## ' and '\n## '
        content = parts[2].strip()
        item_blocks = content.split("\n## ")
        for block in item_blocks:
            block = block.strip()
            if not block:
                continue
            lines = block.split("\n")
            if not lines:
                continue
            item_id = lines[0].strip().lstrip("#").strip()
            item_data: dict[str, object] = {}
            for line in lines[1:]:
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()
                    if value == "null":
                        item_data[key] = None
                    elif value.startswith("[") and value.endswith("]"):
                        inner = value[1:-1].strip()
                        if inner:
                            item_data[key] = [x.strip().strip('"').strip("'") for x in inner.split(",")]
                        else:
                            item_data[key] = []
                    else:
                        try:
                            item_data[key] = datetime.fromisoformat(value)
                        except ValueError:
                            item_data[key] = value
            items.append((item_id, item_data))
        return {"metadata": metadata, "items": items}

    def _serialize_item(self, item_data: dict) -> str:
        lines = []
        for key, value in item_data.items():
            if isinstance(value, datetime):
                value = value.isoformat()
            elif value is None:
                value = "null"
            elif isinstance(value, list):
                value = "[" + ", ".join(f'"{x}"' for x in value) + "]"
            else:
                value = str(value)
            lines.append(f"{key}: {value}")
        return "\n".join(lines)

    def _write_file(self, file_path: Path, file_type: str, items: List[tuple]):
        content_parts = ["---", f"type: {file_type}", "---"]
        for item_id, item_data in items:
            content_parts.append(f"\n## {item_id}")
            content_parts.append(self._serialize_item(item_data))
        content = "\n".join(content_parts)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    def _load_all_items(self, user_id: int, file_type: str) -> List[tuple]:
        file_path = self._get_user_dir(user_id) / f"{file_type}.md"
        data = self._read_file(file_path)
        if data is None:
            return []
        return data.get("items", [])

    def append_message(self, user_id: int, message: InboxMessage) -> None:
        items = self._load_all_items(user_id, "inbox")
        existing_ids = [item[0] for item in items]
        msg_id = self._generate_id("msg", existing_ids)
        item_data = {
            "timestamp": message.timestamp,
            "from_user": message.from_user,
            "sender_id": message.sender_id,
            "sender_name": message.sender_name,
            "content": message.content,
            "chat_id": message.chat_id,
        }
        items.append((msg_id, item_data))
        file_path = self._get_user_dir(user_id) / "inbox.md"
        self._write_file(file_path, "inbox", items)

    def read_messages(self, user_id: int) -> List[InboxMessage]:
        items = self._load_all_items(user_id, "inbox")
        messages = []
        for item_id, item_data in items:
            try:
                msg = InboxMessage(
                    id=item_id,
                    timestamp=item_data.get("timestamp"),
                    from_user=item_data.get("from_user"),
                    sender_id=item_data.get("sender_id"),
                    sender_name=item_data.get("sender_name"),
                    content=item_data.get("content", ""),
                    chat_id=item_data.get("chat_id"),
                )
                messages.append(msg)
            except Exception:
                continue
        return messages

    def clear_messages(self, user_id: int) -> None:
        inbox_path = self._get_user_dir(user_id) / "inbox.md"
        if inbox_path.exists():
            inbox_path.unlink()
    
    def save_backup(self, user_id: int) -> str:
        inbox_path = self._get_user_dir(user_id) / "inbox.md"
        if not inbox_path.exists():
            return ""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self._get_user_dir(user_id) / f"inbox_backup_{timestamp}.md"
        backup_path.write_text(inbox_path.read_text(encoding="utf-8"), encoding="utf-8")
        return str(backup_path)

    def create_backup(self, user_id: int) -> Optional[io.BytesIO]:
        """
        Create a ZIP backup of all user data.
        
        Collects: inbox.md, tasks.md, notes.md, archive/*, inbox_backup/*
        Returns: BytesIO object containing ZIP data, or None if no data found
        
        Must NOT include: user_settings.json (global file)
        """
        user_dir = self.data_dir / str(user_id)
        
        if not user_dir.exists():
            return None
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            files_to_include = [
                "inbox.md",
                "tasks.md",
                "notes.md",
            ]
            
            for filename in files_to_include:
                file_path = user_dir / filename
                if file_path.exists():
                    arcname = filename
                    zip_file.write(file_path, arcname)
            
            archive_dir = user_dir / "archive"
            if archive_dir.exists() and archive_dir.is_dir():
                for file_path in archive_dir.glob("*"):
                    if file_path.is_file():
                        arcname = f"archive/{file_path.name}"
                        zip_file.write(file_path, arcname)
            
            inbox_backup_dir = user_dir / "inbox_backup"
            if inbox_backup_dir.exists() and inbox_backup_dir.is_dir():
                for file_path in inbox_backup_dir.glob("*"):
                    if file_path.is_file():
                        arcname = f"inbox_backup/{file_path.name}"
                        zip_file.write(file_path, arcname)
            
            if zip_file.namelist():
                zip_buffer.seek(0)
                return zip_buffer
            else:
                return None

    def restore_from_backup(self, user_id: int, zip_path: str) -> dict:
        """
        Restore user data from a ZIP backup file.
        
        Args:
            user_id: The ID of the user to restore data for.
            zip_path: Path to the ZIP backup file.
            
        Returns:
            Dict with success status and either extracted files info or error message.
            On success: {'success': True, 'files_restored': [...], 'message': '...'}
            On failure: {'success': False, 'error': '...'}
            
        Raises:
            ValueError: If zip_path is invalid or empty.
            FileNotFoundError: If ZIP file does not exist.
            zipfile.BadZipFile: If file is not a valid ZIP archive.
        """
        zip_file = Path(zip_path)
        
        if not zip_file.exists():
            return {
                'success': False,
                'error': f'Backup file not found: {zip_path}'
            }
        
        if not zip_file.is_file():
            return {
                'success': False,
                'error': f'Path is not a file: {zip_path}'
            }
        
        try:
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                if not file_list:
                    return {
                        'success': False,
                        'error': 'Backup file is empty'
                    }
        except zipfile.BadZipFile:
            return {
                'success': False,
                'error': f'Invalid ZIP file: {zip_path}'
            }
        
        temp_dir = None
        pre_restore_backup = None
        
        try:
            temp_dir = Path(tempfile.mkdtemp(prefix='restore_'))
            
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
                
                files_extracted = len(zip_ref.namelist())
            
            required_files = ['inbox.md', 'tasks.md', 'notes.md']
            missing_files = [f for f in required_files if not (temp_dir / f).exists()]
            
            if missing_files:
                return {
                    'success': False,
                    'error': f'Missing required files in backup: {", ".join(missing_files)}'
                }
            
            user_dir = self._get_user_dir(user_id)
            
            settings_path = Path(str(SETTINGS_FILE))
            if settings_path.exists():
                pre_restore_backup = Path('data') / f'user_settings_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
                shutil.copy2(settings_path, pre_restore_backup)
            
            for filename in ['inbox.md', 'tasks.md', 'notes.md']:
                src = temp_dir / filename
                dst = user_dir / filename
                shutil.copy2(src, dst)
            
            archive_dir = temp_dir / 'archive'
            if archive_dir.exists() and archive_dir.is_dir():
                target_archive_dir = user_dir / 'archive'
                target_archive_dir.mkdir(parents=True, exist_ok=True)
                for file_path in archive_dir.glob('*'):
                    if file_path.is_file():
                        shutil.copy2(file_path, target_archive_dir / file_path.name)
            
            inbox_backup_dir = temp_dir / 'inbox_backup'
            if inbox_backup_dir.exists() and inbox_backup_dir.is_dir():
                target_inbox_backup_dir = user_dir / 'inbox_backup'
                target_inbox_backup_dir.mkdir(parents=True, exist_ok=True)
                for file_path in inbox_backup_dir.glob('*'):
                    if file_path.is_file():
                        shutil.copy2(file_path, target_inbox_backup_dir / file_path.name)
            
            user_settings_file = temp_dir / 'user_settings.json'
            if user_settings_file.exists():
                try:
                    with open(user_settings_file, 'r', encoding='utf-8') as f:
                        settings_data = json.load(f)
                    
                    if isinstance(settings_data, dict) and str(user_id) in settings_data:
                        settings = settings_data[str(user_id)]
                        if isinstance(settings, dict) and 'delay' in settings:
                            delay = settings['delay']
                            if isinstance(delay, int) and delay > 0:
                                from bot.config.user_settings import user_settings
                                user_settings.set_delay(user_id, delay)
                except (json.JSONDecodeError, KeyError, TypeError):
                    pass
            
            return {
                'success': True,
                'files_restored': [
                    'inbox.md',
                    'tasks.md',
                    'notes.md',
                ] + (['archive/*'] if archive_dir.exists() else []) + (['inbox_backup/*'] if inbox_backup_dir.exists() else []),
                'message': f'Successfully restored {files_extracted} files from backup',
                'pre_restore_backup': str(pre_restore_backup) if pre_restore_backup else None
            }
            
        except zipfile.BadZipFile:
            return {
                'success': False,
                'error': f'Invalid ZIP file: {zip_file}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error during restore: {str(e)}'
            }
        finally:
            if temp_dir and temp_dir.exists():
                shutil.rmtree(temp_dir)

    def append_task(self, user_id: int, task: Task) -> None:
        items = self._load_all_items(user_id, "tasks")
        existing_ids = [item[0] for item in items]
        task_id = self._generate_id("task", existing_ids)
        item_data = {
            "title": task.title,
            "tags": task.tags,
            "status": task.status,
            "created_at": task.created_at,
            "completed_at": task.completed_at,
            "archived_at": task.archived_at,
            "source_message_ids": task.source_message_ids,
            "content": task.content,
        }
        items.append((task_id, item_data))
        file_path = self._get_user_dir(user_id) / "tasks.md"
        self._write_file(file_path, "task", items)

    def read_tasks(self, user_id: int) -> List[Task]:
        items = self._load_all_items(user_id, "tasks")
        tasks = []
        for item_id, item_data in items:
            try:
                task = Task(
                    id=item_id,
                    title=item_data.get("title", ""),
                    tags=item_data.get("tags", []),
                    status=item_data.get("status", "pending"),
                    created_at=item_data.get("created_at"),
                    completed_at=item_data.get("completed_at"),
                    archived_at=item_data.get("archived_at"),
                    source_message_ids=item_data.get("source_message_ids", []),
                    content=item_data.get("content", ""),
                )
                tasks.append(task)
            except Exception:
                continue
        return tasks

    def update_task_status(self, user_id: int, task_id: str, status: str) -> bool:
        items = self._load_all_items(user_id, "tasks")
        for i, (id, item_data) in enumerate(items):
            if id == task_id:
                if status == "completed" and not item_data.get("completed_at"):
                    item_data["completed_at"] = datetime.now()
                items[i] = (id, {**item_data, "status": status})
                file_path = self._get_user_dir(user_id) / "tasks.md"
                self._write_file(file_path, "task", items)
                return True
        return False

    def delete_task(self, user_id: int, task_id: str) -> bool:
        items = self._load_all_items(user_id, "tasks")
        existing_ids = [id for id, _ in items]
        
        if task_id not in existing_ids:
            return False
        
        items = [(id, data) for id, data in items if id != task_id]
        
        if len(items) == 0:
            tasks_path = self._get_user_dir(user_id) / "tasks.md"
            if tasks_path.exists():
                tasks_path.unlink()
            return True
        
        file_path = self._get_user_dir(user_id) / "tasks.md"
        self._write_file(file_path, "task", items)
        return True

    def append_note(self, user_id: int, note: Note) -> None:
        items = self._load_all_items(user_id, "notes")
        existing_ids = [item[0] for item in items]
        note_id = self._generate_id("note", existing_ids)
        item_data = {
            "title": note.title,
            "tags": note.tags,
            "created_at": note.created_at,
            "source_message_ids": note.source_message_ids,
            "content": note.content,
        }
        items.append((note_id, item_data))
        file_path = self._get_user_dir(user_id) / "notes.md"
        self._write_file(file_path, "note", items)

    def read_notes(self, user_id: int) -> List[Note]:
        items = self._load_all_items(user_id, "notes")
        notes = []
        for item_id, item_data in items:
            try:
                note = Note(
                    id=item_id,
                    title=item_data.get("title", ""),
                    tags=item_data.get("tags", []),
                    created_at=item_data.get("created_at"),
                    source_message_ids=item_data.get("source_message_ids", []),
                    content=item_data.get("content", ""),
                )
                notes.append(note)
            except Exception:
                continue
        return notes

    def _append_to_archive(self, archive_file: Path, tasks: List[Task]) -> None:
        """Добавить задачи в файл архива"""
        if archive_file.exists():
            existing_data = self._read_file(archive_file)
            if existing_data is None:
                existing_data = {"metadata": {}, "items": []}
            existing_items = existing_data.get("items", [])
        else:
            existing_items = []

        for task in tasks:
            item_data = {
                "title": task.title,
                "tags": task.tags,
                "status": task.status,
                "created_at": task.created_at,
                "completed_at": task.completed_at,
                "archived_at": task.archived_at,
                "source_message_ids": task.source_message_ids,
                "content": task.content,
            }
            existing_items.append((task.id, item_data))

        metadata = {"type": "archived_tasks", "date": archive_file.stem}
        self._write_file_with_metadata(archive_file, metadata, existing_items)

    def _write_file_with_metadata(self, file_path: Path, metadata: dict, items: List[tuple]) -> None:
        """Записать файл с метаданными"""
        content_parts = ["---"]
        for key, value in metadata.items():
            if isinstance(value, datetime):
                value = value.isoformat()
            content_parts.append(f"{key}: {value}")
        content_parts.append("---")

        for item_id, item_data in items:
            content_parts.append(f"\n## {item_id}")
            content_parts.append(self._serialize_item(item_data))

        content = "\n".join(content_parts)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    def _remove_tasks(self, user_id: int, task_ids: List[str]) -> None:
        """Удалить задачи из tasks.md по списку ID"""
        items = self._load_all_items(user_id, "tasks")
        items = [(id, data) for id, data in items if id not in task_ids]

        tasks_path = self._get_user_dir(user_id) / "tasks.md"
        if len(items) == 0:
            if tasks_path.exists():
                tasks_path.unlink()
        else:
            self._write_file(tasks_path, "task", items)

    def archive_completed_tasks(self, user_id: int, date: datetime) -> List[Task]:
        """Перенести все выполненные задачи за сегодня и старше в архив"""
        tasks = self.read_tasks(user_id)
        completed = [
            t for t in tasks
            if t.status == "completed" and t.completed_at and t.completed_at.date() <= date.date()
        ]

        if not completed:
            return []

        archive_dir = self._get_user_dir(user_id) / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)
        archive_file = archive_dir / f"{date.strftime('%Y-%m-%d')}.md"

        for task in completed:
            task.archived_at = date
        self._append_to_archive(archive_file, completed)
        self._remove_tasks(user_id, [t.id for t in completed])

        return completed

    def get_archive_dates(self, user_id: int) -> List[str]:
        """Получить список дат, для которых есть файлы архива"""
        archive_dir = self._get_user_dir(user_id) / "archive"
        if not archive_dir.exists():
            return []

        dates = []
        for file in archive_dir.glob("*.md"):
            dates.append(file.stem)

        return sorted(dates)

    def get_tasks_by_archive_date(self, user_id: int, date: str) -> List[Task]:
        """Получить все задачи из архива за указанную дату"""
        archive_dir = self._get_user_dir(user_id) / "archive"
        archive_file = archive_dir / f"{date}.md"

        data = self._read_file(archive_file)
        if data is None:
            return []

        tasks = []
        for item_id, item_data in data.get("items", []):
            try:
                task = Task(
                    id=item_id,
                    title=item_data.get("title", ""),
                    tags=item_data.get("tags", []),
                    status=item_data.get("status", "pending"),
                    created_at=item_data.get("created_at"),
                    completed_at=item_data.get("completed_at"),
                    archived_at=item_data.get("archived_at"),
                    source_message_ids=item_data.get("source_message_ids", []),
                    content=item_data.get("content", ""),
                )
                tasks.append(task)
            except Exception:
                continue

        return tasks