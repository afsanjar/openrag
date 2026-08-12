# OpenRAG 0.5.1 — IBM Power (ppc64le) Install Package

Self-contained install bundle for running OpenRAG on IBM Power (ppc64le) machines.

## What's in this package

| File | Purpose |
|---|---|
| `install.sh` | End-to-end install script — run this to get OpenRAG running |
| `ppc64le-consolidated.patch` | All ppc64le patches against `langflow-ai/openrag` `refactor-image-config` branch |
| `README.md` | This file |

The `install.sh` has the OpenRAG wheel embedded as a base64 payload — no separate
download or internet access to PyPI is needed for the wheel itself.

---

## Prerequisites

Before running `install.sh`, confirm the following on your Power machine:

| Requirement | Check |
|---|---|
| ppc64le Linux (Power9 or Power10) | `uname -m` → `ppc64le` |
| Podman (rootful) | `podman info` |
| Python 3.13 | `python3.13 --version` |
| uv | `uv --version` |
| IBM w3 credentials | Artifactory login (prompted during install) |
| ~8 GB free RAM | For OpenSearch + Langflow + backend + frontend |
| ~20 GB free disk | For container images |

Install uv if missing:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.local/bin/env
```

---

## Install routes

There are two ways to get OpenRAG running on a Power machine:

| Route | Best for | Steps |
|---|---|---|
| **Tarball `install.sh`** | First-time setup, end users | Extract tarball → run `./install.sh` → `openrag` |
| **Wheel directly** | Iterative testing, dev workflow | `uv pip install wheel` → configure `.env` → `openrag` |

Both end up running the same stack. The tarball route handles image pulls,
`.env` generation, and flow seeding automatically. The direct wheel route gives
you more control and is faster when you're iterating on the wheel itself.

---

## Route 1 — Quick start (tarball)

```bash
tar -xzf openrag-ppc64le-0.5.1.tar.gz
cd openrag-ppc64le
chmod +x install.sh
./install.sh
```

The script runs 6 phases and prompts for credentials at phase 2:

| Phase | What happens |
|---|---|
| 1. Prereqs | Checks podman, uv, Python 3.13, disk/RAM |
| 2. Login | Prompts for IBM w3 email + Artifactory API token; logs into registry |
| 3. Images | Pulls Langflow, backend, frontend images; builds OpenSearch locally |
| 4. Wheel | Extracts and installs the embedded OpenRAG wheel |
| 5. Env | Creates `~/.openrag/tui/.env` with your credentials and passwords |
| 6. Flows | Seeds the default Langflow flows |

When the script finishes, start the TUI:
```bash
openrag
```

Press **S** in the TUI to start the full stack. Once all containers are green,
open `http://<your-machine-ip>:3000` in a browser.

---

## Route 2 — Direct wheel install (testing / dev)

Use this when you already have the wheel (built locally or extracted from the
build script) and want to install and iterate without running the full install
script.

**From your Mac — build and copy the wheel:**
```bash
# Build on Mac (pure Python wheel, works on any arch)
uv build
scp dist/openrag-0.5.1-py3-none-any.whl root@<power-machine>:~/
```

**On the Power machine:**
```bash
uv venv --python 3.13 ~/openrag-venv
source ~/openrag-venv/bin/activate
uv pip install ~/openrag-0.5.1-py3-none-any.whl \
  --extra-index-url https://wheels.developerfirst.ibm.com/ppc64le/linux/+simple/ \
  --index-strategy unsafe-best-match
openrag
```

You will still need to create `~/.openrag/tui/.env` manually (see
[After install — configuring LLM credentials](#after-install--configuring-llm-credentials)
below) and start the stack from the TUI. Container images must already be
pulled or you must have Artifactory access for the TUI to pull them on first
start.

---

## Non-interactive install (CI / scripted)

Set all required env vars before running:

```bash
export ARTIFACTORY_USER=you@ibm.com
export ARTIFACTORY_TOKEN=<your Artifactory API token>
export OPENSEARCH_PASSWORD=<strong password>
export LANGFLOW_SUPERUSER_PASSWORD=<strong password>

./install.sh --non-interactive
```

---

## After install — configuring LLM credentials

The install script creates `~/.openrag/tui/.env`. Open it to add your model
provider credentials before starting the stack:

```bash
nano ~/.openrag/tui/.env
```

**WatsonX (recommended for Power):**
```bash
WATSONX_URL=https://us-south.ml.cloud.ibm.com
WATSONX_APIKEY=<your IBM Cloud API key>
WATSONX_PROJECT_ID=<your WatsonX project ID>
```

**OpenAI-compatible endpoint:**
```bash
OPENAI_API_KEY=<your key>
OPENAI_API_BASE=<endpoint url>   # optional, for custom endpoints
```

---

## Container images used

| Service | Image |
|---|---|
| Langflow | `docker-na-public.artifactory.swg-devops.com/.../openrag-langflow-fast:1.9.0` |
| Backend | `docker-na-public.artifactory.swg-devops.com/.../openrag-backend:0.5.1` |
| Frontend | `docker-na-public.artifactory.swg-devops.com/.../openrag-frontend:0.5.1` |
| OpenSearch Dashboards | `docker-na-public.artifactory.swg-devops.com/.../cnos-dashboards:3.6.0-052726` |
| OpenSearch | Built locally from `icr.io/ppc64le-oss/opensearch-ppc64le:3.6.0` |

All images except OpenSearch are pulled from the IBM internal Artifactory registry
— Artifactory credentials are required.

---

## Applying the patch to upstream (for contributors)

The `ppc64le-consolidated.patch` applies against the `langflow-ai/openrag`
`refactor-image-config` branch:

```bash
git clone --branch refactor-image-config https://github.com/langflow-ai/openrag
cd openrag
git apply /path/to/ppc64le-consolidated.patch
```

The patched branch is also available directly:
```bash
git clone --branch ppc64le-0.5.1 https://github.com/afsanjar/openrag
```

---

## Troubleshooting

**Containers won't start after `openrag` TUI launches**
- Check `~/.openrag/tui/docker-compose.yml` exists
- Confirm `OPENSEARCH_PASSWORD` is set in `~/.openrag/tui/.env`
- Run `podman ps -a` to see container state and `podman logs <name>` for errors

**OpenSearch stays yellow/unhealthy**
- Give it 2–3 minutes on first boot — it initialises security config on startup
- Check `podman logs os` for errors

**`openrag` command not found after install**
- The wheel installs the entry point into uv's managed Python environment
- Run: `source ~/.local/bin/env && openrag`
- Or add `~/.local/bin` to your `PATH` in `~/.bashrc`

**Registry pull fails (401 Unauthorized)**
- Re-run phase 2 manually: `podman login docker-na-public.artifactory.swg-devops.com`
- Use your w3 email and an Artifactory API token (not your w3 password)
- Generate a token at: https://na.artifactory.swg-devops.com → Profile → API Key

---

## Maintainer

Kamryn Schock — kamrynschock@ibm.com

Source branch: [`afsanjar/openrag@ppc64le-0.5.1`](https://github.com/afsanjar/openrag/tree/ppc64le-0.5.1)  
Build script: [`ppc64le/build-scripts/o/openrag/`](https://github.com/ppc64le/build-scripts/tree/master/o/openrag)
