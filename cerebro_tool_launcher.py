"""
title: Cerebro Tool Launcher
author: Andrew Tait Gehrhardt
author_url: https://github.com/atgehrhardt
funding_url: https://github.com/open-webui
version: 0.1.0
"""

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
            owui_run_match = re.search(r"owui run (\w+)", last_message)
            if owui_run_match:
                package_name = owui_run_match.group(1)
                print(f"Detected 'owui run' command for package: {package_name}")
                if self.handle_package(package_name):
                    if self.file:
                        messages[-1]["content"] = f"{{{{HTML_FILE_ID_{self.file}}}}}"
                    else:
                        print(
                            f"Error: File ID not set after handling package {package_name}"
                        )
                        messages[-1][
                            "content"
                        ] = f"Error: Unable to load package {package_name}"
                else:
                    print(f"Error: Failed to handle package {package_name}")
                    messages[-1][
                        "content"
                    ] = f"Error: Failed to load package {package_name}"
        return body