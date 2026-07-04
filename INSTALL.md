# Installation Guide

Follow these steps to set up the **Databricks Container Image Proxy (DCIP)** utility.

## Prerequisites

- **Python 3.9+**: Ensure Python is installed on your system.
- **Docker**: The Docker daemon must be installed and running locally.
- **Databricks Workspace**: You need access to a workspace with Unity Catalog enabled.
- **Unity Catalog Volume**: A target Volume (e.g., `/Volumes/main/default/my_images`) where you have read/write permissions.
- **Databricks Personal Access Token (PAT)**: A token with permissions to access the Files API for the target Volume.

## Setup

Clone the repository and navigate to the project directory:

```bash
git clone https://github.com/irfanghat/databricks-container-image-proxy.git
cd dbx-poc/databricks_container_image_proxy
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the root directory (`~/dbx-poc/databricks_container_image_proxy/.env`) with the following variables:

```env
DATABRICKS_HOST=https://<your-workspace-url>.databricks.com
DATABRICKS_TOKEN=dapi************************
DATABRICKS_VOLUME=/Volumes/<catalog>/<schema>/<volume>
```

Alternatively, you can **export** the following variables:
```sh
export DATABRICKS_HOST=https://<your-workspace-url>.databricks.com
export DATABRICKS_TOKEN=dapi************************
export DATABRICKS_VOLUME=/Volumes/<catalog>/<schema>/<volume>
```

## Verify Installation

Check that the CLI is configured correctly by listing the contents of your volume:

```bash
python dcip.py list
```