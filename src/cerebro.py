"""
title: Cerebro Package Manager
author: Andrew Tait Gehrhardt
author_url: https://github.com/atgehrhardt/Cerebro-OpenWebUI-Package-Manager
funding_url: https://github.com/open-webui
version: 0.2.1

! ! ! 
IMPORTANT: THIS MUST BE THE SECOND TO LAST PRIORITY IN YOUR CHAIN. SET PRIORITY HIGHER THAN ALL 
           OTHER FUNCTIONS EXCEPT FOR THE CEREBRO TOOL LAUNCHER 
! ! !

Commands:
`owui list` - List installed packages
`owui install package_name` - Installs a package
`owui uninstall package_name` - Uninstalls a package
`owui update package_name` - Updates a package (uninstalls then reinstalls)
`owui run package_name` - Runs an installed package in the chat window

You can view all current package available for installation here: https://github.com/atgehrhardt/Cerebro-OpenWebUI-Package-Manager/tree/main/plugins
"""

from typing import List, Union, Generator, Iterator, Optional
from pydantic import BaseModel, Field
import requests
import os
import json
import aiohttp
import uuid
import re
import zipfile
import io
import shutil
from urllib.parse import urlparse, urlunparse
from utils.misc import get_last_user_message
from apps.webui.models.files import Files
from apps.webui.models.tools import Tools, ToolForm, ToolMeta

from config import UPLOAD_DIR


