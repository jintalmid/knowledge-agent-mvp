import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from app.core.config import get_settings


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(get_settings().sqlite_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@contextmanager
def db_session() -> Iterator[sqlite3.Connection]:
    connection = get_connection()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db() -> None:
    with db_session() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL,
                owner_user_id TEXT NOT NULL,
                department_id TEXT NOT NULL,
                security_level TEXT NOT NULL,
                knowledge_base_id TEXT,
                template_id TEXT,
                iteration_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute("CREATE INDEX IF NOT EXISTS idx_tasks_owner_user_id ON tasks(owner_user_id)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS physical_files (
                id TEXT PRIMARY KEY,
                content_hash TEXT NOT NULL UNIQUE,
                original_filename TEXT NOT NULL,
                file_ext TEXT NOT NULL,
                mime_type TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                storage_path TEXT NOT NULL,
                ref_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS task_files (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                physical_file_id TEXT NOT NULL,
                display_name TEXT NOT NULL,
                file_role TEXT NOT NULL,
                parse_status TEXT NOT NULL,
                summary_status TEXT NOT NULL,
                embedding_status TEXT NOT NULL,
                owner_user_id TEXT NOT NULL,
                department_id TEXT NOT NULL,
                security_level TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                FOREIGN KEY(physical_file_id) REFERENCES physical_files(id)
            )
            """
        )
        connection.execute("CREATE INDEX IF NOT EXISTS idx_task_files_task_id ON task_files(task_id)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_task_files_physical_file_id ON task_files(physical_file_id)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_physical_files_content_hash ON physical_files(content_hash)")
