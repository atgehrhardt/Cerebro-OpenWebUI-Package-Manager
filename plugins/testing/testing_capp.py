import os
from pydantic import BaseModel
from typing import Optional
from apps.webui.models.files import Files

class Tools:
    class UserValves(BaseModel):
        pass  # No specific valves needed for this tool

    def __init__(self):
        self.applet_file_id = None

    def embed_applet(self, package_name: str, __user__: Optional[dict] = None) -> str:
        """
        Embed the applet in the chat.
        :param package_name: The name of the package containing the applet.
        :return: A string that will be replaced with the embedded applet.
        """
        if not __user__ or "id" not in __user__:
            return "Error: User ID not provided"

        user_id = __user__["id"]
        
        # Construct the expected filename
        expected_filename = f"/cerebro/plugins/{package_name}/{package_name}_capp.html"
        
        # Get all files for the user
        all_files = Files.get_files()
        
        # Find the file with the matching filename
        matching_file = next((file for file in all_files 
                              if file.user_id == user_id and file.filename == expected_filename), None)
        
        if not matching_file:
            return f"Error: Applet file for package '{package_name}' not found"
        
        self.applet_file_id = matching_file.id
        
        # This string will be replaced with the actual applet content
        return f"{{{{HTML_FILE_ID_{self.applet_file_id}}}}}}"