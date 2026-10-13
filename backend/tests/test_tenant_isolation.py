import io
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.testclient import TestClient

from app.core.config import settings
from app.models.chat_history import ChatHistory
from app.models.legal_document import LegalDocument
from app.routes.ask import ask_question
from app.routes.documents import (
    create_document,
    get_document,
    get_documents,
    delete_document,
    upload_document,
)
from app.routes import ask, documents, history, metrics
from app.routes.history import get_chat_history
from app.schemas.document import DocumentCreate
from app.retrieval.semantic import semantic_search
from app.retrieval.search import search_documents


class FakeDatabase:
    def __init__(self):
        self.added = []
        self.queries = []
        self.committed = False
        self.rolled_back = False

    def add(self, value):
        self.added.append(value)

    def delete(self, value):
        self.deleted = value

    def flush(self):
        for value in self.added:
            if isinstance(value, LegalDocument):
                value.id = 12

    def commit(self):
        self.committed = True

    def refresh(self, _value):
        pass

    def rollback(self):
        self.rolled_back = True

    def query(self, _model):
        query = FakeQuery()
        self.queries.append(query)
        return query


class FakeQuery:
    def __init__(self):
        self.filters = []

    def filter(self, *predicates):
        self.filters.extend(predicates)
        return self

    def all(self):
        return []

    def first(self):
        return None

    def order_by(self, *_expressions):
        return self

    def limit(self, _limit):
        return self


def assert_user_filter(predicates, user_id):
    assert any(
        str(predicate).startswith("legal_documents.user_id =")
        and predicate.right.value == user_id
        for predicate in predicates
    )


def test_document_create_and_list_are_owner_scoped():
    user = SimpleNamespace(id=41)
    database = FakeDatabase()

    created = create_document(
        DocumentCreate(title="Owned", content="Private"),
        current_user=user,
        db=database,
    )
    assert created.user_id == user.id

    get_documents(current_user=user, db=database)
    assert_user_filter(database.queries[-1].filters, user.id)


def test_document_detail_rejects_documents_not_owned_by_request_user():
    user = SimpleNamespace(id=47)
    database = FakeDatabase()

    try:
        get_document(document_id=12, current_user=user, db=database)
    except HTTPException as error:
        assert error.status_code == 403
    else:
        raise AssertionError("Expected an ownership denial")

    predicates = database.queries[0].filters
    assert any(
        str(predicate).startswith("legal_documents.user_id =")
        and predicate.right.value == user.id
        for predicate in predicates
    )


def test_document_delete_rejects_non_owner():
    user = SimpleNamespace(id=48)
    database = FakeDatabase()

    try:
        delete_document(document_id=12, current_user=user, db=database)
    except HTTPException as error:
        assert error.status_code == 403
    else:
        raise AssertionError("Expected an ownership denial")

    assert_user_filter(database.queries[0].filters, user.id)
    assert not database.committed


def test_document_delete_removes_only_an_owned_document():
    user = SimpleNamespace(id=49)
    document = SimpleNamespace(id=12, user_id=user.id)
    database = FakeDatabase()
    query = OwnedDocumentQuery(database, document)
    database.query = lambda _model: query
    database.queries.append(query)

    delete_document(document_id=document.id, current_user=user, db=database)

    assert database.deleted is document
    assert database.committed
    assert any(
        str(predicate).startswith("legal_documents.user_id =")
        and predicate.right.value == user.id
        for predicate in database.queries[0].filters
    )


class OwnedDocumentQuery(FakeQuery):
    def __init__(self, database, document):
        super().__init__()
        self.database = database
        self.document = document

    def first(self):
        return self.document


def test_history_query_is_owner_scoped():
    user = SimpleNamespace(id=45)
    database = FakeDatabase()

    get_chat_history(current_user=user, limit=50, db=database)

    predicate = database.queries[0].filters[0]
    assert str(predicate).startswith("chat_history.user_id =")
    assert predicate.right.value == user.id


