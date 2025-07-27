from typing import Annotated, List

from fastapi import APIRouter, Query
from sqlmodel import select

from app.database.deps import CurrentUser, SessionDep
from app.database.models import Plugin, PluginPublic
from app.logging import log_operation
from app.responses import responses

router = APIRouter(prefix="/plugins", responses=responses)


@router.get("/")
async def read_plugins(
    session: SessionDep,
    current_user: CurrentUser,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> List[PluginPublic]:

    log_operation(
        operation="READ",
        model="Plugin",
        status="PENDING",
        user_id=current_user.id,
    )

    plugins = session.exec(select(Plugin).offset(offset).limit(limit)).all()

    log_operation(
        operation="READ",
        model="Plugin",
        status="SUCCESS",
        user_id=current_user.id,
        detail=f"offset : {offset} limit: {limit}",
    )

    return plugins
