"""Document model operations for WaltConsultant."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from database.connection import DatabaseManager, get_db_manager
from utils.audit import AUDIT_LOGGER


class DocumentModel:
    def __init__(self, db_manager: DatabaseManager | None = None) -> None:
        self.db = db_manager or get_db_manager()

    def _next_document_id(self, connection) -> str:
        row = connection.execute(
            """
            SELECT COALESCE(MAX(CAST(SUBSTR(document_id, 10) AS INTEGER)), 0) AS seq
            FROM documents
            WHERE document_id LIKE 'WALT-DOC-%'
            """
        ).fetchone()
        seq = (row[0] if row else 0) + 1
        return f"WALT-DOC-{seq:05d}"

    def upload_document(
        self,
        reference_type: str,
        reference_id: int,
        document_name: str,
        document_type: str,
        file_path: str,
        uploaded_by: int | None,
    ) -> int:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError("Selected document does not exist.")

        file_bytes = path.read_bytes()
        with self.db.transaction() as connection:
            document_id = self._next_document_id(connection)
            cursor = connection.execute(
                """
                INSERT INTO documents (
                    document_id,
                    reference_type,
                    reference_id,
                    document_name,
                    document_type,
                    file_data,
                    file_name,
                    file_size,
                    uploaded_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document_id,
                    reference_type,
                    reference_id,
                    document_name,
                    document_type,
                    file_bytes,
                    path.name,
                    len(file_bytes),
                    uploaded_by,
                ),
            )
            row_id = int(cursor.lastrowid)

        AUDIT_LOGGER.log_action(uploaded_by, "INSERT", "documents", row_id, None, {"document_name": document_name, "reference_type": reference_type, "reference_id": reference_id})
        return row_id

    def list_documents(self, reference_type: str = "", document_type: str = "") -> list[dict[str, Any]]:
        params: list[Any] = []
        conditions = ["1=1"]

        if reference_type:
            conditions.append("reference_type = ?")
            params.append(reference_type)

        if document_type:
            conditions.append("document_type = ?")
            params.append(document_type)

        query = f"""
            SELECT id, document_id, reference_type, reference_id, document_name,
                   document_type, file_name, file_size, uploaded_at
            FROM documents
            WHERE {' AND '.join(conditions)}
            ORDER BY uploaded_at DESC
        """
        rows = self.db.fetchall(query, tuple(params))
        return [dict(row) for row in rows]

    def get_document(self, document_id: int) -> dict[str, Any] | None:
        row = self.db.fetchone("SELECT * FROM documents WHERE id = ?", (document_id,))
        return dict(row) if row else None

    def delete_document(self, document_id: int, actor_user_id: int | None) -> None:
        old_data = self.get_document(document_id)
        if not old_data:
            raise ValueError("Document not found.")

        self.db.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        AUDIT_LOGGER.log_action(actor_user_id, "DELETE", "documents", document_id, old_data, None)


DOCUMENT_MODEL = DocumentModel()
