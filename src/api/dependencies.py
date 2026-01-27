"""
API Dependencies

Dependency injection for FastAPI routes.
"""

from typing import Optional
import logging

from src.config import MNEMEConfig
from src.pipeline import MNEME

logger = logging.getLogger(__name__)

# Global MNEME instance (singleton pattern for API)
_mneme_instance: Optional[MNEME] = None
_config_instance: Optional[MNEMEConfig] = None


def set_mneme(mneme: MNEME) -> None:
    """Set the global MNEME instance."""
    global _mneme_instance
    _mneme_instance = mneme
    logger.info("MNEME instance set for API")


def get_mneme() -> MNEME:
    """Get the global MNEME instance."""
    if _mneme_instance is None:
        raise RuntimeError(
            "MNEME not initialized. Call set_mneme() first or use MNEMEBuilder."
        )
    return _mneme_instance


def set_config(config: MNEMEConfig) -> None:
    """Set the global config instance."""
    global _config_instance
    _config_instance = config


def get_config() -> MNEMEConfig:
    """Get the global config instance."""
    if _config_instance is None:
        _config_instance = MNEMEConfig()
    return _config_instance


async def get_mneme_async() -> MNEME:
    """Async version of get_mneme for FastAPI."""
    return get_mneme()


async def get_config_async() -> MNEMEConfig:
    """Async version of get_config for FastAPI."""
    return get_config()
