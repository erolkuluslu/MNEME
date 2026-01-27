"""
MNEME API

FastAPI-based REST API for the MNEME RAG system.
"""

from .routes import router, create_app
from .dependencies import set_mneme, get_mneme, set_config, get_config
from .schemas import (
    QueryRequest,
    QueryResponse,
    CitationSchema,
    StatsResponse,
    HealthResponse,
)

__all__ = [
    "router",
    "create_app",
    "set_mneme",
    "get_mneme",
    "set_config",
    "get_config",
    "QueryRequest",
    "QueryResponse",
    "CitationSchema",
    "StatsResponse",
    "HealthResponse",
]
