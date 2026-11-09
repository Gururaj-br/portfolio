from pathlib import Path

import pytest
import yaml

from app.retriever import Retriever, tokenize

PROFILE = yaml.safe_load((Path(__file__).parent.parent / "data" / "profile.yaml").read_text(encoding="utf-8"))


def test_profile_has_required_sections():
    for key in ("person", "contact", "experience", "skills", "index", "suggested_questions"):
        assert key in PROFILE, key
    ids = [c["id"] for c in PROFILE["index"]]
    assert len(ids) == len(set(ids)), "index ids must be unique"


def test_tokenize_drops_stopwords_and_plurals():
    assert tokenize("What AI agents has he built?") == ["ai", "agent", "built"]


@pytest.mark.parametrize(
    "query, expected_id",
    [
        ("What AI agents has he built?", "tricon/agents"),
        ("RAG experience", "projects/rag-qa"),
        ("Has he led people?", "dataweave/mentoring"),
        ("Kafka and data pipelines", "dataweave/etl"),
    ],
)
def test_retrieval_ranks_expected_chunk_in_top3(query, expected_id):
    hits = Retriever(PROFILE["index"]).search(query)["hits"]
    assert expected_id in [h["id"] for h in hits]


def test_every_suggested_question_returns_hits():
    r = Retriever(PROFILE["index"])
    for q in PROFILE["suggested_questions"]:
        assert r.search(q)["hits"], q


def test_no_match_returns_empty():
    assert Retriever(PROFILE["index"]).search("banana smoothie")["hits"] == []


def test_api_endpoints():
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient

    from app.main import app

    c = TestClient(app)
    assert c.get("/healthz").json() == {"ok": True}
    assert "Gururaja" in c.get("/").text
    assert "index" not in c.get("/api/profile").json()
    assert c.get("/api/profile/index").status_code == 404
    assert c.get("/api/ask", params={"q": "agents"}).json()["hits"]
