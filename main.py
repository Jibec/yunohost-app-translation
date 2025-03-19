import json
import os
import subprocess
import tempfile

import requests

URL_APPS_JSON = "https://apps.yunohost.org/default/v3/apps.json"
LOCAL_SRC = "src"
local_filename = "apps.json"

PO4A_CONFIG = "[po4a_langs] fr \n[po4a_paths] translation_files/$master/$master.pot $lang:translation_files/$master/$lang.po\n"

def download_file(url, local_filename):
    response = requests.get(url)
    response.raise_for_status()  # Check if the request was successful
    with open(local_filename, 'wb') as file:
        file.write(response.content)


def add_to_po4a_config(post_upgrade_md_file, app):
    global PO4A_CONFIG
    PO4A_CONFIG += f"[type: text] {post_upgrade_md_file} $lang:translated/$lang/{post_upgrade_md_file} opt:\"--keep 0\" pot={app} \n"


def parse_and_clone_apps(local_filename):
    with open(local_filename, 'r') as file:
        data = json.load(file)

    apps = list(data.get("apps", []).items())[:10]
    total_apps = len(apps)
    for index, (app_name, app) in enumerate(apps, start=1):
        print(f"Processing {index}/{total_apps}: {app_name}")
        git_url = app.get("git", {}).get("url")
        admin_md, description_md, post_upgrade_md = clone_repo(git_url)
        if admin_md is not None:
            admin_md_file = os.path.join(LOCAL_SRC, app_name, "ADMIN.md")
            save_file(admin_md_file, admin_md)
            add_to_po4a_config(admin_md_file, app_name)
        if description_md is not None:
            description_md_file = os.path.join(LOCAL_SRC, app_name, "DESCRIPTION.md")
            save_file(description_md_file, description_md)
            add_to_po4a_config(description_md_file, app_name)
        if post_upgrade_md is not None:
            post_upgrade_md_file = os.path.join(LOCAL_SRC, app_name, "POST_UPGRADE.md")
            save_file(post_upgrade_md_file, post_upgrade_md)
            add_to_po4a_config(post_upgrade_md_file, app_name)

    global PO4A_CONFIG
    save_file(os.path.join("./","po4a.cfg"), PO4A_CONFIG)


def clone_repo(git_url):
    with tempfile.TemporaryDirectory() as temp_dir:
        subprocess.run(["git", "clone", "--depth", "1", git_url, temp_dir], check=True)

        admin_md = read_file_if_exists(os.path.join(temp_dir, "doc", "ADMIN.md"))
        description_md = read_file_if_exists(os.path.join(temp_dir, "doc", "DESCRIPTION.md"))
        post_upgrade_md = read_file_if_exists(os.path.join(temp_dir, "doc", "POST_UPGRADE.md"))

        return admin_md, description_md, post_upgrade_md

def read_file_if_exists(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return file.read()
    return None

def save_file(file_path, content):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as file:
        file.write(content)

if __name__ == "__main__":
    print("Start processing...")
    print("Downloading apps.json")
    download_file(URL_APPS_JSON, local_filename)
    print(f"Downloaded {URL_APPS_JSON} and saved as {local_filename}")
    parse_and_clone_apps(local_filename)
    print("🕊 Done 🕊")