from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routes.data_snapshots import router as data_snapshots_router
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.reference import router as reference_router
from app.api.v1.routes.risk import router as risk_router
from app.api.v1.routes.trades import router as trades_router


router = APIRouter()

router.include_router(health_router, prefix="/system")
router.include_router(reference_router, prefix="/reference")
router.include_router(risk_router, prefix="/risk")
router.include_router(trades_router, prefix="/trades")
router.include_router(data_snapshots_router, prefix="/data")
