import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("LLM_PROVIDER", "local_ollama")

# Settings are read once when app.settings is imported, so tracing must be
# disabled before any test imports application code. Otherwise tests that
# create sessions import agent_graph_service, whose module-level
# initialize_wizardflow() writes real trace files into backend/traces/.
# Tests exercising tracing build their own tracer against a tmp dir and
# monkeypatch wizardflow_service.tracer directly.
os.environ["WIZARDFLOW_ENABLED"] = "false"
