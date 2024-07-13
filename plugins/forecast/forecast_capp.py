"""
title: Forecast
author: Andrew Tait Gehrhardt
author_url: https://github.com/atgehrhardt/Cerebro-OpenWebUI-Package-Manager/plugins/forecast
funding_url: https://github.com/open-webui
version: 0.1.0
"""

import asyncio
from asyncio import sleep
from pydantic import BaseModel, Field
from typing import Optional
from apps.webui.models.files import Files
from config import UPLOAD_DIR
import aiohttp


class Tools:
    """
    Used to retrieve forecast data based on user's detailed location
    """

    class Valves(BaseModel):
        priority: int = Field(
            default=0, description="Priority level for the filter operations."
        )

    def __init__(self):
        self.valves = self.Valves()
        self.package_name = "forecast"
        self.applet_file_id = None

    async def get_user_location(self, session):
        """
        Get user's detailed location based on IP address
        """
        async with session.get("https://ipapi.co/json/") as response:
            if response.status != 200:
                raise Exception(f"Location API returned status code {response.status}")
            location_data = await response.json()
            return {
                "latitude": location_data["latitude"],
                "longitude": location_data["longitude"],
                "city": location_data["city"],
                "region": location_data["region"],
                "country": location_data["country_name"],
                "postal": location_data["postal"],
            }

    async def run(
        self,
        body: Optional[dict] = None,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[callable] = None,
        __event_call__: Optional[callable] = None,
    ) -> str:
        """
        Retrieves information about the weather for the user's detailed location
        :param body: The request body.
        :param __user__: User information, including the user ID.
        :param __event_emitter__: Function to emit events during the process.
        :param __event_call__: Function to call for the final output.
        :return: The final message or an empty string.
        """
        if not __user__ or "id" not in __user__:
            return "Error: User ID not provided"
        if not __event_emitter__ or not __event_call__:
            return "Error: Event emitter or event call not provided"

        user_id = __user__["id"]

        try:
            expected_filename = f"{UPLOAD_DIR}/cerebro/plugins/{self.package_name}/{self.package_name}_capp.html"
            all_files = Files.get_files()
            matching_file = next(
                (
                    file
                    for file in all_files
                    if file.user_id == user_id and file.filename == expected_filename
                ),
                None,
            )

            if not matching_file:
                error_message = f"Error: Applet file for {self.package_name} not found. Make sure the package is installed."
                await __event_emitter__(
                    {"type": "replace", "data": {"content": error_message}}
                )
                await __event_call__(error_message)
                return error_message

            self.applet_file_id = matching_file.id

            # Simulate a loading process
            loading_messages = [
                "Fetching weather data...",
            ]
            for message in loading_messages:
                await __event_emitter__(
                    {"type": "replace", "data": {"content": message}}
                )
                await asyncio.sleep(1)

            headers = {
                "User-Agent": "(myweatherapp.com, contact@myweatherapp.com)",
                "Accept": "application/geo+json",
            }

            async with aiohttp.ClientSession() as session:
                # Get user's detailed location
                location = await self.get_user_location(session)

                # Get the forecast URL for the location
                points_url = f"https://api.weather.gov/points/{location['latitude']},{location['longitude']}"
                async with session.get(points_url, headers=headers) as response:
                    if response.status != 200:
                        raise Exception(f"API returned status code {response.status}")
                    points_data = await response.json()

                # Get the actual forecast
                forecast_url = points_data["properties"]["forecast"]
                async with session.get(forecast_url, headers=headers) as response:
                    if response.status != 200:
                        raise Exception(f"API returned status code {response.status}")
                    forecast_data = await response.json()

            # Extract relevant information
            current_period = forecast_data["properties"]["periods"][0]
            temperature = current_period["temperature"]
            temperature_unit = current_period["temperatureUnit"]
            description = current_period["shortForecast"]
            wind_speed = current_period["windSpeed"]
            wind_direction = current_period["windDirection"]

            # Prepare the detailed location string
            detailed_location = (
                f"{location['city']}, {location['region']}, {location['country']}"
            )

            # Prepare the weather report
            weather_report = f"Current weather in {detailed_location}:\n"
            weather_report += f"Temperature: {temperature}°{temperature_unit}\n"
            weather_report += f"Description: {description}\n"
            weather_report += f"Wind: {wind_speed} from {wind_direction}"

            # Finally, replace with the actual applet embed and weather report
            final_message = f"""{{{{HTML_FILE_ID_{self.applet_file_id}}}}}
            """
            await __event_emitter__(
                {"type": "replace", "data": {"content": final_message}}
            )

            # Simulate a short delay to ensure the message is displayed
            await sleep(0.5)

            return f"""You can find a summary of the weather for {detailed_location} below:\n\n
            {weather_report}

            Please give a detailed summary of the weather report below and ensure you infor the user of the location.
            \n\n\n
            """

        except Exception as e:
            error_message = (
                f"An error occurred while fetching the weather data: {str(e)}"
            )
            print(f"Debug - Error details: {e}")
            await __event_emitter__(
                {"type": "replace", "data": {"content": error_message}}
            )
            await __event_call__(error_message)
            return error_message
