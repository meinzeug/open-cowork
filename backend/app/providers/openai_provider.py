import json
import logging
import httpx
from typing import List, Dict, Any
from app.providers.base import BaseProvider
from app.models.actions import ActionResponse, Action

logger = logging.getLogger(__name__)

class OpenAIProvider(BaseProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.openai.com/v1/chat/completions"

    async def generate_action(
        self,
        task: str,
        screenshot_base64: str,
        history: List[Dict[str, Any]],
        system_prompt: str
    ) -> ActionResponse:
        if not self.api_key:
            raise ValueError("OpenAI API Key ist nicht konfiguriert.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Build messages starting with system prompt
        messages = [
            {"role": "system", "content": system_prompt}
        ]

        # Add history steps
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
        current_content = [
            {
                "type": "text",
                "text": f"Aktueller Schritt. Gesamtaufgabe: {task}"
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{screenshot_base64}"
                }
            }
        ]

        messages.append({
            "role": "user",
            "content": current_content
        })

        data = {
            "model": "gpt-4o",
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0.0,
            "max_tokens": 1500
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = client.post(self.api_url, headers=headers, json=data)

            if response.status_code != 200:
                logger.error(f"OpenAI API Fehler ({response.status_code}): {response.text}")
                raise Exception(f"OpenAI API returned status {response.status_code}: {response.text}")

            result = response.json()
            response_text = result["choices"][0]["message"]["content"].strip()
            
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
            logger.error(f"OpenAI Provider Exception: {e}")
            return ActionResponse(
                summary=f"Fehler bei der Kommunikation mit OpenAI: {str(e)}",
                risk="low",
                requires_confirmation=False,
                action=Action(type="wait", params={"seconds": 5}),
                done=False
            )
