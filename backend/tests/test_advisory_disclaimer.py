from app.services.nodes.utils import strip_advisory_disclaimer


def test_english_disclaimer_sentence_is_stripped():
    reply = (
        "Die Bachelorarbeit umfasst 12 LP. "
        "Advisory; official FU documents and the examination office remain authoritative."
    )
    stripped, found = strip_advisory_disclaimer(reply)
    assert stripped == "Die Bachelorarbeit umfasst 12 LP."
    assert found


def test_prefixed_advisory_variant_is_stripped():
    reply = (
        "Der Prozess umfasst fünf Schritte. "
        "Advisory: Official FU documents and the examination office remain authoritative."
    )
    stripped, found = strip_advisory_disclaimer(reply)
    assert stripped == "Der Prozess umfasst fünf Schritte."
    assert found


def test_orphan_advisory_token_is_cleaned_up():
    reply = (
        "Die Anerkennung erfolgt nach Entscheidung. "
        "Official FU documents and the examination office remain authoritative. advisory"
    )
    stripped, found = strip_advisory_disclaimer(reply)
    assert stripped == "Die Anerkennung erfolgt nach Entscheidung."
    assert found


def test_german_model_variant_is_stripped():
    reply = (
        "Der Wahlbereich umfasst 10 LP. "
        "Die offiziellen FU-Dokumente und das Prüfungsbüro bleiben maßgeblich."
    )
    stripped, found = strip_advisory_disclaimer(reply)
    assert stripped == "Der Wahlbereich umfasst 10 LP."
    assert found


def test_reply_without_disclaimer_is_untouched():
    reply = "Die Bachelorarbeit umfasst 12 LP (RSPO §7)."
    stripped, found = strip_advisory_disclaimer(reply)
    assert stripped == reply
    assert not found
