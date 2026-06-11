import datetime

from pydantic import BaseModel, ConfigDict, UUID4


class Event(BaseModel):
    event_type: str
    emitted_at: datetime.datetime
    payload: dict

    model_config = ConfigDict(extra='ignore')


class RefinedEvent(BaseModel):
    event_id: UUID4
    event_type: str
    emitted_at: datetime.datetime
    date: datetime.date
    hour: int
    payload: dict

    model_config = ConfigDict(extra='ignore')