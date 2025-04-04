import json
import os
import subprocess
import tempfile

import requests

URL_APPS_JSON = "https://apps.yunohost.org/default/v3/apps.json"
LOCAL_SRC = "src"
APPS_JSON = "apps.json"

PO4A_CONFIG = """[po4a_alias:markdown] text opt:\"--option markdown\"
[po4a_langs] fr
[po4a_paths] translation_files/$master/$master.pot $lang:translation_files/$master/$lang.po
"""

def download_file(url, local_filename):
    response = requests.get(url)
    response.raise_for_status()  # Check if the request was successful
    with open(local_filename, 'wb') as file:
        file.write(response.content)


def add_to_po4a_config(post_upgrade_md_file, app):
    global PO4A_CONFIG
    PO4A_CONFIG += f"[type: markdown] {post_upgrade_md_file} $lang:translated/$lang/{post_upgrade_md_file} opt:\"--keep 0\" pot={app} \n"


def parse_and_clone_apps():
    """
    Parse the apps.json file and clone the git repositories of the apps.
    :return:
    """
    with open(APPS_JSON, 'r') as file:
        data = json.load(file)

    apps = list(data.get("apps", []).items())
    total_apps = len(apps)
    for index, (app_name, app) in enumerate(apps, start=1):
        print(f"Processing {index}/{total_apps}: {app_name}")
        git_url = app.get("git", {}).get("url")

        files = ["ADMIN.md", "DESCRIPTION.md", "POST_UPGRADE.md", "PRE_INSTALL.md"]

        found = get_files_to_translate_from_app_repo(git_url, files)

        for file, content in found.items():
            if content is not None:
                admin_md_file = os.path.join(LOCAL_SRC, app_name, file)
                save_file(admin_md_file, content)
                add_to_po4a_config(admin_md_file, app_name)

    global PO4A_CONFIG
    save_file(os.path.join("./","po4a.cfg"), PO4A_CONFIG)


def get_files_to_translate_from_app_repo(git_url: str, files: list):
    """
    Clone a git repository and check for the existence of specific files.

    :param git_url: URL of the git repository
    :param files: list of files to check for existence
    :return: dict with file names as keys and their contents as values
    """
    found = {}
    with tempfile.TemporaryDirectory() as temp_dir:
        subprocess.run(["git", "clone", "--depth", "1", git_url, temp_dir], check=True)
        for file in files:
            found[file] = read_file_if_exists(os.path.join(temp_dir, "doc", file))

    return found

def read_file_if_exists(file_path: str):
    """
    Check if a file exists and read its content.
    :param file_path: Path to the file
    :return: File content if it exists, None otherwise
    """
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return file.read()
    return None

def save_file(file_path: str, content: str):
    """
    Save content to a file, creating directories if necessary.
    :param file_path: File path to save the content
    :param content: Content to save
    :return: None
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as file:
        file.write(content)

if __name__ == "__main__":
    print("Start processing...")
    print("Downloading apps.json")
    download_file(URL_APPS_JSON, APPS_JSON)
    print(f"Downloaded {URL_APPS_JSON} and saved as {APPS_JSON}")
    parse_and_clone_apps()
    print("🕊 Done 🕊")