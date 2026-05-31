import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


APP_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = APP_ROOT.parent
PROJECT_ROOT = BACKEND_ROOT.parent if (BACKEND_ROOT.parent / "ressources").exists() else BACKEND_ROOT

load_dotenv(PROJECT_ROOT / ".env.local")
load_dotenv(PROJECT_ROOT / ".env")


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(value, 0)


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class ScopeClassifierConfig:
    history_turns: int = 1


@dataclass(frozen=True)
class CourseKeySelectorConfig:
    history_turns: int = 2
    max_keys: int = 20
    include_available_semesters_note: bool = True


@dataclass(frozen=True)
class AnswerComposerConfig:
    history_turns: int = 4


@dataclass(frozen=True)
class AgentFlowConfig:
    scope_classifier: ScopeClassifierConfig
    course_key_selector: CourseKeySelectorConfig
    answer_composer: AnswerComposerConfig


agent_flow_config = AgentFlowConfig(
    scope_classifier=ScopeClassifierConfig(
        history_turns=_env_int("AGENT_SCOPE_CLASSIFIER_HISTORY_TURNS", 1),
    ),
    course_key_selector=CourseKeySelectorConfig(
        history_turns=_env_int("AGENT_COURSE_SELECTOR_HISTORY_TURNS", 2),
        max_keys=_env_int("AGENT_COURSE_SELECTOR_MAX_KEYS", 20),
        include_available_semesters_note=_env_bool(
            "AGENT_COURSE_SELECTOR_INCLUDE_SEMESTERS_NOTE",
            True,
        ),
    ),
    answer_composer=AnswerComposerConfig(
        history_turns=_env_int("AGENT_ANSWER_COMPOSER_HISTORY_TURNS", 4),
    ),
)
