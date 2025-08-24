from fastapi import FastAPI, HTTPException
import os
import datetime
import swisseph as swe
import pytz

# Initialize FastAPI app
app = FastAPI(title="Astro Oraculo API")
api = app

# Set path to Swiss ephemeris files from environment variable if provided
ephe_path = os.getenv("EPHE_PATH")
if ephe_path:
    swe.set_ephe_path(ephe_path)

@app.get("/")
def root():
    """Root endpoint to confirm the API is running."""
    return {"message": "Astro oráculo API is running"}

@app.get("/transits/daily")
def daily_transits(date: str = None, time: str = "12:00", zone: str = "UTC"):
    """Return planetary positions for a given date and time."""
    try:
        # If date not provided, use current date in given timezone
        if date is None:
            tz = pytz.timezone(zone)
            now = datetime.datetime.now(tz)
            date = now.strftime("%Y-%m-%d")

        # Parse the input date and time
        dt = datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        # Localize to the specified timezone
        tz = pytz.timezone(zone)
        dt_local = tz.localize(dt)
        # Convert to UTC for Swiss Ephemeris
        dt_utc = dt_local.astimezone(pytz.utc)
        # Calculate Julian day
        jd = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day,
                        dt_utc.hour + dt_utc.minute/60.0 + dt_utc.second/3600.0)

        # Define planets to calculate
        planet_ids = {
            "Sun": swe.SUN,
            "Moon": swe.MOON,
            "Mercury": swe.MERCURY,
            "Venus": swe.VENUS,
            "Mars": swe.MARS,
            "Jupiter": swe.JUPITER,
            "Saturn": swe.SATURN,
            "Uranus": swe.URANUS,
            "Neptune": swe.NEPTUNE,
            "Pluto": swe.PLUTO
        }
        # Names of zodiac signs
        signs = [
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
        ]
        positions = {}
        for name, pid in planet_ids.items():
            result, _ = swe.calc_ut(jd, pid)
            lon = result[0] % 360  # longitude in degrees
            sign_index = int(lon // 30)
            deg_in_sign = lon % 30
            positions[name] = {
                "longitude": lon,
                "sign": signs[sign_index],
                "degree": deg_in_sign
            }

        return {
            "date": date,
            "time": time,
            "zone": zone,
            "positions": positions
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/natal")
def natal_chart():
    """
    Placeholder endpoint for natal chart calculations.
    It should accept birth details and return positions and aspects.
    """
    # TODO: implement natal chart computation using Swiss Ephemeris
    return {"message": "natal endpoint placeholder"}

@app.post("/oraculo/lectura")
def oraculo_lectura():
    """
    Placeholder endpoint for generating oracular readings based on astrological data.
    It should map positions and aspects to tarot cards using CSV correspondences.
    """
    # TODO: implement oracular reading logic
    return {"message": "oráculo lectura endpoint placeholder"}
