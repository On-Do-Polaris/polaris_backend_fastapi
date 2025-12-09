# Routes Package
from .analysis import router as analysis_router
from .reports import router as reports_router
from .simulation import router as simulation_router
from .meta import router as meta_router
from .recommendation import router as recommendation_router
from .additional_data import router as additional_data_router
from .disaster_history import router as disaster_history_router
from .dashboard import router as dashboard_router

__all__ = [
    "analysis_router",
    "reports_router",
    "simulation_router",
    "meta_router",
    "recommendation_router",
    "additional_data_router",
    "disaster_history_router",
    "dashboard_router",
]
