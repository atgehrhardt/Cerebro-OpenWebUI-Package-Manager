"""
title: Template
author: Andrew Tait Gehrhardt
author_url: https://github.com/atgehrhardt/Cerebro-OpenWebUI-Package-Manager/plugins/template
funding_url: https://github.com/open-webui
version: 0.1.0
"""

import asyncio
from asyncio import sleep
from pydantic import BaseModel, Field
from typing import Optional, Union, Generator, Iterator
from apps.webui.models.files import Files
from config import UPLOAD_DIR


class Tools:
    """
    Launches the applet example template file
    """

    class Valves(BaseModel):
        priority: int = Field(
            default=0, description="Priority level for the filter operations."
        )

    def __init__(self):
        self.valves = self.Valves()
        self.package_name = "template"
        self.applet_file_id = None

    async def run(
        self,
        body: Optional[dict] = None,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[callable] = None,
        __event_call__: Optional[callable] = None,
    ) -> str:
        """
        Retrieves information about the weather
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
                "Applet file found... launching",
            ]
            for message in loading_messages:
                await __event_emitter__(
                    {"type": "replace", "data": {"content": message}}
                )
                await asyncio.sleep(1)

            # Finally, replace with the actual applet embed
            final_message = f"{{{{HTML_FILE_ID_{self.applet_file_id}}}}}"
            await __event_emitter__(
                {"type": "replace", "data": {"content": final_message}}
            )

            # Simulate a short delay to ensure the message is displayed
            await sleep(0.5)

            return ""

        except Exception as e:
            error_message = f"An error occurred while launching the applet: {str(e)}"
            await __event_emitter__(
                {"type": "replace", "data": {"content": error_message}}
            )
            await __event_call__(error_message)
            return error_message
