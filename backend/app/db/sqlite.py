import sqlite3
import json
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime

from app.core.config import get_settings

MODEL_SCENARIO_DEFINITIONS = [
    {"scenario": "default_text", "required_tags": ["text"], "is_required": True, "fallback_scenario": None},
    {"scenario": "file_summary", "required_tags": ["text"], "is_required": False, "fallback_scenario": "default_text"},
    {"scenario": "agent_planning", "required_tags": ["text", "reasoning"], "is_required": False, "fallback_scenario": "default_text"},
    {"scenario": "agent_reflection", "required_tags": ["text", "reasoning"], "is_required": False, "fallback_scenario": "default_text"},
    {"scenario": "final_answer", "required_tags": ["text"], "is_required": False, "fallback_scenario": "default_text"},
    {"scenario": "text_tool", "required_tags": ["text"], "is_required": False, "fallback_scenario": "default_text"},
    {"scenario": "excel_code_generation", "required_tags": ["text", "code"], "is_required": False, "fallback_scenario": "default_text"},
    {"scenario": "excel_code_repair", "required_tags": ["text", "code"], "is_required": False, "fallback_scenario": "default_text"},
    {"scenario": "excel_result_explanation", "required_tags": ["text"], "is_required": False, "fallback_scenario": "default_text"},
    {"scenario": "document_parse_vision", "required_tags": ["vision"], "is_required": False, "fallback_scenario": None},
    {"scenario": "embedding_generation", "required_tags": ["embedding"], "is_required": False, "fallback_scenario": None},
    {"scenario": "retrieval_rerank", "required_tags": ["rerank"], "is_required": False, "fallback_scenario": None},
    {"scenario": "ppt_parse", "required_tags": ["vision", "document_parse"], "is_required": False, "fallback_scenario": None},
    {"scenario": "pdf_image_parse", "required_tags": ["vision", "document_parse"], "is_required": False, "fallback_scenario": None},
    {"scenario": "ocr", "required_tags": ["ocr"], "is_required": False, "fallback_scenario": None},
]


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(get_settings().sqlite_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _ensure_column(connection: sqlite3.Connection, table_name: str, column_name: str, column_definition: str) -> None:
    columns = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    if column_name not in {column["name"] for column in columns}:
        connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")


def _deduplicate_task_file_references(connection: sqlite3.Connection) -> None:
    rows = connection.execute(
        """
        SELECT id, task_id, physical_file_id
        FROM task_files
        ORDER BY task_id ASC, physical_file_id ASC, created_at ASC, id ASC
        """
    ).fetchall()

    seen: set[tuple[str, str]] = set()
    duplicate_ids: list[str] = []

    for row in rows:
        key = (row["task_id"], row["physical_file_id"])
        if key in seen:
            duplicate_ids.append(row["id"])
        else:
            seen.add(key)

    if duplicate_ids:
        connection.executemany(
            "DELETE FROM task_files WHERE id = ?",
            [(task_file_id,) for task_file_id in duplicate_ids],
        )

    connection.execute(
        """
        UPDATE physical_files
        SET ref_count = (
            SELECT COUNT(*)
            FROM task_files
            WHERE task_files.physical_file_id = physical_files.id
        )
        """
    )


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _seed_model_scenarios(connection: sqlite3.Connection) -> None:
    now = _now_iso()
    for definition in MODEL_SCENARIO_DEFINITIONS:
        connection.execute(
            """
            INSERT INTO model_route_configs (
                id,
                scenario,
                model_id,
                required_tags_json,
                is_required,
                fallback_scenario,
                enabled,
                created_at,
                updated_at
            )
            VALUES (?, ?, NULL, ?, ?, ?, 1, ?, ?)
            ON CONFLICT(scenario) DO NOTHING
            """,
            (
                f"route_{definition['scenario']}",
                definition["scenario"],
                json.dumps(definition["required_tags"], ensure_ascii=False),
                1 if definition["is_required"] else 0,
                definition["fallback_scenario"],
                now,
                now,
            ),
        )


def _seed_default_model_from_env(connection: sqlite3.Connection) -> None:
    settings = get_settings()
    provider_type = (settings.llm_provider_type or "").replace("-", "_")
    if provider_type != "openai_compatible" or not settings.llm_base_url or not settings.llm_model:
        return

    now = _now_iso()
    provider_id = "provider_env_default"
    model_id = "model_env_default_text"
    connection.execute(
        """
        INSERT INTO model_providers (
            id,
            name,
            provider_type,
            base_url,
            api_key_env_name,
            api_key,
            enabled,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, NULL, 1, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            provider_type = excluded.provider_type,
            base_url = excluded.base_url,
            api_key_env_name = excluded.api_key_env_name,
            updated_at = excluded.updated_at
        """,
        (
            provider_id,
            "Default .env OpenAI-compatible provider",
            provider_type,
            settings.llm_base_url,
            "LLM_API_KEY",
            now,
            now,
        ),
    )
    connection.execute(
        """
        INSERT INTO model_configs (
            id,
            provider_id,
            display_name,
            model_name,
            model_types_json,
            capability_tags_json,
            context_window,
            output_window,
            enabled,
            is_default_text_model,
            last_test_status,
            last_test_message,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, 1, 1, NULL, NULL, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            provider_id = excluded.provider_id,
            model_name = excluded.model_name,
            enabled = 1,
            is_default_text_model = 1,
            updated_at = excluded.updated_at
        """,
        (
            model_id,
            provider_id,
            f"{settings.llm_model} (.env default)",
            settings.llm_model,
            json.dumps(["text"], ensure_ascii=False),
            json.dumps(["text", "reasoning", "code"], ensure_ascii=False),
            now,
            now,
        ),
    )
    connection.execute(
        """
        UPDATE model_route_configs
        SET model_id = COALESCE(model_id, ?),
            updated_at = ?
        WHERE scenario = 'default_text'
        """,
        (model_id, now),
    )


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
                parse_error TEXT,
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
        _ensure_column(connection, "task_files", "parse_error", "TEXT")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_task_files_task_id ON task_files(task_id)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_task_files_physical_file_id ON task_files(physical_file_id)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_physical_files_content_hash ON physical_files(content_hash)")
        _deduplicate_task_file_references(connection)
        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_task_files_unique_task_physical_file
            ON task_files(task_id, physical_file_id)
            """
        )
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
            CREATE TABLE IF NOT EXISTS model_providers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                provider_type TEXT NOT NULL,
                base_url TEXT NOT NULL,
                api_key_env_name TEXT,
                api_key TEXT,
                enabled INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute("CREATE INDEX IF NOT EXISTS idx_model_providers_provider_type ON model_providers(provider_type)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_model_providers_enabled ON model_providers(enabled)")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS model_configs (
                id TEXT PRIMARY KEY,
                provider_id TEXT NOT NULL,
                display_name TEXT NOT NULL,
                model_name TEXT NOT NULL,
                model_types_json TEXT NOT NULL,
                capability_tags_json TEXT NOT NULL,
                context_window INTEGER,
                output_window INTEGER,
                enabled INTEGER NOT NULL DEFAULT 1,
                is_default_text_model INTEGER NOT NULL DEFAULT 0,
                last_test_status TEXT,
                last_test_message TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(provider_id) REFERENCES model_providers(id) ON DELETE CASCADE
            )
            """
        )
        _ensure_column(connection, "model_configs", "output_window", "INTEGER")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_model_configs_provider_id ON model_configs(provider_id)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_model_configs_enabled ON model_configs(enabled)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_model_configs_default_text ON model_configs(is_default_text_model)")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS model_route_configs (
                id TEXT PRIMARY KEY,
                scenario TEXT NOT NULL UNIQUE,
                model_id TEXT,
                required_tags_json TEXT NOT NULL,
                is_required INTEGER NOT NULL DEFAULT 0,
                fallback_scenario TEXT,
                enabled INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(model_id) REFERENCES model_configs(id) ON DELETE SET NULL
            )
            """
        )
        connection.execute("CREATE INDEX IF NOT EXISTS idx_model_route_configs_scenario ON model_route_configs(scenario)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_model_route_configs_model_id ON model_route_configs(model_id)")
        _seed_model_scenarios(connection)
        _seed_default_model_from_env(connection)
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS llm_call_logs (
                id TEXT PRIMARY KEY,
                task_id TEXT,
                agent_run_id TEXT,
                iteration_id TEXT,
                scenario TEXT,
                provider_id TEXT,
                model_id TEXT,
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
        _ensure_column(connection, "llm_call_logs", "scenario", "TEXT")
        _ensure_column(connection, "llm_call_logs", "provider_id", "TEXT")
        _ensure_column(connection, "llm_call_logs", "model_id", "TEXT")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_llm_call_logs_task_id ON llm_call_logs(task_id)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_llm_call_logs_agent_run_id ON llm_call_logs(agent_run_id)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_llm_call_logs_iteration_id ON llm_call_logs(iteration_id)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_llm_call_logs_scenario ON llm_call_logs(scenario)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_llm_call_logs_provider_id ON llm_call_logs(provider_id)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_llm_call_logs_model_id ON llm_call_logs(model_id)")
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
