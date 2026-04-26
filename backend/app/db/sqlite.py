import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from app.core.config import get_settings


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(get_settings().sqlite_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _ensure_column(connection: sqlite3.Connection, table_name: str, column_name: str, column_definition: str) -> None:
    columns = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    if column_name not in {column["name"] for column in columns}:
        connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")


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
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS parsed_contents (
                id TEXT PRIMARY KEY,
                task_file_id TEXT NOT NULL UNIQUE,
                physical_file_id TEXT NOT NULL,
                content_type TEXT NOT NULL,
                text_content TEXT,
                excel_profile_json TEXT,
                parse_quality TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(task_file_id) REFERENCES task_files(id) ON DELETE CASCADE,
                FOREIGN KEY(physical_file_id) REFERENCES physical_files(id)
            )
            """
        )
        connection.execute("CREATE INDEX IF NOT EXISTS idx_parsed_contents_task_file_id ON parsed_contents(task_file_id)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_parsed_contents_physical_file_id ON parsed_contents(physical_file_id)")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS llm_call_logs (
                id TEXT PRIMARY KEY,
                task_id TEXT,
                agent_run_id TEXT,
                iteration_id TEXT,
                module_name TEXT NOT NULL,
                provider_type TEXT NOT NULL,
                model_name TEXT NOT NULL,
                prompt_preview TEXT NOT NULL,
                response_preview TEXT,
                status TEXT NOT NULL,
                error_message TEXT,
                latency_ms INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        _ensure_column(connection, "llm_call_logs", "agent_run_id", "TEXT")
        _ensure_column(connection, "llm_call_logs", "iteration_id", "TEXT")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_llm_call_logs_task_id ON llm_call_logs(task_id)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_llm_call_logs_agent_run_id ON llm_call_logs(agent_run_id)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_llm_call_logs_iteration_id ON llm_call_logs(iteration_id)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_llm_call_logs_created_at ON llm_call_logs(created_at)")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS file_summaries (
                id TEXT PRIMARY KEY,
                task_file_id TEXT NOT NULL UNIQUE,
                physical_file_id TEXT NOT NULL,
                summary_text TEXT NOT NULL,
                keywords_json TEXT NOT NULL,
                tags_json TEXT NOT NULL,
                category TEXT NOT NULL,
                summary_method TEXT NOT NULL,
                llm_provider TEXT NOT NULL,
                llm_model TEXT NOT NULL,
                knowledge_item_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(task_file_id) REFERENCES task_files(id) ON DELETE CASCADE,
                FOREIGN KEY(physical_file_id) REFERENCES physical_files(id)
            )
            """
        )
        connection.execute("CREATE INDEX IF NOT EXISTS idx_file_summaries_task_file_id ON file_summaries(task_file_id)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_file_summaries_physical_file_id ON file_summaries(physical_file_id)")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS file_summary_extras (
                file_summary_id TEXT PRIMARY KEY,
                table_understanding_json TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(file_summary_id) REFERENCES file_summaries(id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS document_chunks (
                id TEXT PRIMARY KEY,
                task_file_id TEXT NOT NULL,
                physical_file_id TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(task_file_id) REFERENCES task_files(id) ON DELETE CASCADE,
                FOREIGN KEY(physical_file_id) REFERENCES physical_files(id)
            )
            """
        )
        connection.execute("CREATE INDEX IF NOT EXISTS idx_document_chunks_task_file_id ON document_chunks(task_file_id)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_document_chunks_physical_file_id ON document_chunks(physical_file_id)")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS embedding_records (
                id TEXT PRIMARY KEY,
                chunk_id TEXT NOT NULL,
                embedding_provider TEXT NOT NULL,
                embedding_model TEXT NOT NULL,
                vector_store TEXT NOT NULL,
                vector_ref TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(chunk_id) REFERENCES document_chunks(id) ON DELETE CASCADE
            )
            """
        )
        connection.execute("CREATE INDEX IF NOT EXISTS idx_embedding_records_chunk_id ON embedding_records(chunk_id)")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS retrieval_settings (
                id TEXT PRIMARY KEY,
                retrieval_mode TEXT NOT NULL,
                chunk_size INTEGER NOT NULL,
                chunk_overlap INTEGER NOT NULL,
                top_k INTEGER NOT NULL,
                embedding_provider TEXT,
                embedding_model TEXT,
                vector_store TEXT,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS questions (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                question_text TEXT NOT NULL,
                question_type TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
            )
            """
        )
        connection.execute("CREATE INDEX IF NOT EXISTS idx_questions_task_id ON questions(task_id)")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS answers (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                agent_run_id TEXT,
                question_id TEXT NOT NULL,
                answer_text_markdown TEXT NOT NULL,
                selected_task_file_ids_json TEXT NOT NULL,
                source_refs_json TEXT NOT NULL,
                iteration_count INTEGER NOT NULL,
                llm_provider TEXT NOT NULL,
                llm_model TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                FOREIGN KEY(agent_run_id) REFERENCES agent_runs(id) ON DELETE SET NULL,
                FOREIGN KEY(question_id) REFERENCES questions(id) ON DELETE CASCADE
            )
            """
        )
        _ensure_column(connection, "answers", "agent_run_id", "TEXT")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_answers_task_id ON answers(task_id)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_answers_agent_run_id ON answers(agent_run_id)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_answers_question_id ON answers(question_id)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_answers_created_at ON answers(created_at)")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS excel_analysis_runs (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                agent_run_id TEXT,
                iteration_id TEXT,
                task_file_id TEXT NOT NULL,
                question_id TEXT NOT NULL,
                generated_code TEXT NOT NULL,
                final_code TEXT NOT NULL,
                code_status TEXT NOT NULL,
                execution_status TEXT NOT NULL,
                result_json TEXT,
                stdout TEXT,
                stderr TEXT,
                repair_attempts INTEGER NOT NULL DEFAULT 0,
                first_error TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                FOREIGN KEY(agent_run_id) REFERENCES agent_runs(id) ON DELETE SET NULL,
                FOREIGN KEY(iteration_id) REFERENCES agent_iterations(id) ON DELETE SET NULL,
                FOREIGN KEY(task_file_id) REFERENCES task_files(id) ON DELETE CASCADE,
                FOREIGN KEY(question_id) REFERENCES questions(id) ON DELETE CASCADE
            )
            """
        )
        _ensure_column(connection, "excel_analysis_runs", "agent_run_id", "TEXT")
        _ensure_column(connection, "excel_analysis_runs", "iteration_id", "TEXT")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_excel_analysis_runs_task_id ON excel_analysis_runs(task_id)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_excel_analysis_runs_agent_run_id ON excel_analysis_runs(agent_run_id)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_excel_analysis_runs_iteration_id ON excel_analysis_runs(iteration_id)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_excel_analysis_runs_task_file_id ON excel_analysis_runs(task_file_id)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_excel_analysis_runs_question_id ON excel_analysis_runs(question_id)")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_runs (
                id TEXT PRIMARY KEY,
                task_id TEXT,
                goal TEXT NOT NULL,
                status TEXT NOT NULL,
                max_iterations INTEGER NOT NULL DEFAULT 10,
                current_iteration INTEGER NOT NULL DEFAULT 0,
                final_answer_markdown TEXT,
                stop_reason TEXT,
                owner_user_id TEXT NOT NULL,
                department_id TEXT NOT NULL,
                security_level TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE SET NULL
            )
            """
        )
        connection.execute("CREATE INDEX IF NOT EXISTS idx_agent_runs_task_id ON agent_runs(task_id)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_agent_runs_status ON agent_runs(status)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_agent_runs_created_at ON agent_runs(created_at)")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_iterations (
                id TEXT PRIMARY KEY,
                agent_run_id TEXT NOT NULL,
                iteration_index INTEGER NOT NULL,
                plan_text TEXT,
                tool_name TEXT,
                tool_input_json TEXT,
                tool_result_json TEXT,
                reflection_text TEXT,
                decision TEXT NOT NULL,
                llm_call_log_id TEXT,
                status TEXT NOT NULL,
                error_message TEXT,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                FOREIGN KEY(agent_run_id) REFERENCES agent_runs(id) ON DELETE CASCADE,
                FOREIGN KEY(llm_call_log_id) REFERENCES llm_call_logs(id)
            )
            """
        )
        _ensure_column(connection, "agent_iterations", "tool_result_json", "TEXT")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_agent_iterations_agent_run_id ON agent_iterations(agent_run_id)")
        connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_agent_iterations_run_index ON agent_iterations(agent_run_id, iteration_index)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_agent_iterations_status ON agent_iterations(status)")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS observations (
                id TEXT PRIMARY KEY,
                agent_run_id TEXT NOT NULL,
                agent_iteration_id TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                observation_type TEXT NOT NULL,
                content_text TEXT,
                content_json TEXT,
                status TEXT NOT NULL,
                error_message TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(agent_run_id) REFERENCES agent_runs(id) ON DELETE CASCADE,
                FOREIGN KEY(agent_iteration_id) REFERENCES agent_iterations(id) ON DELETE CASCADE
            )
            """
        )
        connection.execute("CREATE INDEX IF NOT EXISTS idx_observations_agent_run_id ON observations(agent_run_id)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_observations_agent_iteration_id ON observations(agent_iteration_id)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_observations_tool_name ON observations(tool_name)")
