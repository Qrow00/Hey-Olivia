import httpx
import json
from typing import Optional


class WeatherService:
    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    async def get_current(self, lat: float = 14.5995, lon: float = 120.9842, timezone: str = "Asia/Manila") -> dict:
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code",
            "timezone": timezone,
            "forecast_days": 1,
        }

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(self.BASE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

        current = data.get("current", {})
        daily = data.get("daily", {})

        return {
            "temperature": current.get("temperature_2m"),
            "feels_like": current.get("apparent_temperature"),
            "humidity": current.get("relative_humidity_2m"),
            "precipitation": current.get("precipitation"),
            "weather_code": current.get("weather_code"),
            "weather_description": self._code_to_text(current.get("weather_code", 0)),
            "wind_speed": current.get("wind_speed_10m"),
            "wind_direction": current.get("wind_direction_10m"),
            "high": daily.get("temperature_2m_max", [None])[0],
            "low": daily.get("temperature_2m_min", [None])[0],
            "precipitation_chance": daily.get("precipitation_probability_max", [None])[0],
        }

    async def get_summary(self, lat: float = 14.5995, lon: float = 120.9842) -> str:
        try:
            weather = await self.get_current(lat, lon)
            desc = weather["weather_description"]
            temp = weather["temperature"]
            feels = weather["feels_like"]
            humidity = weather["humidity"]
            high = weather["high"]
            low = weather["low"]
            precip = weather["precipitation_chance"]

            parts = [f"Currently {desc} and {temp}°C, feels like {feels}°C."]
            if high and low:
                parts.append(f"High of {high}°C, low of {low}°C.")
            if humidity:
                parts.append(f"Humidity at {humidity}%.")
            if precip and precip > 20:
                parts.append(f"{precip}% chance of precipitation today.")

            return " ".join(parts)
        except Exception as e:
            return f"Weather data unavailable: {e}"

    def _code_to_text(self, code: int) -> str:
        codes = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Foggy",
            48: "Rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Light rain",
            63: "Moderate rain",
            65: "Heavy rain",
            71: "Light snow",
            73: "Moderate snow",
            75: "Heavy snow",
            80: "Light showers",
            81: "Moderate showers",
            82: "Violent showers",
            95: "Thunderstorm",
            96: "Thunderstorm with hail",
            99: "Thunderstorm with heavy hail",
        }
        return codes.get(code, "Unknown")


weather_service = WeatherService()
