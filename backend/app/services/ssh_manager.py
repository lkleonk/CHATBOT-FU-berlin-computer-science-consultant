import logging
from typing import Any

from app.settings import settings


logger = logging.getLogger(__name__)


class SSHManager:
    """Manages the SSH tunnel for FU-hosted Ollama (provider=fu_ollama)."""

    def __init__(self):
        self.tunnel: Any | None = None

    def start(self) -> None:
        logger.info(
            "Initializing SSH tunnel to %s@%s:%s",
            settings.FU_OLLAMA.SSH_USER,
            settings.FU_OLLAMA.SSH_HOST,
            settings.FU_OLLAMA.SSH_PORT,
        )
        from sshtunnel import SSHTunnelForwarder

        self.tunnel = SSHTunnelForwarder(
            (settings.FU_OLLAMA.SSH_HOST, settings.FU_OLLAMA.SSH_PORT),
            ssh_username=settings.FU_OLLAMA.SSH_USER,
            ssh_password=settings.FU_OLLAMA.SSH_PASSWORD,
            remote_bind_address=(
                settings.FU_OLLAMA.REMOTE_BIND_ADDRESS,
                settings.FU_OLLAMA.REMOTE_BIND_PORT,
            ),
            local_bind_address=("127.0.0.1", 0),
        )
        self.tunnel.start()
        logger.info(
            "SSH tunnel established. Forwarding 127.0.0.1:%s -> %s:%s",
            self.tunnel.local_bind_port,
            settings.FU_OLLAMA.REMOTE_BIND_ADDRESS,
            settings.FU_OLLAMA.REMOTE_BIND_PORT,
        )

    def stop(self) -> None:
        if self.tunnel:
            logger.info("Stopping SSH tunnel.")
            self.tunnel.stop()
            self.tunnel = None

    def get_base_url(self) -> str | None:
        if self.tunnel and self.tunnel.is_active:
            return f"http://127.0.0.1:{self.tunnel.local_bind_port}"
        return None
