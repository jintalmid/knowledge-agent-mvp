import asyncio
import zipfile
from io import BytesIO

import pytest
from fastapi import HTTPException, UploadFile

from app.core.auth import CurrentUser
from app.core.config import get_settings
from app.db.sqlite import db_session, init_db
from app.schemas.task import TaskCreate
from app.services import files as file_service
from app.services import parsing as parsing_service
from app.services import tasks as task_service


@pytest.fixture()
def workspace(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "test.sqlite3"))
    monkeypatch.setenv("UPLOADS_DIR", str(tmp_path / "uploads"))
    get_settings.cache_clear()
    init_db()
    yield tmp_path
    get_settings.cache_clear()


def _upload(filename: str, content: bytes, content_type: str = "text/plain") -> UploadFile:
    return UploadFile(file=BytesIO(content), filename=filename, headers={"content-type": content_type})


def _create_task(connection) -> str:
    task = task_service.create_task(
        connection,
        TaskCreate(name="auto parse test", description=""),
        CurrentUser(),
    )
    return task.id


def _minimal_docx(text: str) -> bytes:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "[Content_Types].xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>""",
        )
        archive.writestr(
            "_rels/.rels",
            """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>""",
        )
        archive.writestr(
            "word/document.xml",
            f"""<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>{text}</w:t></w:r></w:p>
  </w:body>
</w:document>""",
        )
    return buffer.getvalue()


def test_upload_success_auto_parse_success(workspace):
    with db_session() as connection:
        task_id = _create_task(connection)
        task_file = asyncio.run(
            file_service.create_task_file(
                connection,
                task_id,
                _upload("notes.txt", "hello auto parse".encode("utf-8")),
                CurrentUser(),
            )
        )

        assert task_file.parse_status == "parsed"
        assert task_file.parse_error is None

        parsed = parsing_service.get_parsed_content(connection, task_file.id)
        assert parsed is not None
        assert parsed.content_type == "text"
        assert parsed.text_content == "hello auto parse"


def test_upload_docx_auto_parses_as_text(workspace):
    with db_session() as connection:
        task_id = _create_task(connection)
        task_file = asyncio.run(
            file_service.create_task_file(
                connection,
                task_id,
                _upload(
                    "brief.docx",
                    _minimal_docx("DOCX auto parse works"),
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                ),
                CurrentUser(),
            )
        )

        parsed = parsing_service.get_parsed_content(connection, task_file.id)

        assert task_file.parse_status == "parsed"
        assert task_file.parse_error is None
        assert task_file.file_ext == "docx"
        assert parsed is not None
        assert parsed.content_type == "text"
        assert parsed.text_content == "DOCX auto parse works"


def test_upload_success_parse_failure_keeps_file(workspace, monkeypatch):
    def fail_parse(connection, task_file_id):
        raise HTTPException(status_code=400, detail="simulated parse failure")

    monkeypatch.setattr(file_service.parsing_service, "parse_task_file", fail_parse)

    with db_session() as connection:
        task_id = _create_task(connection)
        task_file = asyncio.run(
            file_service.create_task_file(
                connection,
                task_id,
                _upload("notes.txt", "kept even if parse fails".encode("utf-8")),
                CurrentUser(),
            )
        )

        assert task_file.parse_status == "failed"
        assert task_file.parse_error == "simulated parse failure"
        assert file_service.get_task_file(connection, task_file.id) is not None
        assert file_service.get_physical_file(connection, task_file.physical_file_id) is not None
        assert parsing_service.get_parsed_content(connection, task_file.id) is None


def test_upload_failure_does_not_trigger_parse(workspace, monkeypatch):
    calls = {"count": 0}

    def count_parse(connection, task_file_id):
        calls["count"] += 1

    monkeypatch.setattr(file_service.parsing_service, "parse_task_file", count_parse)

    with db_session() as connection:
        task_id = _create_task(connection)
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(
                file_service.create_task_file(
                    connection,
                    task_id,
                    _upload("blocked.exe", b"not allowed", "application/octet-stream"),
                    CurrentUser(),
                )
            )

        assert exc_info.value.status_code == 400
        assert calls["count"] == 0


def test_manual_retry_parse_still_works_after_auto_parse_failure(workspace, monkeypatch):
    def fail_parse(connection, task_file_id):
        raise HTTPException(status_code=400, detail="first parse failed")

    with db_session() as connection:
        task_id = _create_task(connection)
        with monkeypatch.context() as patch_context:
            patch_context.setattr(file_service.parsing_service, "parse_task_file", fail_parse)
            task_file = asyncio.run(
                file_service.create_task_file(
                    connection,
                    task_id,
                    _upload("retry.md", "# Retry works".encode("utf-8")),
                    CurrentUser(),
                )
            )

        assert task_file.parse_status == "failed"

        parsed = parsing_service.parse_task_file(connection, task_file.id)
        refreshed = file_service.get_task_file(connection, task_file.id)

        assert parsed.content_type == "text"
        assert parsed.text_content == "# Retry works"
        assert refreshed is not None
        assert refreshed.parse_status == "parsed"
        assert refreshed.parse_error is None


def test_same_task_duplicate_upload_returns_existing_reference(workspace, monkeypatch):
    calls = {"count": 0}
    original_parse = file_service.parsing_service.parse_task_file

    def count_parse(connection, task_file_id):
        calls["count"] += 1
        return original_parse(connection, task_file_id)

    monkeypatch.setattr(file_service.parsing_service, "parse_task_file", count_parse)

    with db_session() as connection:
        task_id = _create_task(connection)
        first_task_file = asyncio.run(
            file_service.create_task_file(
                connection,
                task_id,
                _upload("duplicate-a.txt", b"same content"),
                CurrentUser(),
            )
        )
        second_task_file = asyncio.run(
            file_service.create_task_file(
                connection,
                task_id,
                _upload("duplicate-b.txt", b"same content"),
                CurrentUser(),
            )
        )

        task_files = file_service.list_task_files(connection, task_id)
        physical_file = file_service.get_physical_file(connection, first_task_file.physical_file_id)

        assert second_task_file.id == first_task_file.id
        assert task_files is not None
        assert len(task_files) == 1
        assert physical_file is not None
        assert physical_file.ref_count == 1
        assert calls["count"] == 1


def test_same_physical_file_can_be_referenced_by_different_tasks(workspace):
    with db_session() as connection:
        first_task_id = _create_task(connection)
        second_task_id = task_service.create_task(
            connection,
            TaskCreate(name="second task", description=""),
            CurrentUser(),
        ).id

        first_task_file = asyncio.run(
            file_service.create_task_file(
                connection,
                first_task_id,
                _upload("shared-a.txt", b"shared content"),
                CurrentUser(),
            )
        )
        second_task_file = asyncio.run(
            file_service.create_task_file(
                connection,
                second_task_id,
                _upload("shared-b.txt", b"shared content"),
                CurrentUser(),
            )
        )

        physical_file = file_service.get_physical_file(connection, first_task_file.physical_file_id)

        assert second_task_file.id != first_task_file.id
        assert second_task_file.physical_file_id == first_task_file.physical_file_id
        assert physical_file is not None
        assert physical_file.ref_count == 2
