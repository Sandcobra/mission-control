from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.schemas.runs import RunCostUpdateRequest, RunCreateRequest, RunResponse
from app.services import run_service

router = APIRouter(prefix="/api/runs", tags=["runs"])


def _run_to_response(run) -> RunResponse:
    return RunResponse(
        id=run.id,
        agent_id=run.agent_id,
        task_id=run.task_id,
        run_status=run.run_status,
        started_at=run.started_at,
        ended_at=run.ended_at,
        token_input=run.token_input,
        token_output=run.token_output,
        estimated_cost_usd=float(run.estimated_cost_usd) if run.estimated_cost_usd is not None else None,
        metadata=run.metadata_,
    )


@router.post(
    "/",
    response_model=RunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new agent run",
)
async def create_run(
    body: RunCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> RunResponse:
    run = await run_service.create_run(db, body)
    return _run_to_response(run)


@router.post(
    "/{run_id}/cost",
    response_model=RunResponse,
    status_code=status.HTTP_200_OK,
    summary="Update token usage and cost for a run",
)
async def update_run_cost(
    run_id: uuid.UUID,
    body: RunCostUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> RunResponse:
    try:
        run = await run_service.update_run_cost(db, run_id, body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return _run_to_response(run)


@router.get(
    "/{run_id}",
    response_model=RunResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a single run by ID",
)
async def get_run(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> RunResponse:
    run = await run_service.get_run(db, run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run {run_id} not found.",
        )
    return _run_to_response(run)
