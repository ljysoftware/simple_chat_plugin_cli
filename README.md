# Simple Chat Plugin CLI

A command-line tool for registering plugins to the Simple Chat Plugin Server.

## Overview

This CLI provides a registration script that plugin developers can integrate into their own CI/CD pipelines. It:

1. Fetches `pluginspec.yml` from your plugin repository (via GitHub raw URL)
2. Parses plugin metadata (name, version, assets, description)
3. Registers each plugin to the Simple Chat Plugin Server

**Note**: This CLI is a tool you integrate into your workflow. How you design your pipeline (triggers, branches, etc.) is up to you.

## Quick Start Guide

### Step 1: Create Your Plugin Repository

Create a public GitHub repository for your plugins:

```
your-plugin-repo/
├── pluginspec.yml              # Required: Plugin specification
├── assets/
│   └── plugins/
│       ├── your_plugin.js      # Your plugin files
│       └── your_plugin.css
└── .github/
    └── workflows/
        └── plugin-register.yml # Your workflow (design as needed)
```

### Step 2: Create `pluginspec.yml`

Create a `pluginspec.yml` file in the root of your repository:

```yaml
plugins:
  - name: my_awesome_plugin
    version: 1.0.0
    assets:
      - assets/plugins/my_awesome_plugin.js
    description: A brief description of what your plugin does.

  - name: another_plugin
    version: 1.2.0
    assets:
      - assets/plugins/another_plugin.js
      - assets/plugins/another_plugin.css
    description: Another plugin with multiple asset files.
```

#### Plugin Fields Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique plugin identifier (use snake_case) |
| `version` | string | Yes | Semantic version (e.g., `1.0.0`, `2.1.3`) |
| `assets` | list | Yes | Relative paths to plugin files (JS, CSS, etc.) |
| `description` | string | Yes | Brief description of the plugin functionality |

### Step 3: Create GitHub Actions Workflow

Create `.github/workflows/plugin-register.yml` in your repository. Below is a basic example:

```yaml
name: Plugin Register

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  register:
    name: Register Plugins to Server
    runs-on: ubuntu-latest

    steps:
      - name: Checkout plugin repository
        uses: actions/checkout@v4

      - name: Checkout CLI repository
        uses: actions/checkout@v4
        with:
          repository: ljysoftware/simple_chat_plugin_cli
          ref: main
          path: cli

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install pyyaml

      - name: Register plugins
        env:
          PLUGIN_REPO_OWNER: ${{ github.repository_owner }}
          PLUGIN_REPO_NAME: ${{ github.event.repository.name }}
          PLUGIN_REPO_BRANCH: main
        run: python cli/scripts/register-plugins.py
```

### Step 4: Trigger Your Workflow

Once set up, your plugins will be registered when the workflow runs (based on your configured triggers).

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `PLUGIN_REPO_OWNER` | Yes | GitHub username or organization |
| `PLUGIN_REPO_NAME` | Yes | Repository name |
| `PLUGIN_REPO_BRANCH` | Yes | Branch to fetch `pluginspec.yml` from |
| `API_URL` | No | Custom plugin server URL (defaults to official server) |

### Important: Understanding `PLUGIN_REPO_BRANCH`

The CLI fetches `pluginspec.yml` from GitHub using this URL pattern:

```
https://raw.githubusercontent.com/{OWNER}/{REPO}/{BRANCH}/pluginspec.yml
```

This means `PLUGIN_REPO_BRANCH` should point to a branch where your `pluginspec.yml` **already exists** (i.e., has been pushed/merged).

### Using a Custom API Server

If you're running your own plugin server, add the `API_URL` environment variable:

```yaml
- name: Register plugins
  env:
    PLUGIN_REPO_OWNER: ${{ github.repository_owner }}
    PLUGIN_REPO_NAME: ${{ github.event.repository.name }}
    PLUGIN_REPO_BRANCH: main
    API_URL: https://your-custom-server.com/plugins
  run: python cli/scripts/register-plugins.py
```

Or set it as a repository variable:

1. Go to your repository **Settings**
2. Navigate to **Secrets and variables** > **Actions** > **Variables**
3. Add `PLUGIN_API_URL` with your server URL
4. Reference it in the workflow: `API_URL: ${{ vars.PLUGIN_API_URL }}`

## Workflow Trigger Options

Design your workflow triggers based on your team's needs. Here are common patterns:

### On Push (after merge)

Registers plugins when changes are merged to your target branch:

```yaml
on:
  push:
    branches: [main]
```

### On Pull Request

Runs registration when a PR is opened or updated:

```yaml
on:
  pull_request:
    branches: [main]
```

**Note**: When using `pull_request`, ensure `PLUGIN_REPO_BRANCH` points to a branch where `pluginspec.yml` exists. The CLI fetches from GitHub raw URL, not the local checkout.

### Manual Trigger

Allows manual execution from the GitHub Actions tab:

```yaml
on:
  workflow_dispatch:
```

### Combined Triggers

```yaml
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:
```

## How It Works

```
Your Plugin Repository                    Simple Chat Plugin Server
        |                                           |
        +-- Workflow triggered (push/PR/manual)     |
        |                                           |
        +-- CLI fetches pluginspec.yml              |
        |   from PLUGIN_REPO_BRANCH via GitHub      |
        |                                           |
        +-- For each plugin defined:                |
                |                                   |
                +-- POST request -----------------> |
                      - name                        |
                      - version                     |
                      - assets (file paths)         |
                      - description                 |
                      - url (raw GitHub URL)        |
                      - author (repo owner)         |
                                                    |
                                        Plugin registered and
                                        available in Simple Chat
```

## API Response

On successful registration, the server returns:

```json
{
  "id": "uuid-string",
  "name": "my_awesome_plugin",
  "version": "1.0.0",
  "url": "https://raw.githubusercontent.com/your-username/your-repo/main",
  "assets": ["assets/plugins/my_awesome_plugin.js"],
  "description": "A brief description of what your plugin does.",
  "author": "your-username",
  "enabled": true,
  "verified": false,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

## Local Development & Testing

```bash
# Clone your plugin repository
git clone https://github.com/your-username/your-plugin-repo.git
cd your-plugin-repo

# Clone the CLI
git clone https://github.com/ljysoftware/simple_chat_plugin_cli.git cli

# Install dependencies
pip install pyyaml

# Set environment variables
export PLUGIN_REPO_OWNER=your-username
export PLUGIN_REPO_NAME=your-plugin-repo
export PLUGIN_REPO_BRANCH=main

# Run the registration script
python cli/scripts/register-plugins.py
```

## Troubleshooting

### Common Issues

**1. "Missing required environment variables"**

Ensure all required environment variables are set in your workflow:
- `PLUGIN_REPO_OWNER`
- `PLUGIN_REPO_NAME`
- `PLUGIN_REPO_BRANCH`

**2. "404 when fetching pluginspec.yml"**

- Verify `pluginspec.yml` exists in your repository root
- Check that the branch name in `PLUGIN_REPO_BRANCH` matches your actual branch
- Ensure your repository is public (private repos require authentication)

**3. "Failed registration with 4xx error"**

- Check that your `pluginspec.yml` syntax is valid YAML
- Ensure all required fields (`name`, `version`, `assets`, `description`) are present
- Verify asset file paths are correct relative to repository root

### Validating Your pluginspec.yml

```bash
# Quick YAML syntax check
python -c "import yaml; yaml.safe_load(open('pluginspec.yml'))"
```

## Requirements

- Python 3.12+
- `pyyaml` package
- Public GitHub repository (for automatic asset fetching)

## License

MIT
