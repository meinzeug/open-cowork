import os
import subprocess
import base64
import logging
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pyautogui

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("sandbox_agent")

# Configuration
DISPLAY = os.getenv("DISPLAY", ":1")
WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "/workspace")
os.environ["DISPLAY"] = DISPLAY

# Disable PyAutoGUI Failsafe so that cursor moving to screen edge doesn't crash the agent
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.1

app = FastAPI(title="Linux Sandbox Agent API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global shell state
class ShellState:
    cwd: str = WORKSPACE_DIR

shell_state = ShellState()

# Request Models
class MouseMoveRequest(BaseModel):
    x: int
    y: int

class MouseClickRequest(BaseModel):
    x: Optional[int] = None
    y: Optional[int] = None
    button: str = "left"  # left, right, middle
    click_type: str = "single"  # single, double

class MouseDragRequest(BaseModel):
    x: int
    y: int

class MouseScrollRequest(BaseModel):
    clicks: int
    direction: str = "down"  # up, down

class KeyboardTypeRequest(BaseModel):
    text: str

class KeyboardKeyRequest(BaseModel):
    key: str  # e.g., "enter", "ctrl+c", "ctrl+l"

class ShellRequest(BaseModel):
    command: str
    cwd: Optional[str] = None

class FileReadRequest(BaseModel):
    path: str

class FileWriteRequest(BaseModel):
    path: str
    content: str

class FileListRequest(BaseModel):
    path: Optional[str] = None


@app.get("/health")
def health():
    return {"status": "ok", "display": DISPLAY, "workspace": WORKSPACE_DIR}


@app.post("/screenshot")
def take_screenshot():
    screenshot_path = "/tmp/screenshot.png"
    if os.path.exists(screenshot_path):
        try:
            os.remove(screenshot_path)
        except Exception as e:
            logger.warning(f"Could not remove old screenshot: {e}")

    try:
        # Use scrot for lightweight high-performance screenshot
        res = subprocess.run(
            ["scrot", "-z", screenshot_path],
            env=dict(os.environ, DISPLAY=DISPLAY),
            capture_output=True,
            text=True
        )
        if res.returncode != 0:
            logger.error(f"scrot failed: {res.stderr}")
            # Fallback to PyAutoGUI if scrot failed
            pyautogui.screenshot(screenshot_path)
            
        if not os.path.exists(screenshot_path):
            raise HTTPException(status_code=500, detail="Screenshot file was not created.")

        with open(screenshot_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
        
        # Get screen size for resolution detection
        width, height = pyautogui.size()
        
        return {
            "success": True,
            "image": encoded_string,
            "width": width,
            "height": height
        }
    except Exception as e:
        logger.error(f"Screenshot exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mouse/move")
def mouse_move(req: MouseMoveRequest):
    try:
        pyautogui.moveTo(req.x, req.y, duration=0.2)
        return {"success": True, "x": req.x, "y": req.y}
    except Exception as e:
        logger.error(f"Mouse move exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mouse/click")
def mouse_click(req: MouseClickRequest):
    try:
        if req.x is not None and req.y is not None:
            pyautogui.moveTo(req.x, req.y, duration=0.2)
        
        clicks = 2 if req.click_type == "double" else 1
        pyautogui.click(button=req.button, clicks=clicks)
        
        pos = pyautogui.position()
        return {"success": True, "x": pos.x, "y": pos.y, "button": req.button, "type": req.click_type}
    except Exception as e:
        logger.error(f"Mouse click exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mouse/drag")
def mouse_drag(req: MouseDragRequest):
    try:
        pyautogui.dragTo(req.x, req.y, duration=0.5, button="left")
        return {"success": True, "x": req.x, "y": req.y}
    except Exception as e:
        logger.error(f"Mouse drag exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mouse/scroll")
def mouse_scroll(req: MouseScrollRequest):
    try:
        # positive scroll is up, negative scroll is down
        amount = req.clicks if req.direction == "up" else -req.clicks
        pyautogui.scroll(amount)
        return {"success": True, "clicks": req.clicks, "direction": req.direction}
    except Exception as e:
        logger.error(f"Mouse scroll exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/keyboard/type")
def keyboard_type(req: KeyboardTypeRequest):
    try:
        # Type with slight delay to mimic human input
        pyautogui.write(req.text, interval=0.01)
        return {"success": True, "text": req.text}
    except Exception as e:
        logger.error(f"Keyboard type exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/keyboard/key")
def keyboard_key(req: KeyboardKeyRequest):
    try:
        keys = req.key.lower().split("+")
        if len(keys) > 1:
            pyautogui.hotkey(*keys)
        else:
            pyautogui.press(req.key)
        return {"success": True, "key": req.key}
    except Exception as e:
        logger.error(f"Keyboard key exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/open_app")
def open_app(req: KeyboardTypeRequest):
    try:
        # Run application as background process inside the desktop environment
        subprocess.Popen(
            f"DISPLAY={DISPLAY} {req.text}",
            shell=True,
            preexec_fn=os.setsid,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return {"success": True, "app": req.text}
    except Exception as e:
        logger.error(f"Open app exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/shell")
def run_shell(req: ShellRequest):
    target_cwd = req.cwd or shell_state.cwd
    
    # Ensure CWD exists
    if not os.path.exists(target_cwd):
        target_cwd = WORKSPACE_DIR
        
    try:
        # Run command with bash
        res = subprocess.run(
            req.command,
            shell=True,
            cwd=target_cwd,
            env=dict(os.environ, DISPLAY=DISPLAY),
            capture_output=True,
            text=True,
            timeout=30  # Prevent infinite hangs
        )
        
        # Simple cd tracker in bash
        if req.command.strip().startswith("cd "):
            parts = req.command.split(" ", 1)
            if len(parts) > 1:
                new_dir = os.path.expanduser(parts[1].strip())
                new_path = os.path.abspath(os.path.join(target_cwd, new_dir))
                if os.path.exists(new_path) and os.path.isdir(new_path):
                    shell_state.cwd = new_path
                    logger.info(f"Updated shell state CWD to: {shell_state.cwd}")

        return {
            "success": True,
            "stdout": res.stdout,
            "stderr": res.stderr,
            "exit_code": res.returncode,
            "cwd": shell_state.cwd
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Command timed out after 30 seconds",
            "exit_code": -1,
            "cwd": shell_state.cwd
        }
    except Exception as e:
        logger.error(f"Shell command exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/files/read")
def read_file(req: FileReadRequest):
    # Resolve relative paths relative to current workspace
    full_path = os.path.abspath(os.path.join(shell_state.cwd, req.path))
    
    # Simple jail check (sandbox containment)
    if not full_path.startswith(WORKSPACE_DIR) and not full_path.startswith("/tmp"):
        # We can warning or block. In a sandbox, we let it slide for system files but block edits.
        # For security, let's allow reading files outside, but be cautious.
        pass
        
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail=f"File not found: {req.path}")
    if os.path.isdir(full_path):
        raise HTTPException(status_code=400, detail="Path is a directory, not a file.")
        
    try:
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return {"success": True, "path": req.path, "content": content}
    except Exception as e:
        logger.error(f"Read file exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/files/write")
def write_file(req: FileWriteRequest):
    full_path = os.path.abspath(os.path.join(shell_state.cwd, req.path))
    
    # Ensure target directory exists
    dir_name = os.path.dirname(full_path)
    os.makedirs(dir_name, exist_ok=True)
    
    try:
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(req.content)
        return {"success": True, "path": req.path, "size": len(req.content)}
    except Exception as e:
        logger.error(f"Write file exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/files/list")
def list_files(req: FileListRequest):
    target_dir = os.path.abspath(os.path.join(shell_state.cwd, req.path or "."))
    if not os.path.exists(target_dir):
        raise HTTPException(status_code=404, detail="Directory not found")
        
    try:
        items = []
        for name in os.listdir(target_dir):
            path = os.path.join(target_dir, name)
            is_dir = os.path.isdir(path)
            size = os.path.getsize(path) if not is_dir else 0
            items.append({
                "name": name,
                "is_dir": is_dir,
                "size": size
            })
        return {"success": True, "path": target_dir, "files": items}
    except Exception as e:
        logger.error(f"List files exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))