class Filter:
    SUPPORTED_COMMANDS = ["run", "install", "uninstall", "list", "update"]

    class Valves(BaseModel):
        priority: int = Field(
            default=1, description="Priority level for the filter operations."
        )
        open_webui_host: str = os.getenv(
            "OPEN_WEBUI_HOST",
            "https://192.168.1.154",  # If using Nginx this MUST be your server ip address https://192.168.1.xxx
        )
        openai_base_url: str = os.getenv(
            "OPENAI_BASE_URL", "http://host.docker.internal:11434/v1"
        )
        package_repo_url: str = os.getenv(
            "CEREBRO_PACKAGE_REPO_URL",
            "https://github.com/atgehrhardt/Cerebro-OpenWebUI-Package-Manager/tree/main/plugins",
        )

    def __init__(self):
        self.valves = self.Valves()
        self.last_created_file = None
        self.selected_model = None
        self.user_id = None
        self.file = None
        self.package_files = {}
        self.pkg_launch = False
        self.installed_pkgs = []
        self.packages = []

    def check_tool_exists(self, tool_name: str) -> bool:
        tool_file = os.path.join(
            UPLOAD_DIR, "cerebro", "plugins", tool_name, f"{tool_name}_capp.py"
        )
        return os.path.exists(tool_file)

    def uninstall_tool(self, tool_name: str):
        if not self.check_tool_exists(tool_name):
            print(f"Tool {tool_name} does not exist.")
            return

        try:
            # Get the tool by name
            tools = Tools.get_tools()
            tool = next((t for t in tools if t.name == tool_name), None)

            if tool:
                # Delete the tool from the database
                if Tools.delete_tool_by_id(tool.id):
                    print(
                        f"Tool {tool_name} uninstalled successfully from the database."
                    )
                else:
                    print(f"Failed to uninstall tool {tool_name} from the database.")
            else:
                print(f"Tool {tool_name} not found in the database.")

            # Remove the tool file
            tool_file = os.path.join(
                UPLOAD_DIR, "cerebro", "plugins", tool_name, f"{tool_name}_capp.py"
            )
            if os.path.exists(tool_file):
                os.remove(tool_file)
                print(f"Removed tool file: {tool_file}")

            self.pkg_launch = "Tool Uninstalled"
        except Exception as e:
            raise Exception(f"Error uninstalling tool {tool_name}: {str(e)}")

    def update_tool(self, tool_name: str):
        if not self.check_tool_exists(tool_name):
            print(f"Tool {tool_name} does not exist. Cannot update.")
            self.pkg_launch = "Tool Not Installed"
            return

        print(f"Updating tool {tool_name}...")
        try:
            # Uninstall the tool
            self.uninstall_tool(tool_name)

            # Install the tool again
            self.install_package(tool_name)  # This will install both package and tool

            print(f"Tool {tool_name} updated successfully.")
            self.pkg_launch = "Tool Updated"
        except Exception as e:
            print(f"Error updating tool {tool_name}: {str(e)}")
            self.pkg_launch = "Tool Update Failed"
            raise Exception(f"Error updating tool {tool_name}: {str(e)}")

    def create_file(
        self,
        package_name,
        file_name: str,
        title: str,
        content: str,
        user_id: Optional[str] = None,
    ):
        user_id = user_id or self.user_id

        if not user_id:
            raise ValueError("User ID is required to create a file.")

        base_path = os.path.join(UPLOAD_DIR, "cerebro", "plugins", package_name)
        os.makedirs(base_path, exist_ok=True)

        file_id = str(uuid.uuid4())
        file_path = os.path.join(base_path, file_name)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                print(f"Writing file to {file_path}...")
                f.write(content)
        except IOError as e:
            raise IOError(f"Error writing file to {file_path}: {str(e)}")

        try:
            meta = {
                "source": file_path,
                "title": title,
                "content_type": "text/html",
                "size": os.path.getsize(file_path),
                "path": file_path,
            }
        except FileNotFoundError as e:
            raise FileNotFoundError(f"File {file_path} not found: {str(e)}")

        class FileForm(BaseModel):
            id: str
            filename: str
            meta: dict = {}

        form_data = FileForm(id=file_id, filename=file_name, meta=meta)

        try:
            self.file = Files.insert_new_file(user_id, form_data)
            self.last_created_file = self.file
            return self.file
        except Exception as e:
            os.remove(file_path)
            raise Exception(f"Error inserting file into database: {str(e)}")

    def get_file_url(self, file_id: str) -> str:
        return f"{self.valves.open_webui_host}/api/v1/files/{file_id}/content"

    def handle_package(self, package_name, url: str, file_name: str):
        files = Files.get_files()
        files = [file for file in files if file.user_id == self.user_id]
        files = [file for file in files if file_name in file.filename]
        print("Files: ", files)

        if files:
            self.file = files[0].id
            print(f"\n{self.file}\n")
            print("File already exists")
        else:
            if not url:
                print("No URL provided, cannot download the file.")
                return

            try:
                print(f"Downloading the file from {url}...\n")
                response = requests.get(url)
                response.raise_for_status()
                file_content = response.text
                print("Downloaded file content:")
                print(file_content)
            except Exception as e:
                raise Exception(f"Error downloading {file_name}: {str(e)}")

            try:
                if not self.user_id:
                    raise ValueError("User ID is not set. Cannot create file.")
                created_file = self.create_file(
                    package_name, file_name, file_name, file_content, self.user_id
                )
                self.file = (
                    created_file.id if hasattr(created_file, "id") else created_file
                )
            except Exception as e:
                print(f"Error creating file: {str(e)}")
                raise Exception(f"Error creating file: {str(e)}")

        return self.file

    def is_package_installed(self, package_name: str) -> bool:
        package_dir = os.path.join(UPLOAD_DIR, "cerebro", "plugins", package_name)
        return os.path.exists(package_dir)

    def get_zip_url_from_tree_url(self, tree_url: str) -> str:
        parsed_url = urlparse(tree_url)
        path_parts = parsed_url.path.split("/")

        if "tree" in path_parts:
            tree_index = path_parts.index("tree")
            repo_path = "/".join(path_parts[:tree_index])
            branch = path_parts[tree_index + 1]

            # Construct the raw zip URL
            zip_path = f"{repo_path}/archive/{branch}.zip"
            return urlunparse(parsed_url._replace(path=zip_path))
        else:
            # If 'tree' is not in the URL, assume it's the main branch
            return f"{tree_url}/archive/main.zip"

    def get_subdirectory_from_tree_url(self, tree_url: str) -> str:
        parsed_url = urlparse(tree_url)
        path_parts = parsed_url.path.split("/")

        if "tree" in path_parts:
            tree_index = path_parts.index("tree")
            return "/".join(path_parts[tree_index + 2 :])
        else:
            return ""

    def install_package(self, package_name: str):
        tree_url = self.valves.package_repo_url
        zip_url = self.get_zip_url_from_tree_url(tree_url)
        subdirectory = self.get_subdirectory_from_tree_url(tree_url)

        print(f"Tree URL: {tree_url}")
        print(f"Zip URL: {zip_url}")
        print(f"Subdirectory: {subdirectory}")

        if self.is_package_installed(package_name):
            print(f"Package {package_name} is already installed.")
            self.pkg_launch = "Already Installed"
            return

        try:
            # Download the zip file
            print(f"Downloading zip file from: {zip_url}")
            response = requests.get(zip_url)
            response.raise_for_status()

            # Get the repo name and branch from the url
            repo_name = tree_url.split("/")[-4]
            branch = tree_url.split("/")[-2]

            # Extract the specific package directory
            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
                all_files = zip_ref.namelist()
                print(f"Files in zip: {all_files}")

                # Try to find the package directory
                package_dir = None
                for file in all_files:
                    if file.endswith(
                        f"{subdirectory}/{package_name}/"
                    ) or file.endswith(f"{subdirectory}/{package_name}"):
                        package_dir = file
                        break

                if not package_dir:
                    raise FileNotFoundError(
                        f"Package directory for {package_name} not found in zip file"
                    )

                print(f"Found package directory: {package_dir}")

                # Extract the package files
                for file in all_files:
                    if file.startswith(package_dir):
                        print(f"Extracting {file}...")
                        zip_ref.extract(file, UPLOAD_DIR)

            # Get the source directory
            src_dir = os.path.join(UPLOAD_DIR, package_dir)
            dst_dir = os.path.join(UPLOAD_DIR, "cerebro", "plugins", package_name)

            print(f"Source directory: {src_dir}")
            print(f"Destination directory: {dst_dir}")

            # Check if the source directory exists
            if not os.path.exists(src_dir):
                raise FileNotFoundError(f"Source directory not found: {src_dir}")

            # Create the destination directory if it doesn't exist
            os.makedirs(os.path.dirname(dst_dir), exist_ok=True)

            # Move the package directory to the plugins directory
            shutil.move(src_dir, dst_dir)

            # Remove the extracted directory
            extracted_dir = os.path.join(UPLOAD_DIR, f"{repo_name}-{branch}")
            shutil.rmtree(extracted_dir)

            # Loop through all the files in the package directory and create them in the database
            for root, dirs, files in os.walk(dst_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    print(f"Creating file: {file_path}")

                    # Get the content of each file
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            file_content = f.read()

                        filename = os.path.basename(file_path)
                        # Create file in the database
                        created_file = self.create_file(
                            package_name,
                            f"{file_path}",
                            f"{file_path}",
                            file_content,
                            self.user_id,
                        )

                        self.package_files[filename] = (
                            created_file.id
                            if hasattr(created_file, "id")
                            else created_file
                        )
                    except Exception as e:
                        print(f"Error creating file: {str(e)}")
                        raise Exception(f"Error creating file: {str(e)}")

            # Update the contents of _capp.html file
            capp_file = os.path.join(dst_dir, f"{package_name}_capp.html")
            if os.path.exists(capp_file):
                with open(capp_file, "r", encoding="utf-8") as f:
                    capp_content = f.read()
                    for filename, file_id in self.package_files.items():
                        # Replace the filename with the file content url
                        capp_content = capp_content.replace(
                            "{" + filename + "}", self.get_file_url(file_id)
                        )
                # Update the content of the _capp.html file
                with open(capp_file, "w", encoding="utf-8") as f:
                    f.write(capp_content)
            else:
                print(f"Warning: {capp_file} not found. Skipping content update.")

            # Check for and install tool
            tool_file = os.path.join(dst_dir, f"{package_name}_capp.py")
            if os.path.exists(tool_file):
                print(f"Installing tool for package: {package_name}")
                with open(tool_file, "r", encoding="utf-8") as f:
                    tool_content = f.read()

                # Prepend "cer_" to the tool name
                cer_tool_name = f"cer_{package_name}"

                # Extract the description from the tool content
                description = "Tool for " + package_name  # Default description
                doc_string = self.extract_class_docstring(tool_content)
                if doc_string:
                    description = doc_string.strip()

                # Create a ToolForm instance with the modified name and description
                tool_form = ToolForm(
                    id=str(uuid.uuid4()),
                    name=cer_tool_name,
                    content=tool_content,
                    meta=ToolMeta(description=description),
                )

                # Insert the tool
                tool = Tools.insert_new_tool(self.user_id, tool_form, [])
                if tool:
                    print(
                        f"Tool for package {package_name} installed successfully as {cer_tool_name} with description: {description}"
                    )
                else:
                    print(f"Failed to install tool for package {package_name}.")

            print(f"Package {package_name} installed successfully.")
            self.pkg_launch = "Installed"

        except Exception as e:
            print(f"Error installing package {package_name}: {str(e)}")
            raise Exception(f"Error installing package {package_name}: {str(e)}")

    def extract_class_docstring(self, content: str) -> Optional[str]:
        """
        Extract the docstring of the first class in the given content.
        """
        import ast

        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    docstring = ast.get_docstring(node)
                    if docstring:
                        return docstring
        except SyntaxError:
            print("Failed to parse the tool content")
        return None

    def update_package(self, package_name: str):
        if not self.is_package_installed(package_name):
            print(f"Package {package_name} is not installed. Cannot update.")
            self.pkg_launch = "Not Installed"
            return

        print(f"Updating package {package_name}...")
        try:
            # Uninstall the package (which will also uninstall the tool)
            self.uninstall_package(package_name)

            # Install the package again (which will also install the tool)
            self.install_package(package_name)

            print(f"Package {package_name} updated successfully.")
            self.pkg_launch = "Updated"
        except Exception as e:
            print(f"Error updating package {package_name}: {str(e)}")
            self.pkg_launch = "Update Failed"
            raise Exception(f"Error updating package {package_name}: {str(e)}")

    def uninstall_package(self, package_name: str):
        package_dir = os.path.join(UPLOAD_DIR, "cerebro", "plugins", package_name)
        if not os.path.exists(package_dir):
            print(f"Package {package_name} does not exist.")
            return

        try:
            # Get all files
            all_files = Files.get_files()

            # Filter files related to the package
            files_to_delete = [
                file
                for file in all_files
                if file.user_id == self.user_id
                and f"/cerebro/plugins/{package_name}/" in file.filename
            ]

            # Delete files from the database
            deleted_count = 0
            for file in files_to_delete:
                if Files.delete_file_by_id(file.id):
                    deleted_count += 1
                print(f"Deleted file: {file.filename}")

            print(f"Deleted {deleted_count} files from the database.")

            # Remove files and directories from the file system
            if os.path.exists(package_dir):
                shutil.rmtree(package_dir)
                print(f"Removed package directory: {package_dir}")
            else:
                print(f"Package directory {package_dir} does not exist.")

            # Uninstall tool
            tools = Tools.get_tools()
            tool_name = (
                f"cer_{package_name}"  # Look for the tool with the "cer_" prefix
            )
            tool = next((t for t in tools if t.name == tool_name), None)

            if tool:
                if Tools.delete_tool_by_id(tool.id):
                    print(
                        f"Tool {tool_name} for package {package_name} uninstalled successfully."
                    )
                else:
                    print(
                        f"Failed to uninstall tool {tool_name} for package {package_name}."
                    )
            else:
                print(
                    f"No tool found with name {tool_name} for package {package_name}."
                )

            print(f"Package {package_name} uninstalled successfully.")
            self.pkg_launch = "Uninstalled"
        except Exception as e:
            raise Exception(f"Error uninstalling package {package_name}: {str(e)}")

    def list_packages(self, body: dict) -> List[str]:
        if not self.user_id:
            print("User ID is not set. Cannot list packages.")
            return []

        plugins_dir = os.path.join(UPLOAD_DIR, "cerebro", "plugins")
        if not os.path.exists(plugins_dir):
            print("Plugins directory does not exist.")
            return []

        self.packages = [
            d
            for d in os.listdir(plugins_dir)
            if os.path.isdir(os.path.join(plugins_dir, d))
        ]

        # Update installed packages based on both directory existence and database entries
        all_files = Files.get_files()
        db_packages = set(
            [
                file.filename.split("/cerebro/plugins/")[1].split("/")[0]
                for file in all_files
                if file.user_id == self.user_id and "/cerebro/plugins/" in file.filename
            ]
        )

        self.installed_pkgs = list(set(self.packages) | db_packages)

        print(f"\n\n\nPackages list: {self.installed_pkgs}\n\n\n")

        self.pkg_launch = "list"
        return self.installed_pkgs

    def list_packages(self, body: dict) -> List[str]:
        if not self.user_id:
            print("User ID is not set. Cannot list packages.")
            return []

        plugins_dir = os.path.join(UPLOAD_DIR, "cerebro", "plugins")
        if not os.path.exists(plugins_dir):
            print("Plugins directory does not exist.")
            return []

        self.packages = [
            d
            for d in os.listdir(plugins_dir)
            if os.path.isdir(os.path.join(plugins_dir, d))
        ]
        print(f"\n\n\nPackages list: {self.packages}\n\n\n")

        self.pkg_launch = "list"
        self.installed_pkgs = self.packages
        return self.packages

    def check_package_exists(self, package_name: str) -> bool:
        package_dir = os.path.join(
            UPLOAD_DIR, "cerebro", "plugins", package_name.replace("_capp.html", "")
        )
        return os.path.exists(package_dir)

    def inlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        print(f"inlet:{__name__}")
        print(f"inlet:body:{body}")
        print(f"inlet:user:{__user__}")

        if __user__ and "id" in __user__:
            self.user_id = __user__["id"]
        else:
            print("Warning: No valid user ID provided")

        messages = body.get("messages", [])
        if messages:
            last_message = messages[-1]["content"]

            if last_message.startswith("owui "):
                command_parts = last_message.split()
                if len(command_parts) >= 2:
                    command = command_parts[1]
                    if command not in self.SUPPORTED_COMMANDS:
                        self.pkg_launch = "invalid"

                if last_message.startswith("owui run"):
                    command_parts = last_message.split()
                    if len(command_parts) >= 3:
                        _, _, package_name = command_parts[:3]
                        url = (
                            " ".join(command_parts[3:])
                            if len(command_parts) > 3
                            else None
                        )
                        file_name = f"{package_name}_capp.html"
                        print(
                            f"Running command with file name: {file_name} and URL: {url}"
                        )

                        if not self.check_package_exists(file_name):
                            self.pkg_launch = "none"

                        self.handle_package(package_name, url, file_name)
                        self.pkg_launch = True

                elif last_message.startswith("owui install"):
                    command_parts = last_message.split()
                    if len(command_parts) >= 3:
                        package_name = command_parts[2]
                        print(f"Installing package: {package_name}")
                        self.install_package(package_name)

                elif last_message.startswith("owui uninstall"):
                    command_parts = last_message.split()
                    if len(command_parts) >= 3:
                        package_name = " ".join(command_parts[2:])
                        print(f"Uninstalling package: {package_name}")
                        self.uninstall_package(package_name)

                elif last_message.startswith("owui list"):
                    self.list_packages(body)

                elif last_message.startswith("owui update"):
                    command_parts = last_message.split()
                    if len(command_parts) >= 3:
                        package_name = " ".join(command_parts[2:])
                        print(f"Updating package: {package_name}")
                        self.update_package(package_name)

        return body

    def outlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        print(f"outlet:{__name__}")
        print(f"outlet:body:{body}")
        print(f"outlet:user:{__user__}")

        if self.pkg_launch is True:
            if self.file:
                body["messages"][-1]["content"] = f"{{{{HTML_FILE_ID_{self.file}}}}}"
            else:
                print("Error: File ID not set after handling package")
                body["messages"][-1]["content"] = "Error: Unable to load package"
        elif self.pkg_launch == "Installed":
            body["messages"][-1]["content"] = "Package Installed"
        elif self.pkg_launch == "Already Installed":
            body["messages"][-1]["content"] = "Package Already Installed"
        elif self.pkg_launch == "Uninstalled":
            body["messages"][-1]["content"] = "Package Uninstalled"
        elif self.pkg_launch == "Updated":
            body["messages"][-1]["content"] = "Package Updated Successfully"
        elif self.pkg_launch == "Update Failed":
            body["messages"][-1]["content"] = "Package Update Failed"
        elif self.pkg_launch == "Not Installed":
            body["messages"][-1]["content"] = "Package Not Installed. Cannot Update."
        elif self.pkg_launch == "list":
            body["messages"][-1]["content"] = (
                "--- INSTALLED PACKAGES--- \n" + "\n".join(self.installed_pkgs)
            )
        elif self.pkg_launch == "none":
            body["messages"][-1]["content"] = "Package Not installed"
        elif self.pkg_launch == "invalid":
            body["messages"][-1][
                "content"
            ] = f"Invalid command. Supported commands are: {', '.join(self.SUPPORTED_COMMANDS)}"
        else:
            pass

        self.pkg_launch = False

        print("\n\n\n")
        return body
