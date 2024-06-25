from typing import List, Dict, Optional
import re
import uuid
from apps.webui.models.files import Files
import requests


class Filter:
    def __init__(self):
        self.file = None
        self.user_id = None

    def inlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        print(f"inlet:{__name__}")
        print(f"inlet:body:{body}")
        print(f"inlet:user:{__user__}")
        if __user__ and "id" in __user__:
            self.user_id = __user__["id"]
        else:
            print("Warning: No valid user ID provided")
        return body

    def handle_package(self, package_name: str):
        files = Files.get_files()
        files = [file for file in files if file.user_id == self.user_id]
        files = [
            file
            for file in files
            if file.filename.endswith(f"{package_name}_capp.html")
        ]
        print("Files: ", files)
        if files:
            self.file = files[0].id
            print(f"\nFound file: {self.file}\n")
            return True
        else:
            print(f"No matching file found for package: {package_name}")
            return False

    def outlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        print(f"outlet:{__name__}")
        print(f"outlet:body:{body}")
        print(f"outlet:user:{__user__}")
        messages = body.get("messages", [])
        if messages:
            last_message = messages[-1]["content"]
            owui_run_matches = re.finditer(r"owui run (\w+)", last_message)

            new_content = last_message
            for match in owui_run_matches:
                package_name = match.group(1)
                print(f"Detected 'owui run' command for package: {package_name}")
                if self.handle_package(package_name):
                    if self.file:
                        replacement = f"{{{{HTML_FILE_ID_{self.file}}}}}"
                        new_content = new_content.replace(match.group(0), replacement)
                        self.file = None  # Reset file ID after use
                    else:
                        print(
                            f"Error: File ID not set after handling package {package_name}"
                        )
                        replacement = f"Error: Unable to load package {package_name}"
                        new_content = new_content.replace(match.group(0), replacement)
                else:
                    print(f"Error: Failed to handle package {package_name}")
                    replacement = f"Error: Failed to load package {package_name}"
                    new_content = new_content.replace(match.group(0), replacement)

            messages[-1]["content"] = new_content
        return body
