from typing import List, Union, Generator, Iterator, Optional
from pydantic import BaseModel
import requests
import os
import json
import aiohttp
import uuid
import re
import zipfile
import io
import shutil
from utils.misc import get_last_user_message
from apps.webui.models.files import Files

from config import UPLOAD_DIR


class Filter:
    SUPPORTED_COMMANDS = ["run", "install", "uninstall", "list"]

    class Valves(BaseModel):
        open_webui_host: str = os.getenv(
            "OPEN_WEBUI_HOST", "https://localhost:3000"
        )
        openai_base_url: str = os.getenv(
            "OPENAI_BASE_URL", "http://host.docker.internal:11434/v1"
        )
        package_repo_url: str = os.getenv(
            "CEREBRO_PACKAGE_REPO_URL",
            "https://github.com/atgehrhardt/Cerebro-OpenWebUI-Package-Manager",
        )

    def __init__(self):
        self.file_handler = True
        self.valves = self.Valves()
        self.last_created_file = None
        self.selected_model = None
        self.user_id = None
        self.file = None
        self.package_files = {}
        self.pkg_launch = False
        self.installed_pkgs = []
        self.packages = []

    def create_file(
        self, package_name, file_name: str, title: str, content: str, user_id: Optional[str] = None
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

    def install_package(self, package_name: str):
        zip_url = f"{self.valves.package_repo_url}/archive/main.zip"

        if self.is_package_installed(package_name):
            print(f"Package {package_name} is already installed.")
            self.pkg_launch = "Already Installed"
            return

        try:
            # Download the zip file
            response = requests.get(zip_url)
            response.raise_for_status()
            
            # Get the repo name from the url
            repo_name = self.valves.package_repo_url.split("/")[-1]

            # Extract the specific package directory
            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
                package_dir = f"{repo_name}-main/plugins/{package_name}"
                print(f"Extracting package directory: {package_dir}...")
                for file in zip_ref.namelist():
                    if file.startswith(package_dir) and file != package_dir + "/":
                        # Extract the package files
                        print(f"Extracting {file}...")
                        zip_ref.extract(file, UPLOAD_DIR)
                        
            # Get the source directory
            src_dir = os.path.join(UPLOAD_DIR, package_dir)
            dst_dir = os.path.join(UPLOAD_DIR, "cerebro", "plugins", package_name)
            
            # Check if the source directory exists
            if not os.path.exists(src_dir):
                raise FileNotFoundError(f"Source directory not found: {src_dir}")
            
            # Create the destination directory if it doesn't exist
            os.makedirs(os.path.dirname(dst_dir), exist_ok=True)
            
            # Move the package directory to the plugins directory
            shutil.move(src_dir, dst_dir)
            
            # Remove the extracted directory
            shutil.rmtree(os.path.join(UPLOAD_DIR, f"{repo_name}-main"))
            
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
                        
                        self.package_files[filename] = created_file.id if hasattr(created_file, "id") else created_file
                    except Exception as e:
                        print(f"Error creating file: {str(e)}")
                        raise Exception(f"Error creating file: {str(e)}")
            
            # Update the contents of _capp.html file
            capp_file = os.path.join(dst_dir, f"{package_name}_capp.html")
            with open(capp_file, "r", encoding="utf-8") as f:
                capp_content = f.read()
                for filename, file_id in self.package_files.items():
                    # Replace the filename with the file content url
                    capp_content = capp_content.replace("{"+filename+"}", self.get_file_url(file_id))
                # Update the content of the _capp.html file
                with open(capp_file, "w", encoding="utf-8") as f:
                    f.write(capp_content)
            
            print(f"Package {package_name} installed successfully.")
            self.pkg_launch = "Installed"

        except Exception as e:
            print(f"Error installing package {package_name}: {str(e)}")
            raise Exception(f"Error installing package {package_name}: {str(e)}")

    def uninstall_package(self, package_name: str):
        package_dir = os.path.join(UPLOAD_DIR, "cerebro", "plugins", package_name)
        if not os.path.exists(package_dir):
            print(f"Package {package_name} does not exist.")
            return

        try:
            for root, dirs, files in os.walk(package_dir, topdown=False):
                for file in files:
                    os.remove(os.path.join(root, file))
                for dir in dirs:
                    os.rmdir(os.path.join(root, dir))
            os.rmdir(package_dir)

            # Remove the file from the database
            files = Files.get_files()
            files = [file for file in files if file.user_id == self.user_id]
            files = [
                file for file in files if f"{package_name}_capp.html" in file.filename
            ]
            if files:
                Files.delete_file_by_id(files[0].id)

            print(f"Package {package_name} uninstalled successfully.")
            self.pkg_launch = "Uninstalled"
        except Exception as e:
            raise Exception(f"Error deleting package {package_name}: {str(e)}")

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
            print(f"Last message: {last_message}")

            if last_message.startswith("owui "):
                command_parts = last_message.split()
                if len(command_parts) >= 2:
                    command = command_parts[1]
                    if command not in self.SUPPORTED_COMMANDS:
                        self.pkg_launch = "invalid"
                        return body

                if last_message.startswith("owui run"):
                    command_parts = last_message.split()
                    print(f"Command parts: {command_parts}")
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
                            return body

                        self.handle_package(package_name, url, file_name)
                        self.pkg_launch = True
                        return body

                elif last_message.startswith("owui install"):
                    command_parts = last_message.split()
                    print(f"Command parts: {command_parts}")
                    if len(command_parts) >= 3:
                        package_name = command_parts[2]
                        print(f"Installing package: {package_name}")
                        self.install_package(package_name)
                        return body

                elif last_message.startswith("owui uninstall"):
                    command_parts = last_message.split()
                    print(f"Command parts: {command_parts}")
                    if len(command_parts) >= 3:
                        package_name = " ".join(command_parts[2:])
                        print(f"Uninstalling package: {package_name}")
                        self.uninstall_package(package_name)
                        return body

                elif last_message.startswith("owui list"):
                    self.list_packages(body)
                    print(f"\n\n\nReturning body: {body}\n\n\n")
                    return body
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

        return body
