from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
import datetime
import pytz
import os
import swisseph as swe

# Import the existing app from astro_main (with daily endpoints)
from .astro_main import app

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set the ephemeris path
swe.set_ephe_path(os.getenv("EPHE_PATH", "/app/ephe"))

# Aspect definitions: angle and orb in degrees
ASPECT_TYPES = {
    "conjunction": (0, 8),
    "sextile": (60, 6),
    "square": (90, 6),
    "trine": (120, 6),
    "opposition": (180, 8),
}

# Planet IDs for Swiss Ephemeris
PLANET_IDS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Uranus": swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO,
}

# Zodiac signs
SIGNS = [
    "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
    "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces",
]

def _angle_diff(a1: float, a2: float) -> float:
    diff = abs(a1 - a2) % 360
    return diff if diff <= 180 else 360 - diff

@app.get("/natal")
def natal_chart(date: str, time: str, zone: str, lat: float, lon: float):
    """Return natal chart planetary positions, ascendant, midheaven and aspects for the given date, time and location."""
    try:
        # Parse date and time with timezone
        dt = datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        tz = pytz.timezone(zone)
        dt_local = tz.localize(dt)
        dt_utc = dt_local.astimezone(pytz.utc)
        jd = swe.julday(
            dt_utc.year,
            dt_utc.month,
            dt_utc.day,
            dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0,
        )

        # Compute planetary positions
        positions = {}
        for name, pid in PLANET_IDS.items():
            result, _ = swe.calc_ut(jd, pid)
            lon_deg = result[0] % 360
            sign_index = int(lon_deg // 30)
            positions[name] = {
                "longitude": lon_deg,
                "sign": SIGNS[sign_index],
                "degree": lon_deg % 30,
            }

        # Compute houses to get Ascendant and Midheaven
        cusps, ascmc = swe.houses(jd, lat, lon)
        asc_lon = ascmc[0] % 360
        mc_lon = ascmc[1] % 360
        for label, lon_value in [("Ascendant", asc_lon), ("Midheaven", mc_lon)]:
            idx = int(lon_value // 30)
            positions[label] = {
                "longitude": lon_value,
                "sign": SIGNS[idx],
                "degree": lon_value % 30,
            }

        # Compute aspects
        aspects = []
        names = list(positions.keys())
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a1 = positions[names[i]]["longitude"]
                a2 = positions[names[j]]["longitude"]
                diff = _angle_diff(a1, a2)
                for aspect, (angle, orb) in ASPECT_TYPES.items():
                    if abs(diff - angle) <= orb:
                        aspects.append({
                            "planet1": names[i],
                            "planet2": names[j],
                            "aspect": aspect,
                            "orb": round(abs(diff - angle), 2),
                        })
                        break

        return {
            "date": date,
            "time": time,
            "zone": zone,
            "lat": lat,
            "lon": lon,
            "positions": positions,
            "aspects": aspects,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Expose the FastAPI app for uvicorn
api = app
