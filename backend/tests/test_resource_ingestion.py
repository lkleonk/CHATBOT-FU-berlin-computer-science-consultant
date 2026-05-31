from app.services.resource_loader import chunk_text, content_hash, load_text_resource, normalize_text


def test_normalize_text_collapses_blank_lines_and_spaces():
    assert normalize_text("A  B\r\n\r\n\r\nC") == "A B\n\nC"


def test_chunk_text_uses_semantic_heading():
    chunks = chunk_text("Randbedingungen\nA rule paragraph.\n\nAnother paragraph.", default_heading="Doc")

    assert len(chunks) == 1
    assert chunks[0].section_heading == "Randbedingungen"
    assert "A rule paragraph" in chunks[0].content


def test_load_text_resource(tmp_path):
    path = tmp_path / "rules.txt"
    path.write_text("Title Line\n\nRandbedingungen\nRule body", encoding="utf-8")

    title, chunks = load_text_resource(path)

    assert title == "Title Line"
    assert chunks
    assert content_hash(chunks[0].content).startswith("sha256:")
