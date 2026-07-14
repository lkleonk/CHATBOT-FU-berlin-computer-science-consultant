from app.domain.degrees.bsc_informatik.program_rules import (
    COMPULSORY_ELECTIVE_MODULES,
    CORE_MODULES,
    get_program_rules,
)


def _section(section_id: str):
    return next(section for section in get_program_rules().sections if section.id == section_id)


def test_bsc_compulsory_modules_total_116_lp():
    assert sum(lp for _, lp in CORE_MODULES) == 116
    assert len(_section("compulsory-modules").items) == 16


def test_bsc_compulsory_elective_catalogue_has_exact_legal_name_and_size():
    assert len(COMPULSORY_ELECTIVE_MODULES) == 13
    assert "Aktuelle Themen in der Informatik" in COMPULSORY_ELECTIVE_MODULES
    assert "Aktuelle Forschungsthemen in der Informatik" not in COMPULSORY_ELECTIVE_MODULES


def test_bsc_abv_and_thesis_rules_include_key_constraints():
    abv_text = " ".join(item.text for item in _section("abv").items)
    thesis_text = " ".join(item.text for item in _section("bachelorarbeit").items)

    assert "5, 10, 15, or 20 LP" in abv_text
    assert "not the only valid internship route" in abv_text
    assert "90 successfully completed LP" in thesis_text
    assert "passed or formally recognised" in thesis_text
