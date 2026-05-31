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


class Settings(BaseModel):
    """Centralized env-backed configuration."""

    class Api(BaseModel):
        TITLE: str = "FU Berlin CS Consultant API"
        DESCRIPTION: str = "Backend consultant for FU Berlin Informatik Master study-plan and course-offering questions."
        VERSION: str = "0.1.0"

    class Deployment(BaseModel):
        HOSTNAME: str = os.getenv("CONSULTANT_HOST", "0.0.0.0")
        PORT: int = int(os.getenv("CONSULTANT_PORT", "5100"))

    class Llm(BaseModel):
        PROVIDER: str = os.getenv("LLM_PROVIDER", "academiccloud")

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

    class Qdrant(BaseModel):
        HOST: str = os.getenv("QDRANT_HOST", "qdrant")
        PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
        COLLECTION: str = os.getenv("QDRANT_COLLECTION", "fu_cs_consultant_knowledge")
        EMBEDDING_MODEL: str = os.getenv(
            "QDRANT_EMBEDDING_MODEL",
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        )
        VECTOR_SIZE: int = int(os.getenv("QDRANT_VECTOR_SIZE", "384"))

    class Rag(BaseModel):
        SCORE_THRESHOLD: float = float(os.getenv("RAG_SCORE_THRESHOLD", "0.35"))
        RETRIEVAL_LIMIT: int = int(os.getenv("RAG_RETRIEVAL_LIMIT", "5"))
        RESOURCES_DIR: Path = Path(os.getenv("RESOURCES_DIR", str(PROJECT_ROOT / "ressources")))

    API: Api = Api()
    DEPLOYMENT: Deployment = Deployment()
    LLM: Llm = Llm()
    ACADEMICCLOUD: AcademicCloud = AcademicCloud()
    FU_OLLAMA: FuOllama = FuOllama()
    LOCAL_OLLAMA: LocalOllama = LocalOllama()
    QDRANT: Qdrant = Qdrant()
    RAG: Rag = Rag()

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
