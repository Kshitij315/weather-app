# app/models.py
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class WeatherRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    city: str
    lat: float
    lon: float
    temp_c: float
    feels_like_c: float
    humidity: int
    wind_ms: float
    rain_1h: float = 0.0
    recorded_at: datetime = Field(default_factory=datetime.utcnow)
