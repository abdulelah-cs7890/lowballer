"""Lowballer API — serves flagged underpriced car deals to the dashboard."""

from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import repository
from app.config import settings
from app.db import SessionLocal, get_session, init_db
from app.models.schemas import DealDetailOut, DealOut, HealthOut
from app.models.tables import Flag
from app.valuation.model import MODEL_PATH

STREAM_POLL_SECONDS = 2.0


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    task = None
    if settings.refresh_interval_seconds > 0:
        from app.ebay.scheduler import run_loop

        task = asyncio.create_task(run_loop(settings.refresh_interval_seconds))
    yield
    if task:
        task.cancel()


app = FastAPI(title="Lowballer API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz", response_model=HealthOut)
def healthz(session: Session = Depends(get_session)) -> HealthOut:
    open_deals = session.scalar(
        select(func.count()).select_from(Flag).where(Flag.status == "open")
    )
    return HealthOut(
        status="ok", model_loaded=MODEL_PATH.exists(), open_deals=int(open_deals or 0)
    )


@app.get("/deals", response_model=list[DealOut])
def deals(
    make: str | None = None,
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    min_percent_below: float | None = Query(None, ge=0, le=1),
    limit: int = Query(100, ge=1, le=500),
    session: Session = Depends(get_session),
) -> list[dict]:
    return repository.list_deals(
        session,
        make=make,
        min_price=min_price,
        max_price=max_price,
        min_percent_below=min_percent_below,
        limit=limit,
    )


@app.get("/deals/stream")
async def deals_stream(request: Request) -> StreamingResponse:
    """Server-Sent Events: pushes each newly flagged deal as it appears.

    Starts from the current newest flag, then polls for anything newer and streams it.
    Comment lines (`:`) act as heartbeats so proxies don't drop the idle connection.
    """

    async def event_generator():
        with SessionLocal() as session:
            last_id = repository.max_flag_id(session)
        yield ": connected\n\n"
        while True:
            if await request.is_disconnected():
                break
            with SessionLocal() as session:
                fresh = repository.new_flagged_deals(session, last_id)
            for flag_id, deal in fresh:
                last_id = max(last_id, flag_id)
                yield f"data: {json.dumps(deal)}\n\n"
            await asyncio.sleep(STREAM_POLL_SECONDS)
            yield ": ping\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/deals/{listing_id}", response_model=DealDetailOut)
def deal_detail(listing_id: str, session: Session = Depends(get_session)) -> dict:
    deal = repository.get_deal(session, listing_id)
    if deal is None:
        raise HTTPException(status_code=404, detail="listing not found")
    return deal
