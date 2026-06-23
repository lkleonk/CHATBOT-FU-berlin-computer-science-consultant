from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.services.nodes.answer_composer import answer_composer_node
from app.services.nodes.course_key_selector import course_key_selector_node
from app.services.nodes.course_lookup import course_lookup_node
from app.services.nodes.offtopic import offtopic_node
from app.services.nodes.rule_checker import rule_checker_node
from app.services.nodes.scope_classifier import scope_classifier_node
from app.services.nodes.study_plan_parser import study_plan_parser_node
from app.services.routing import route_after_classifier
from app.services.states.consultant_state import ConsultantState
from app.services.wizardflow_service import initialize_wizardflow


workflow = StateGraph(ConsultantState)

workflow.add_node("scope_classifier", scope_classifier_node)
workflow.add_node("course_key_selector", course_key_selector_node)
workflow.add_node("course_lookup", course_lookup_node)
workflow.add_node("study_plan_parser", study_plan_parser_node)
workflow.add_node("rule_checker", rule_checker_node)
workflow.add_node("answer_composer", answer_composer_node)
workflow.add_node("offtopic", offtopic_node)

workflow.add_edge(START, "scope_classifier")
workflow.add_conditional_edges(
    "scope_classifier",
    route_after_classifier,
    {
        "off_topic": "offtopic",
        "degree_question": "answer_composer",
        "course_offering_question": "course_key_selector",
        "plan_check": "study_plan_parser",
    },
)

workflow.add_edge("course_key_selector", "course_lookup")
workflow.add_edge("course_lookup", "answer_composer")
workflow.add_edge("study_plan_parser", "rule_checker")
workflow.add_edge("rule_checker", "answer_composer")
workflow.add_edge("answer_composer", END)
workflow.add_edge("offtopic", END)

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)
initialize_wizardflow(app)
