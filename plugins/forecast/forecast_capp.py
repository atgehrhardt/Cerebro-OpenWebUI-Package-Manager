import os
import asyncio
from pydantic import BaseModel
from typing import Optional, Union, Generator, Iterator
from apps.webui.models.files import Files

from config import UPLOAD_DIR


class Tools:
    """
    A tool used for displaying current weather information
    """

    def __init__(self):
        self.package_name = "weather"
        self.applet_file_id = None

    async def run(
        self,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[callable] = None,
        __event_call__: Optional[callable] = None,
    ) -> str:
        """
        Embed the testing applet in the chat.
        :param __user__: User information, including the user ID.
        :param __event_emitter__: Function to emit events during the process.
        :param __event_call__: Function to call for the final output.
        :return: An empty string, as the final output is handled by __event_call__.
        """

        if not __user__ or "id" not in __user__:
            return "Error: User ID not provided"

        if not __event_emitter__ or not __event_call__:
            return "Error: Event emitter or event call not provided"

        user_id = __user__["id"]

        # Emit initial message
        await __event_emitter__(
            {"type": "replace", "data": {"content": "Searching for applet file..."}}
        )

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
            return ""

        self.applet_file_id = matching_file.id

        # Simulate a loading process
        loading_messages = [
            "Applet file found: Loading",
        ]

        for message in loading_messages:
            await __event_emitter__({"type": "replace", "data": {"content": message}})
            await asyncio.sleep(1)

        # Finally, replace with the actual applet embed
        final_message = f"{{{{HTML_FILE_ID_{self.applet_file_id}}}}}"
        await __event_emitter__({"type": "replace", "data": {"content": final_message}})

        # Use __event_call__ to set the final output
        await __event_call__(final_message)

        # Return an empty string as the final output is handled by __event_call__
        return ""
