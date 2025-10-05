# from fastapi import FastAPI

# app = FastAPI()

# @app.get("/")
# def read_root():
#     return {"message": "Hello from FastAPI backend!"}

# @app.get("/health/{name}")
# def greet_user(name: str):
#     return {"greeting": f"FastAPI is running, {name}!"}


# app/main.py
import os
import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import random
from dotenv import load_dotenv

# local imports
from .db import create_db_and_tables, get_session
from .models import WeatherRecord
from sqlmodel import select

# load environment
load_dotenv()

OPENWEATHER_KEY = os.getenv("OPENWEATHER_API_KEY")
if not OPENWEATHER_KEY:
    print("Warning: OPENWEATHER_API_KEY not set in environment.")

app = FastAPI(title="Weather Aggregator")

# Allow CORS from your Django dev server (adjust origins if using other ports)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8001", "http://127.0.0.1:8001", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

class CurrentWeatherOut(BaseModel):
    city: str
    lat: float
    lon: float
    temp_c: float
    feels_like_c: float
    humidity: int
    wind_ms: float
    rain_1h: float



@app.get("/api/weather/current", response_model=CurrentWeatherOut)
def get_current_weather(city: str = Query("Thane,IN")):
    if not OPENWEATHER_KEY:
        raise HTTPException(status_code=500, detail="OpenWeather API key not configured.")
    params = {"q": city, "appid": OPENWEATHER_KEY, "units": "metric"}
    url = "https://api.openweathermap.org/data/2.5/weather"
    r = requests.get(url, params=params, timeout=10)
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    d = r.json()
    rain_1h = d.get("rain", {}).get("1h", 0.0)
    return {
        "city": f"{d.get('name')},{d.get('sys',{}).get('country','')}",
        "lat": d.get("coord", {}).get("lat"),
        "lon": d.get("coord", {}).get("lon"),
        "temp_c": d.get("main", {}).get("temp"),
        "feels_like_c": d.get("main", {}).get("feels_like"),
        "humidity": d.get("main", {}).get("humidity"),
        "wind_ms": d.get("wind", {}).get("speed"),
        "rain_1h": rain_1h
    }

@app.get("/ping")
def ping():
    return {"ok": True, "time": datetime.utcnow().isoformat()}


@app.post("/api/weather/save")
def save_current(city: str = Query("Thane,IN")):
    print("DEBUG: /api/weather/save called for", city, flush=True)
    cw = get_current_weather(city=city)
    with get_session() as session:
        rec = WeatherRecord(
            city=cw["city"],
            lat=cw["lat"],
            lon=cw["lon"],
            temp_c=cw["temp_c"],
            feels_like_c=cw["feels_like_c"],
            humidity=cw["humidity"],
            wind_ms=cw["wind_ms"],
            rain_1h=cw["rain_1h"],
        )
        session.add(rec)
        session.commit()
        session.refresh(rec)
        return {"saved_id": rec.id}

@app.get("/api/weather/history", response_model=List[WeatherRecord])
def get_history(city: str = Query("Thane,IN"), hours: int = Query(72)):
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    with get_session() as session:
        q = select(WeatherRecord).where(WeatherRecord.recorded_at >= cutoff)
        results = session.exec(q).all()
        results = [r for r in results if city.split(",")[0].lower() in r.city.lower()]
        return results
    

@app.get("/api/nasa/rainfall")
def nasa_rainfall(lat: float, lon: float, start: Optional[str] = None, end: Optional[str] = None):
    """
    Fetch daily rainfall using NASA POWER API (reliable public endpoint).
    Returns last 7 days of precipitation (mm/day).
    Filters out missing (-999) values.
    """
    import requests
    from datetime import datetime, timedelta

    # Default: last 7 days
    end_dt = datetime.utcnow() if not end else datetime.fromisoformat(end)
    start_dt = (end_dt - timedelta(days=6)) if not start else datetime.fromisoformat(start)

    start_str = start_dt.strftime("%Y%m%d")
    end_str = end_dt.strftime("%Y%m%d")

    url = (
        "https://power.larc.nasa.gov/api/temporal/daily/point"
        f"?parameters=PRECTOTCORR&community=RE&longitude={lon}&latitude={lat}"
        f"&start={start_str}&end={end_str}&format=JSON"
    )

    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        rain_data = data.get("properties", {}).get("parameter", {}).get("PRECTOTCORR", {})
        series = []
        for date, val in rain_data.items():
            if val != -999:  # skip missing data
                series.append({"date": date, "rain_mm": round(val, 2)})

        series.sort(key=lambda x: x["date"])
        return {"lat": lat, "lon": lon, "series": series}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
