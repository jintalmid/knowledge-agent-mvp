from datetime import UTC, datetime

from app.core.auth import CurrentUser
from app.core.config import get_settings
from app.db.sqlite import db_session, init_db
from app.schemas.task import TaskCreate
from app.services import agent_runner as agent_runner_service
from app.services import tasks as task_service


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def test_get_agent_run_includes_saved_agent_answer_id(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "test.sqlite3"))
    monkeypatch.setenv("UPLOADS_DIR", str(tmp_path / "uploads"))
    get_settings.cache_clear()
    init_db()

    with db_session() as connection:
        task = task_service.create_task(connection, TaskCreate(name="agent", description=""), CurrentUser())
        now = _now_iso()
        run_id = "arun_test"
        question_id = "q_test"
        answer_id = "ans_test"

        connection.execute(
            """
            INSERT INTO questions (id, task_id, question_text, question_type, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (question_id, task.id, "question", "agent_run", now),
        )
        connection.execute(
            """
            INSERT INTO agent_runs (
                id,
                task_id,
                goal,
                status,
                max_iterations,
                current_iteration,
                final_answer_markdown,
                stop_reason,
                owner_user_id,
                department_id,
                security_level,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                task.id,
                "question",
                "completed",
                3,
                1,
                "answer",
                "reflection_stop",
                task.owner_user_id,
                task.department_id,
                task.security_level,
                now,
                now,
            ),
        )
        connection.execute(
            """
            INSERT INTO answers (
                id,
                task_id,
                agent_run_id,
                question_id,
                answer_text_markdown,
                selected_task_file_ids_json,
                source_refs_json,
                iteration_count,
                llm_provider,
                llm_model,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (answer_id, task.id, run_id, question_id, "answer", "[]", "[]", 1, "test_provider", "test_model", now),
        )

        agent_run = agent_runner_service.get_agent_run(connection, run_id)

    get_settings.cache_clear()

    assert agent_run is not None
    assert agent_run.answer_id == answer_id


def test_final_prompt_requires_visible_iteration_and_observation_labels():
    _, user_prompt = agent_runner_service._build_final_prompt(
        "question",
        [
            {
                "iteration_label": "Iteration 1",
                "observation_label": "Observation 1.1",
                "tool_result": {
                    "status": "success",
                    "output": {
                        "agent_run_id": "arun_test",
                        "iteration_id": "aiter_hidden",
                        "observation": "evidence",
                    },
                },
            }
        ],
    )

    assert "Iteration 1" in user_prompt
    assert "Observation 1.1" in user_prompt
    assert "Do not cite internal database ids" in user_prompt
    assert "aiter_hidden" not in user_prompt
    assert "arun_test" not in user_prompt
