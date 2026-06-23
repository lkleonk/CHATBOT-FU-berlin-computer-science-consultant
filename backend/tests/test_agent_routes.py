from app.services.nodes.scope_classifier import heuristic_classify
from app.services.routing import route_after_classifier


def test_route_after_classifier_plan_check():
    assert route_after_classifier({"message_type": "plan_check"}) == "plan_check"


def test_route_after_classifier_degree_question():
    assert route_after_classifier({"message_type": "degree_question"}) == "degree_question"


def test_route_after_classifier_course_offering_question():
    assert route_after_classifier({"message_type": "course_offering_question"}) == "course_offering_question"


def test_route_after_classifier_defaults_off_topic():
    assert route_after_classifier({"message_type": "unexpected"}) == "off_topic"


def test_heuristic_classifier_detects_degree_question():
    message_type = heuristic_classify("Wie viele LP brauche ich im Anwendungsbereich im Master Informatik?")

    assert message_type == "degree_question"


def test_heuristic_classifier_detects_english_degree_question():
    message_type = heuristic_classify("How many credits do I need for technical CS?")

    assert message_type == "degree_question"


def test_heuristic_classifier_detects_course_offering_question():
    message_type = heuristic_classify("Welche Softwareprojekte gibt es im SoSe 2026?")

    assert message_type == "course_offering_question"


def test_heuristic_classifier_detects_plan_check():
    message_type = heuristic_classify(
        "Bitte prüfe meinen Studienplan: Rechnersicherheit 10 LP, "
        "Softwareprojekt Praktische Informatik B 10 LP, Master Informatik."
    )

    assert message_type == "plan_check"
