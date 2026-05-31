import json
import logging
import httpx
from typing import List, Dict, Any
from app.providers.base import BaseProvider
from app.models.actions import ActionResponse, Action

logger = logging.getLogger(__name__)

class OllamaProvider(BaseProvider):
    def __init__(self, api_base: str = "http://localhost:11434"):
        self.api_base = api_base
        self.api_url = f"{api_base}/api/chat"

    async def generate_action(
        self,
        task: str,
        screenshot_base64: str,
        history: List[Dict[str, Any]],
        system_prompt: str
    ) -> ActionResponse:
        headers = {"Content-Type": "application/json"}

        # Build message history
        messages = [
            {"role": "system", "content": system_prompt}
        ]

        # Add history
        for step in history:
            action_json = {
                "summary": step.get("summary", ""),
                "risk": step.get("risk", "low"),
                "requires_confirmation": step.get("requires_confirmation", False),
                "action": {
                    "type": step.get("action_type"),
                    "params": step.get("action_params", {})
                },
                "done": step.get("status") == "completed" or step.get("action_type") == "finish"
            }
            messages.append({
                "role": "assistant",
                "content": json.dumps(action_json)
            })
            
            env_content = f"Step {step.get('step')} Result:\n"
            if step.get("output"):
                env_content += f"Stdout: {step.get('output')}\n"
            if step.get("error"):
                env_content += f"Error: {step.get('error')}\n"
            if not step.get("output") and not step.get("error"):
                env_content += "Aktion erfolgreich ausgeführt.\n"
                
            messages.append({
                "role": "user",
                "content": env_content
            })

        # Add current screenshot
        messages.append({
            "role": "user",
            "content": f"Aktueller Schritt. Gesamtaufgabe: {task}",
            "images": [screenshot_base64]
        })

        # Default model is llama3.2-vision or llava
        data = {
            "model": "llama3.2-vision",
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.0
            }
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = client.post(self.api_url, headers=headers, json=data)

            if response.status_code != 200:
                logger.error(f"Ollama API Fehler ({response.status_code}): {response.text}")
                raise Exception(f"Ollama API returned status {response.status_code}: {response.text}")

            result = response.json()
            response_text = result["message"]["content"].strip()
            
            # Clean JSON formatting
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            parsed_json = json.loads(response_text)
            
            return ActionResponse(
                summary=parsed_json.get("summary", ""),
                risk=parsed_json.get("risk", "low"),
                requires_confirmation=parsed_json.get("requires_confirmation", False),
                action=Action(
                    type=parsed_json["action"].get("type", "wait"),
                    params=parsed_json["action"].get("params", {})
                ),
                done=parsed_json.get("done", False)
            )

        except Exception as e:
            logger.error(f"Ollama Provider Exception: {e}")
            # Try falling back to llava
            if "llama3.2-vision" in data["model"]:
                try:
                    logger.info("Versuche Fallback auf llava Modell...")
                    data["model"] = "llava"
                    async with httpx.AsyncClient(timeout=120.0) as client:
                        response = client.post(self.api_url, headers=headers, json=data)
                    if response.status_code == 200:
                        result = response.json()
                        response_text = result["message"]["content"].strip()
                        if "```json" in response_text:
                            response_text = response_text.split("```json")[1].split("```")[0].strip()
                        parsed_json = json.loads(response_text)
                        return ActionResponse(
                            summary=parsed_json.get("summary", ""),
                            risk=parsed_json.get("risk", "low"),
                            requires_confirmation=parsed_json.get("requires_confirmation", False),
                            action=Action(
                                type=parsed_json["action"].get("type", "wait"),
                                params=parsed_json["action"].get("params", {})
                            ),
                            done=parsed_json.get("done", False)
                        )
                except Exception as ex:
                    logger.error(f"Ollama Fallback Fehler: {ex}")

            return ActionResponse(
                summary=f"Fehler bei der Kommunikation mit Ollama: {str(e)}",
                risk="low",
                requires_confirmation=False,
                action=Action(type="wait", params={"seconds": 5}),
                done=False
            )
