# Linux Cowork Agent (Open Cowork)

**Linux Cowork Agent** is a full-featured, secure, and highly modular local desktop agent platform for Ubuntu/Linux. It allows an AI agent to see an isolated virtual Linux desktop, use mouse and keyboard automation, operate a web browser, edit files, execute terminal commands, and perform actions safely under customizable security constraints.

## 🚀 Key Features

*   **Isolated Linux Desktop Environment**: Runs a lightweight XFCE4 desktop inside a Docker container using Xvfb (Virtual Framebuffer).
*   **VNC/noVNC Live Stream**: Watch the agent work in real-time through a beautiful web dashboard utilizing a secure noVNC stream.
*   **Native Linux Desktop Bridge**: Inspect and control the XFCE/X11 desktop with structured window management, active-window detection, installed application discovery, URL launch, clipboard access, screenshots, and precise zoom-region inspection.
*   **Modular LLM Provider System**: Supports Anthropic Claude API (with native/structured computer use), OpenAI GPT-4o, OpenRouter, Ollama (for local vision models), and a **MockProvider** for testing without API keys.
*   **Robust Safety Engine**:
    *   **Risk Scoring**: Evaluates the potential risk level (`low`, `medium`, `high`) of every action.
    *   **Interactive Confirmation Gateway**: Automatically prompts the user for confirmation on medium/high-risk actions (e.g., `sudo`, deletion of files `rm -rf`, curl execution, password inputs, checkout pages).
    *   **Strict Isolation**: The agent only has access to its virtual sandbox. It cannot access the host machine's system files or network unless explicitly configured.
*   **E-Stop (Not-Aus)**: Instantly stop or pause the agent loop at any moment from the web interface.

---

## 🛠️ Architecture

The system operates as a three-tier architecture orchestrated via Docker Compose:

1.  **`sandbox`**: The isolated virtual Ubuntu environment. It runs Xvfb, XFCE4, VNC, noVNC, X11 utilities, and a lightweight Python **Sandbox Agent REST API** that receives commands (clicks, keys, shell scripts, window management, app discovery, clipboard, screenshots) from the backend and executes them locally inside the container.
2.  **`backend`**: A FastAPI application that orchestrates the agent loop, manages sessions, streams real-time WebSocket events, sends screenshot history/zoom context to LLM providers, and executes safety policy verification.
3.  **`frontend`**: A React + TypeScript frontend built with Vite. It features a modern dashboard containing the embedded noVNC view, real-time action logs, provider settings, zoom screenshots, and approval dialogs.

---

## 💻 Getting Started

### 📋 Prerequisites
*   Ubuntu/Linux host machine.
*   Docker & Docker Compose installed.
*   `gh` CLI logged in (optional, for remote sync).

### ⚙️ Quick Start

1.  Clone the repository (or navigate to your local copy):
    ```bash
    git clone https://github.com/meinzeug/open-cowork.git
    cd open-cowork
    ```

2.  Set up environment variables:
    ```bash
    cp .env.example .env
    # Edit .env and enter your API keys (e.g., ANTHROPIC_API_KEY)
    ```

3.  Install/check host dependencies once:
    ```bash
    ./install_ubuntu.sh
    ```

4.  Build and run the entire stack:
    ```bash
    ./start.sh
    ```

5.  Open the web interface:
    Access `http://localhost:3000` (or the backend/frontend mapped port) in your web browser.

### Docker daemon troubleshooting

If startup fails with `failed to connect to the docker API at unix:///var/run/docker.sock`, the Docker daemon is not running or your user cannot access it.

```bash
git pull
./install_ubuntu.sh
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
newgrp docker
./start.sh
```

If `systemctl` reports `Unit docker.service does not exist`, your host has the Docker CLI but not the Docker Engine service. Run `git pull && ./install_ubuntu.sh`; the installer repairs this by installing Docker Engine via Docker CE packages or Ubuntu's `docker.io` fallback.

On systems without `systemctl`, start Docker through the host's service manager and then rerun `./start.sh`.

---

## 🛡️ Safety & Security Policy

To prevent prompt injection attacks or destructive operations, the agent is configured to:
1.  **Block list**: Disallow modifications of system configurations (`/etc`), file permissions (`chmod`, `chown`), and dangerous tools (`dd`, `mkfs`) unless approved.
2.  **Explicit confirmation**: Require user validation before filling out credit card info, password forms, or executing system installation scripts.
3.  **No Host Escalation**: The container does not mount the host root directory and runs in a separate network bridge.
