from app.services.nodes.scope_classifier import heuristic_classify
from app.services.routing import route_after_classifier


def test_route_after_classifier_plan_check():
    assert route_after_classifier({"message_type": "plan_check"}) == "plan_check"


def test_route_after_classifier_defaults_off_topic():
    assert route_after_classifier({"message_type": "unexpected"}) == "off_topic"


def test_heuristic_classifier_detects_study_question():
    message_type = heuristic_classify("Wie viele LP brauche ich im Anwendungsbereich im Master Informatik?")

    assert message_type == "study_question"


def test_heuristic_classifier_detects_plan_check():
    message_type = heuristic_classify(
        "Bitte prüfe meinen Studienplan: Rechnersicherheit 10 LP, "
        "Softwareprojekt Praktische Informatik B 10 LP, Master Informatik."
    )

    assert message_type == "plan_check"
