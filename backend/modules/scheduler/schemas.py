import datetime as dt

from pydantic import BaseModel, ConfigDict


class ScheduleCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    analysis_id: str
    cron_expression: str
    enabled: bool = True


class ScheduleUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cron_expression: str | None = None
    enabled: bool | None = None


class ScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    analysis_id: str
    cron_expression: str
    enabled: bool
    last_run: dt.datetime | None
    next_run: dt.datetime | None
    created_at: dt.datetime
