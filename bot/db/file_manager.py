import yaml  # type: ignore[import-untyped]
from datetime import datetime
from pathlib import Path
from typing import List, Optional

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

    def append_task(self, user_id: int, task: Task) -> None:
        items = self._load_all_items(user_id, "tasks")
        existing_ids = [item[0] for item in items]
        task_id = self._generate_id("task", existing_ids)
        item_data = {
            "title": task.title,
            "tags": task.tags,
            "status": task.status,
            "created_at": task.created_at,
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
                items[i] = (id, {**item_data, "status": status})
                file_path = self._get_user_dir(user_id) / "tasks.md"
                self._write_file(file_path, "task", items)
                return True
        return False

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