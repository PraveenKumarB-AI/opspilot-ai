from opspilot.retriever import get_retriever, load_chunks


def test_chunks_have_citation_ids():
    chunks = load_chunks()
    assert len(chunks) > 30
    assert all(c.chunk_id.startswith("KB-") and " §" in c.chunk_id for c in chunks)


def test_search_finds_the_right_document():
    r = get_retriever()
    cases = {
        "depreciation run failed with method missing": "KB-01",
        "export a report to excel": "KB-02",
        "ERP sync log shows inactive account code": "KB-07",
        "no matching retirement unit when I unitize": "KB-05",
    }
    for query, doc in cases.items():
        assert doc in [h["doc_id"] for h in r.search(query)[:3]], query


def test_unrelated_question_has_weak_evidence():
    r = get_retriever()
    assert r.search("what is the capital of France")[0]["score"] < r.min_evidence