def test_pdf_upload_attaches_authenticated_user_id():
    user = SimpleNamespace(id=42)
    database = FakeDatabase()
    upload = UploadFile(
        filename="owned.pdf",
        file=io.BytesIO(b"%PDF-1.4"),
    )
    reader = SimpleNamespace(is_encrypted=False, pages=[])

    with (
        patch("app.routes.documents.PdfReader", return_value=reader),
        patch(
            "app.routes.documents.split_pages",
            return_value=[
                {
                    "content": "Some private legal text.",
                    "page_number": 1,
                    "chapter": None,
                    "section": None,
                    "section_title": None,
                }
            ],
        ),
        patch(
            "app.routes.documents.generate_embedding",
            return_value=[0.1] * 384,
        ),
    ):
        uploaded = upload_document(
            file=upload,
            current_user=user,
            db=database,
        )

    assert uploaded.user_id == user.id
    chunks = [
        value for value in database.added
        if hasattr(value, "document_id")
    ]
    assert len(chunks) == 1
    assert chunks[0].user_id == user.id
    assert database.committed


def test_retrieval_query_is_filtered_before_semantic_search():
    user_id = 43
    database = FakeDatabase()
    chunk = SimpleNamespace(
        id=5,
        document_id=1,
        content=(
            "Legal rights and obligations apply under this act. "
            "The rules describe remedies for people affected by law."
        ),
        section=None,
        metadata_json={},
        document=SimpleNamespace(title="Legal Act"),
    )
    database.query = lambda *_args: RecordingRetrievalQuery(database, [chunk])
    semantic_users = []

    with (
        patch(
            "app.retrieval.search.semantic_search",
            side_effect=lambda _query, _db, user_id, candidate_ids: (
                semantic_users.append(user_id) or {5: 0.9}
            ),
        ),
        patch(
            "app.retrieval.search.keyword_search",
            return_value={5: 0.9},
        ),
    ):
        results = search_documents("legal rules", database, user_id=user_id)

    assert results[0][0].id == chunk.id
    assert semantic_users == [user_id]
    assert_user_filter(database.retrieval_filters, user_id)


def test_vector_search_applies_owner_filter_to_database_query():
    user_id = 46
    chunk = SimpleNamespace(id=8)
    filters = []

    class RecordingVectorQuery:
        def join(self, *_args, **_kwargs):
            return self

        def filter(self, *predicates):
            filters.extend(predicates)
            return self

        def all(self):
            return [(chunk, 0.2)]

    database = SimpleNamespace(
        query=lambda *_args: RecordingVectorQuery()
    )
    with patch(
        "app.retrieval.semantic.generate_embedding",
        return_value=[0.1] * 384,
    ):
        scores = semantic_search(
            "legal rules",
            database,
            user_id=user_id,
            candidate_ids=[chunk.id],
        )

    assert scores == {chunk.id: 0.8}
    assert_user_filter(filters, user_id)


class RecordingRetrievalQuery:
    def __init__(self, database, chunks):
        self.database = database
        self.chunks = chunks

    def join(self, *_args, **_kwargs):
        return self

    def filter(self, *predicates):
        self.database.retrieval_filters = getattr(
            self.database,
            "retrieval_filters",
            [],
        ) + list(predicates)
        return self

    def options(self, *_args, **_kwargs):
        return self

    def all(self):
        return self.chunks


def test_ask_persists_chat_under_the_authenticated_user():
    user = SimpleNamespace(id=44)
    database = FakeDatabase()

    with patch(
        "app.routes.ask.rag_pipeline",
        return_value={"answer": "Private response", "citations": []},
    ) as pipeline:
        result = ask_question(
            question="Private question",
            current_user=user,
            db=database,
        )

    pipeline.assert_called_once()
    assert pipeline.call_args.kwargs["user_id"] == user.id
    history = next(
        value for value in database.added
        if isinstance(value, ChatHistory)
    )
    assert history.user_id == user.id
    assert history.question == "Private question"
    assert result["answer"] == "Private response"
    assert database.committed


def test_tenant_routes_reject_requests_without_user_identity():
    app = FastAPI()
    app.include_router(documents.router)
    app.include_router(ask.router)
    app.include_router(metrics.router)
    app.include_router(history.router)
    client = TestClient(app)

    with patch.object(settings, "AUTH_MODE", "disabled"):
        responses = [
            client.get("/documents"),
            client.post("/ask/?question=private"),
            client.get("/metrics/"),
            client.get("/history/"),
        ]

    assert [response.status_code for response in responses] == [401] * 4
