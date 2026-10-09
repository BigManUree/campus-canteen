from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, model_validator


class WindowBase(BaseModel):
    window_name: str
    canteen_id: Optional[int] = None
    parent_id: int = 0
    sort_order: int = 0

    model_config = ConfigDict(populate_by_name=True)


class WindowCreate(WindowBase):
    pass


class WindowUpdate(BaseModel):
    window_name: Optional[str] = None
    canteen_id: Optional[int] = None
    parent_id: Optional[int] = None
    sort_order: Optional[int] = None

    model_config = ConfigDict(populate_by_name=True)


class WindowOut(WindowBase):
    window_id: int
    canteen_name: Optional[str] = None
    create_time: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def inject_canteen_name(cls, data):
        if not isinstance(data, dict) and hasattr(data, "canteen"):
            canteen = getattr(data, "canteen", None)
            if canteen is not None and getattr(data, "canteen_name", None) is None:
                setattr(data, "canteen_name", getattr(canteen, "canteen_name", None))
        elif isinstance(data, dict) and data.get("canteen_name") is None:
            canteen = data.get("canteen")
            if canteen is not None:
                data["canteen_name"] = getattr(canteen, "canteen_name", None) if not isinstance(canteen, dict) else canteen.get("canteen_name")
        return data
