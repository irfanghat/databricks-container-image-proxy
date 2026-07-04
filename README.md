# DBRX Registry

A **serverless Docker image registry** backed by **Databricks Unity Catalog Volumes**. No registry server, and **no extra infrastructure**.

If you already run Databricks, you already have a governed, access-controlled, versioned storage layer sitting in your workspace. This turns that into a private container registry with three commands: `push`, `pull`, `run`.


## Why Databricks Volumes as a container registry?

This is an idea that started out as a Proof of Concept.

Also, if you're already a Databricks shop, Unity Catalog Volumes give you something a purpose-built registry would charge you extra for:

- **Unified governance** - The same Unity Catalog permissions (Catalog/Schema/Volume), that guard your tables and files now guard your container images. No separate registry IAM to maintain.
- **Zero new infrastructure** - No registry server to deploy, patch, or scale. Volumes are already highly available, durable **object storage** under the hood.
- **One audit trail** - Image pushes and pulls show up alongside other Unity Catalog access logs.
- **Cost simplicity** - You pay for storage you likely already provision, not a second storage bill for a dedicated registry.
- **Team-native** - Data and ML engineers already have Databricks credentials, there's no separate registry login to distribute or rotate.

This project is intentionally simple, it doesn't try to reimplement the **OCI Distribution Spec**. It saves images as compressed tarballs (`docker save` -> `gzip`) and streams them to and from a Volume path using the Databricks **Files API**. Think of it as `docker save`/`docker load`, automated, with your Volume as the shared drop point.


## How it works

[Diagram]()

- **Push**: `docker save` -> gzip-compress with a live progress bar and SHA-256 checksum → stream directly to the Volume via `PUT`.
- **Pull**: stream the object back with `GET` -> decompress -> `docker load` into your local daemon.
- **List**: reads the Volume directory listing and reconstructs image name/tag pairs from the stored filenames.
- **Run**: pulls automatically if the image isn't cached locally, then hands off to `docker run`.

Image references are stored as `<name>__<tag>.tar.gz`, so `nginx:alpine` becomes `nginx__alpine.tar.gz` inside your configured Volume path.


## Prerequisites (Linux)

- Python 3.9+
- Docker installed and running locally
- A Databricks workspace with a Unity Catalog **Volume** you have read/write access to
- A Databricks **personal access token** (or other bearer token) with Files API permissions on that Volume


## Installation & Configuration

Please refer to the INSTALL.md file for detailed setup instructions and environment variable configuration.

## Usage

### Push a local image

```bash
python dcip.py push nginx:alpine
```

Saves, compresses, and uploads the image to your configured Volume.

### Pull an image

```bash
python dcip.py pull nginx:alpine
```

Downloads, decompresses, and loads the image into your local Docker daemon.

### List images in the registry

```bash
python dcip.py list
```

Prints a table of every image name, tag, size, and last-modified time stored in the Volume.

### Run an image (pulling automatically if needed)

```bash
python dcip.py run nginx:alpine --name my-nginx -p 8080:80
```

> ⚠️ **Image reference must come immediately after `run`, before any Docker flags.** Since DBRX Registry forwards arbitrary `docker run` flags transparently, the image has to be bound first so flags like `-p`, `-e`, `--name`, and `-d` are correctly passed through to Docker, not misread as the image name.

```bash
# -------------------------------------------------
# Detached, with env vars and a container name
# -------------------------------------------------
python dcip.py run my-app:v1.2.0 -d -p 8080:80 --name production-app -e NODE_ENV=production
```


## Command reference

| Command | Description |
|---|---|
| `push <image>` | Save, compress, and upload a local image to the Volume |
| `pull <image>` | Download, decompress, and load an image from the Volume |
| `run <image> [docker flags...]` | Pull if missing, then `docker run` with forwarded flags |
| `list` | List all images currently stored in the Volume |


## Limitations

- **Not OCI-compliant.** This is a tarball shuttle, not a Distribution Spec-compatible registry, you can't `docker pull` from it directly, only through this CLI.
- **No layer deduplication.** Every push uploads a full compressed tarball of the image, there's no shared-layer storage like a real registry.
- **5 GiB per-file cap**, per the Databricks Files API's direct-upload limit, fine for most application images, worth knowing for very large ones.
- **Single reader/writer model.** There's no locking, concurrent pushes to the same tag can race.

If you need full OCI compliance, layer caching, or multi-writer safety at scale, treat this as a lightweight bridge rather than a Harbor/ECR replacement, the sweet spot is small teams or CI pipelines that want zero extra infrastructure and already trust Unity Catalog for governance.


## Troubleshooting
To do