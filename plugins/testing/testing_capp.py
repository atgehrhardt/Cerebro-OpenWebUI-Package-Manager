import os
import asyncio
from pydantic import BaseModel
from typing import Optional, Union, Generator, Iterator
from apps.webui.models.files import Files

class Tools:
    """
    A tool for embedding a specific applet in the chat.
    Use this tool when you need to display the [YOUR_PACKAGE_NAME] applet in the conversation.
    The applet must be previously installed using the package manager.
    """

    def __init__(self):
        self.package_name = "testing"  
        self.applet_file_id = None

    async def run(
        self, 
        __user__: Optional[dict] = None, 
        __event_emitter__: Optional[callable] = None
    ) -> Union[str, Generator, Iterator]:
        """
        Embed the testing applet in the chat.
        :param __user__: User information, including the user ID.
        :param __event_emitter__: Function to emit events during the process.
        :return: A string that will be replaced with the embedded applet, or an error message.
        """
        
        if not __user__ or "id" not in __user__:
            return "Error: User ID not provided"

        user_id = __user__["id"]
        
        if __event_emitter__:
            await __event_emitter__(
                {"type": "status", "data": {"description": "Searching for applet file", "done": False}}
            )
        
        expected_filename = f"/cerebro/plugins/{self.package_name}/{self.package_name}_capp.html"
        
        all_files = Files.get_files()
        matching_file = next((file for file in all_files 
                              if file.user_id == user_id and file.filename == expected_filename), None)
        
        if not matching_file:
            if __event_emitter__:
                await __event_emitter__(
                    {"type": "status", "data": {"description": "Applet file not found", "done": True}}
                )
            return f"Error: Applet file for {self.package_name} not found. Make sure the package is installed."
        
        self.applet_file_id = matching_file.id
        
        if __event_emitter__:
            await __event_emitter__(
                {"type": "status", "data": {"description": "Applet file found", "done": True}}
            )
            await asyncio.sleep(1)  # Simulating some processing time
            await __event_emitter__(
                {"type": "status", "data": {"description": "Embedding applet", "done": False}}
            )
            await asyncio.sleep(1)  # Simulating embedding process
            await __event_emitter__(
                {"type": "status", "data": {"description": "Applet embedded successfully", "done": True}}
            )
        
        return f"{{{{HTML_FILE_ID_{self.applet_file_id}}}}}"