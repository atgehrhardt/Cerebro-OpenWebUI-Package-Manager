import os
import requests
from datetime import datetime
from pydantic import BaseModel
from typing import List


class Tools:
    class UserValves(BaseModel):
        OPENWEATHER_API_KEY: str
        pass

    def __init__(self):
        pass

    def get_current_weather(self, city: str, __user__: dict) -> str:
        """
        Get the current weather for a given city.
        :param city: The name of the city to get the weather for.
        :return: The current weather information or an error message.
        """
        print(__user__)

        user_valves = __user__.get("valves")
        if not user_valves:
            return "Tell the user: 'User Valves not configured.'"

        api_key = user_valves.OPENWEATHER_API_KEY
        if not api_key:
            return "Tell the user that the API key is must be set in the valves: 'OPENWEATHER_API_KEY'."

        base_url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": api_key,
            "units": "metric",  # Optional: Use 'imperial' for Fahrenheit
        }

        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
            data = response.json()

            if data.get("cod") != 200:
                return f"Error fetching weather data: {data.get('message')}"

            weather_description = data["weather"][0]["description"]
            temperature = data["main"]["temp"]
            humidity = data["main"]["humidity"]
            wind_speed = data["wind"]["speed"]

            return f"Weather in {city}: {temperature}°C - {weather_description}"
        except requests.RequestException as e:
            return f"Error fetching weather data: {str(e)}"
