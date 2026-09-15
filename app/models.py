from datetime import datetime, timezone
from typing import Annotated, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Model(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)


class LocationInput(Model):
    query: Name
    city: Annotated[str, StringConstraints(strip_whitespace=True, max_length=100)] = ''


class TripInput(Model):
    start: LocationInput
    waypoints: list[LocationInput] = Field(min_length=3, max_length=8)
    end: LocationInput | None = None
    end_mode: Literal['fixed', 'open', 'roundtrip'] = 'fixed'
    objective: Literal['fastest', 'shortest'] = 'fastest'
    raw_input: str = Field(default='', max_length=3000)

    @model_validator(mode='after')
    def validate_end(self):
        if (self.end_mode == 'fixed') != (self.end is not None):
            raise ValueError('固定终点必须填写；开放或返回起点模式不能另外填写终点')
        return self

    def locations(self) -> list[LocationInput]:
        return [self.start, *self.waypoints] + ([self.end] if self.end else [])


class Place(Model):
    candidate_id: str
    poi_id: str | None = None
    name: Name
    address: str = Field(max_length=1000)
    city: str = Field(default='', max_length=100)
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    coordinate_system: Literal['GCJ-02'] = 'GCJ-02'


class Trip(Model):
    trip_id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: str = Field(default_factory=now)
    updated_at: str = Field(default_factory=now)
    revision: int = 0
    status: Literal['draft', 'resolved', 'confirmed', 'optimized'] = 'draft'
    input: TripInput
    candidates: list[list[Place]] = Field(default_factory=list)
    places: list[Place] = Field(default_factory=list)
    result: dict | None = None


class Revision(Model):
    revision: int = Field(ge=0, strict=True)


class Confirmation(Revision):
    candidate_ids: list[str] = Field(min_length=4, max_length=10)
