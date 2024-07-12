import os
from pydantic import BaseModel
from typing import Optional
from apps.webui.models.files import Files

class Tools:
    """
    A tool for embedding a specific applet in the chat.
    Use this tool when you need to display the [YOUR_PACKAGE_NAME] applet in the conversation.
    The applet must be previously installed using the package manager.
    """

    class UserValves(BaseModel):
        pass  # No specific valves needed for this tool

    def __init__(self):
        self.package_name = "testing"  
        self.applet_file_id = None

    def run(self, __user__: Optional[dict] = None) -> str:
        if not __user__ or "id" not in __user__:
            return "Error: User ID not provided"

        user_id = __user__["id"]
        
        expected_filename = f"/cerebro/plugins/{self.package_name}/{self.package_name}_capp.html"
        
        all_files = Files.get_files()
        matching_file = next((file for file in all_files 
                              if file.user_id == user_id and file.filename == expected_filename), None)
        
        if not matching_file:
            return f"Error: Applet file for {self.package_name} not found. Make sure the package is installed."
        
        self.applet_file_id = matching_file.id
        
        return f"{{{{HTML_FILE_ID_{self.applet_file_id}}}}}}"