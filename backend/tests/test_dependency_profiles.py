import re
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
LEGACY_ONLY_DEPENDENCIES = {
    "huggingface-hub",
    "numpy",
    "pillow",
    "qdrant-client",
    "safetensors",
    "scikit-learn",
    "scipy",
    "sentence-transformers",
    "tokenizers",
    "torch",
    "tqdm",
    "transformers",
}


def _declared_dependency_names(path: Path) -> set[str]:
    names: set[str] = set()
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("#", "-")):
            continue
        name = re.split(r"[<>=!~;\[]", line, maxsplit=1)[0]
        names.add(name.strip().lower().replace("_", "-"))
    return names


def test_default_runtime_excludes_legacy_rag_dependencies():
    runtime_dependencies = _declared_dependency_names(BACKEND_ROOT / "requirements.txt")

    assert runtime_dependencies.isdisjoint(LEGACY_ONLY_DEPENDENCIES)


def test_legacy_rag_profile_contains_embedding_dependencies_and_runtime_base():
    legacy_path = BACKEND_ROOT / "requirements-legacy-rag.txt"
    legacy_text = legacy_path.read_text(encoding="utf-8")
    legacy_dependencies = _declared_dependency_names(legacy_path)

    assert "-r requirements.txt" in legacy_text.splitlines()
    assert LEGACY_ONLY_DEPENDENCIES <= legacy_dependencies
