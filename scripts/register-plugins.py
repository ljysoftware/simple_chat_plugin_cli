"""
Plugin Registry Script

This script should be placed in a PRIVATE repository.
It fetches pluginspec.yml from the public plugin repository
and registers only new/updated plugins to the backend API.
"""

import os
import json
import urllib.request
from typing import TypedDict

import urllib.error

import yaml

CONFIG = {
    "pluginRepo": {
        "owner": os.environ.get("PLUGIN_REPO_OWNER"),
        "repo": os.environ.get("PLUGIN_REPO_NAME"),
        "branch": os.environ.get("PLUGIN_REPO_BRANCH"),
    },
    "api": {
        "url": os.environ.get("API_URL"),
    },
}

REQUIRED_ENV_VARS = ["PLUGIN_REPO_OWNER", "PLUGIN_REPO_NAME", "PLUGIN_REPO_BRANCH"]

def validate_config():
    missing = [var for var in REQUIRED_ENV_VARS if not os.environ.get(var)]
    if missing:
        print(f"Missing required environment variables: {', '.join(missing)}")
        exit(1)

GITHUB_URL = f"https://raw.githubusercontent.com/{CONFIG['pluginRepo']["owner"]}/{CONFIG['pluginRepo']["repo"]}/{CONFIG['pluginRepo']["branch"]}"
URL = f"{GITHUB_URL}/pluginspec.yml"
class PluginSpec(TypedDict):
    name: str
    version: str
    assets: list[str]
    description: str

class PluginSpecs(TypedDict):
    plugins: list[PluginSpec]

def fetch_spec_file():
    print(f"📥 Fetching Plugin Spec: {URL}")

    req = urllib.request.Request(URL)
    with urllib.request.urlopen(req) as response:
        return response.read().decode("utf-8")


def get_plugin_hash(plugin):
    return (
        f"{plugin['name']}|{plugin['version']}|{plugin['url']}|{plugin['description']}|{plugin.get('author', '')}"
    )


def register_plugin(plugin: PluginSpec):
    api_url = CONFIG["api"]["url"]

    post_data = json.dumps(
        {
            "name": plugin["name"],
            "version": plugin["version"],
            "assets": plugin["assets"],
            "description": plugin["description"],
            "url": GITHUB_URL,
            "author": CONFIG["pluginRepo"]["owner"],
        }
    ).encode("utf-8")
    
    headers = {
        "Content-Type": "application/json",
    }

    req = urllib.request.Request(
        api_url, data=post_data, headers=headers, method="POST"
    )

    try:
        with urllib.request.urlopen(req) as response:
            return {
                "success": True,
                "data": response.read().decode("utf-8"),
                "statusCode": response.status,
            }
    except urllib.error.HTTPError as e:
        return {
            "success": False,
            "data": e.read().decode("utf-8"),
            "statusCode": e.code,
        }


def main():
    print("🚀 Plugin Registration Started")
    print("=" * 40)

    # if not CONFIG["api"]["url"]:
    #     print("Missing required environment variable: API_URL")
    #     exit(1)

    # Load previous state

    try:
        # Fetch pluginspec.yml from public repo
        plugin_spec = fetch_spec_file()

        spec: PluginSpecs = yaml.safe_load(plugin_spec)

        print(f"✓ Found {len(spec['plugins'])} plugin(s) in spec\n")

        success_count = 0
        fail_count = 0


        for plugin in spec["plugins"]:
            try:
                result = register_plugin(plugin)

                if result["success"]:
                    print(f"  Registered ({result['statusCode']})")
                    success_count += 1
                else:
                    print(f"  Failed ({result['statusCode']}): {result['data']}")
                    fail_count += 1
            except Exception as err:
                print(f"  Error: {err}")
                fail_count += 1

        print("\n" + "=" * 40)
        print(f"✅ Success: {success_count}")
        print(f"❌ Failed: {fail_count}")

        if fail_count > 0:
            exit(1)

    except Exception as err:
        print(f"❌ Fatal error: {err}")
        exit(1)


if __name__ == "__main__":
    main()
