"""
Plugin Registry Script

This script should be placed in a PRIVATE repository.
It fetches pluginspec.yml from the public plugin repository
and registers only new/updated plugins to the backend API.
"""

import os
import json
import urllib.request

import urllib.error
from pathlib import Path

import yaml

CONFIG = {
    "pluginRepo": {
        "owner": os.environ.get("PLUGIN_REPO_OWNER", "your-org"),
        "repo": os.environ.get("PLUGIN_REPO_NAME", "simple_chat_example_plugins"),
        "branch": os.environ.get("PLUGIN_REPO_BRANCH", "examples"),
        "specFile": "pluginspec.yml",
    },
    "api": {
        "url": os.environ.get("API_URL"),
    },
    "stateFile": Path(__file__).parent.parent / ".plugin-state.json",
}


def load_state():
    try:
        if CONFIG["stateFile"].exists():
            return json.loads(CONFIG["stateFile"].read_text(encoding="utf-8"))
    except Exception:
        print("⚠ Could not load state file, starting fresh")
    return {"plugins": {}}


def save_state(state):
    CONFIG["stateFile"].write_text(
        json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def fetch_raw_file(owner, repo, branch, file_path):
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{file_path}"
    print(f"📥 Fetching: {url}")

    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        return response.read().decode("utf-8")


def get_plugin_hash(plugin):
    return (
        f"{plugin['name']}|{plugin['version']}|{plugin['url']}|{plugin['description']}|{plugin.get('author', '')}"
    )


def register_plugin(plugin):
    api_url = CONFIG["api"]["url"]

    post_data = json.dumps(
        {
            "name": plugin["name"],
            "version": str(plugin["version"]),
            "url": plugin["url"],
            "description": plugin["description"],
            "author": plugin.get("author", "Unknown"),
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

    if not CONFIG["api"]["url"]:
        print("Missing required environment variable: API_URL")
        exit(1)

    # Load previous state
    state = load_state()
    print(f"📂 Loaded state: {len(state['plugins'])} plugin(s) tracked\n")

    try:
        # Fetch pluginspec.yml from public repo
        spec_content = fetch_raw_file(
            CONFIG["pluginRepo"]["owner"],
            CONFIG["pluginRepo"]["repo"],
            CONFIG["pluginRepo"]["branch"],
            CONFIG["pluginRepo"]["specFile"],
        )

        spec = yaml.safe_load(spec_content)
        print(f"✓ Found {len(spec['plugins'])} plugin(s) in spec\n")

        # Check for new/updated plugins
        plugins_to_register = []

        for plugin in spec["plugins"]:
            hash_val = get_plugin_hash(plugin)
            previous_hash = state["plugins"].get(plugin["name"])

            if previous_hash == hash_val:
                print(f"⏭ Skipping {plugin['name']} (unchanged)")
            else:
                print(f"🆕 Detected change: {plugin['name']}")
                plugins_to_register.append(plugin)

        if not plugins_to_register:
            print("\n✅ No changes detected. Nothing to register.")
            return

        print(f"\n→ Registering {len(plugins_to_register)} plugin(s)...\n")

        # Register changed plugins
        success_count = 0
        fail_count = 0

        for plugin in plugins_to_register:
            print(f"→ Registering: {plugin['name']} v{plugin['version']}")

            try:
                result = register_plugin(plugin)

                if result["success"]:
                    print(f"  Registered ({result['statusCode']})")
                    state["plugins"][plugin["name"]] = get_plugin_hash(plugin)
                    success_count += 1
                else:
                    print(f"  Failed ({result['statusCode']}): {result['data']}")
                    fail_count += 1
            except Exception as err:
                print(f"  Error: {err}")
                fail_count += 1

        # Save updated state
        save_state(state)
        print("\n💾 State saved")

        # Summary
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
