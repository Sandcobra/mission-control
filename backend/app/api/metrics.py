from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.schemas.metrics import CostMetrics, FailureMetrics, OverviewMetrics
from app.services import metrics_service

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get(
    "/overview",
    response_model=OverviewMetrics,
    status_code=status.HTTP_200_OK,
    summary="High-level operational overview metrics",
)
async def get_overview(
    db: AsyncSession = Depends(get_db),
) -> OverviewMetrics:
    return await metrics_service.get_overview_metrics(db)


@router.get(
    "/costs",
    response_model=CostMetrics,
    status_code=status.HTTP_200_OK,
    summary="Token usage and cost breakdown by agent, task, and day",
)
async def get_costs(
    db: AsyncSession = Depends(get_db),
) -> CostMetrics:
    return await metrics_service.get_cost_metrics(db)


@router.get(
    "/failures",
    response_model=FailureMetrics,
    status_code=status.HTTP_200_OK,
    summary="Task failure analysis and recent error details",
)
async def get_failures(
    db: AsyncSession = Depends(get_db),
) -> FailureMetrics:
    return await metrics_service.get_failure_metrics(db)
