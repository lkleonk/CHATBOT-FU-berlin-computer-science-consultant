import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel


APP_ROOT = Path(__file__).resolve().parent
BACKEND_ROOT = APP_ROOT.parent
PROJECT_ROOT = BACKEND_ROOT.parent if (BACKEND_ROOT.parent / "ressources").exists() else BACKEND_ROOT

load_dotenv(PROJECT_ROOT / ".env.local")
load_dotenv(PROJECT_ROOT / ".env")


SUPPORTED_PROVIDERS = {"academiccloud", "fu_ollama", "local_ollama"}


def parse_comma_separated(value: str) -> list[str]:
    """Parse a comma-separated env value while preserving its configured order."""
    items = (item.strip().rstrip("/") for item in value.split(","))
    return list(dict.fromkeys(item for item in items if item))


class Settings(BaseModel):
    """Centralized env-backed configuration."""

    class Api(BaseModel):
        TITLE: str = "FU Berlin CS Consultant API"
        DESCRIPTION: str = "Backend consultant for FU Berlin Informatik Master study-plan and course-offering questions."
        VERSION: str = "0.1.0"

    class Deployment(BaseModel):
        HOSTNAME: str = os.getenv("CONSULTANT_HOST", "127.0.0.1")
        PORT: int = int(os.getenv("CONSULTANT_PORT", "8000"))
        CORS_ALLOWED_ORIGINS: list[str] = parse_comma_separated(
            os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000")
        )
        FORWARDED_ALLOW_IPS: str = os.getenv("FORWARDED_ALLOW_IPS", "127.0.0.1")

    class Llm(BaseModel):
        PROVIDER: str = os.getenv("LLM_PROVIDER", "academiccloud")

    class Quota(BaseModel):
        DAILY_LLM_INVOCATIONS: int = int(os.getenv("DAILY_LLM_INVOCATIONS", "200"))
        DAILY_USER_ACTIONS: int = int(os.getenv("DAILY_USER_ACTIONS", "30"))

    class Sessions(BaseModel):
        INACTIVITY_TTL_SECONDS: int = int(os.getenv("SESSION_INACTIVITY_TTL_SECONDS", "172800"))
        CLEANUP_INTERVAL_SECONDS: int = int(os.getenv("SESSION_CLEANUP_INTERVAL_SECONDS", "300"))

    class AcademicCloud(BaseModel):
        BASE_URL: str = os.getenv("ACADEMICCLOUD_BASE_URL", "https://chat-ai.academiccloud.de/v1")
        API_KEY: str = os.getenv("ACADEMICCLOUD_API_KEY", "")
        MODEL: str = os.getenv("ACADEMICCLOUD_MODEL", "qwen3-235b-a22b")
        TEMPERATURE: float = float(os.getenv("ACADEMICCLOUD_TEMPERATURE", "0.2"))
        MAX_TOKENS: int = int(os.getenv("ACADEMICCLOUD_MAX_TOKENS", "1200"))
        TIMEOUT: float = float(os.getenv("ACADEMICCLOUD_TIMEOUT", "120"))

    class FuOllama(BaseModel):
        """FU-hosted Ollama reached through an automatic SSH tunnel.

        BASE_URL is filled in at runtime by SSHManager once the tunnel is up.
        """

        BASE_URL: str = ""
        MODEL: str = os.getenv("FU_OLLAMA_MODEL", "llama3.2")
        TEMPERATURE: float = float(os.getenv("FU_OLLAMA_TEMPERATURE", "0.2"))
        MAX_TOKENS: int = int(os.getenv("FU_OLLAMA_MAX_TOKENS", "1200"))
        TIMEOUT: float = float(os.getenv("FU_OLLAMA_TIMEOUT", "120"))

        SSH_HOST: str = os.getenv("FU_SSH_HOST", "")
        SSH_PORT: int = int(os.getenv("FU_SSH_PORT", "22"))
        SSH_USER: str = os.getenv("FU_SSH_USER", "")
        SSH_PASSWORD: str = os.getenv("FU_SSH_PASSWORD", "")
        REMOTE_BIND_ADDRESS: str = os.getenv("FU_REMOTE_BIND_ADDRESS", "127.0.0.1")
        REMOTE_BIND_PORT: int = int(os.getenv("FU_REMOTE_BIND_PORT", "11434"))

    class LocalOllama(BaseModel):
        BASE_URL: str = os.getenv("LOCAL_OLLAMA_HOST", "http://host.docker.internal:11434")
        MODEL: str = os.getenv("LOCAL_OLLAMA_MODEL", "llama3.2")
        TEMPERATURE: float = float(os.getenv("LOCAL_OLLAMA_TEMPERATURE", "0.2"))
        MAX_TOKENS: int = int(os.getenv("LOCAL_OLLAMA_MAX_TOKENS", "1200"))
        TIMEOUT: float = float(os.getenv("LOCAL_OLLAMA_TIMEOUT", "120"))

    class WizardFlow(BaseModel):
        ENABLED: bool = os.getenv("WIZARDFLOW_ENABLED", "true").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        _output_dir = Path(os.getenv("WIZARDFLOW_OUTPUT_DIR", "traces"))
        OUTPUT_DIR: Path = _output_dir if _output_dir.is_absolute() else BACKEND_ROOT / _output_dir
        FILE_PREFIX: str = os.getenv("WIZARDFLOW_FILE_PREFIX", "fu_cs_consultant")

    API: Api = Api()
    DEPLOYMENT: Deployment = Deployment()
    LLM: Llm = Llm()
    QUOTA: Quota = Quota()
    SESSIONS: Sessions = Sessions()
    ACADEMICCLOUD: AcademicCloud = AcademicCloud()
    FU_OLLAMA: FuOllama = FuOllama()
    LOCAL_OLLAMA: LocalOllama = LocalOllama()
    WIZARDFLOW: WizardFlow = WizardFlow()

    def provider_name(self) -> str:
        return self.LLM.PROVIDER.lower()

    def is_fu_ollama(self) -> bool:
        return self.provider_name() == "fu_ollama"

    def is_local_ollama(self) -> bool:
        return self.provider_name() == "local_ollama"

    def is_academiccloud(self) -> bool:
        return self.provider_name() == "academiccloud"

    def active_model_name(self) -> str:
        if self.is_fu_ollama():
            return self.FU_OLLAMA.MODEL
        if self.is_local_ollama():
            return self.LOCAL_OLLAMA.MODEL
        return self.ACADEMICCLOUD.MODEL


settings = Settings()
