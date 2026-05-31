import json
import logging
import httpx
from typing import List, Dict, Any
from app.providers.base import BaseProvider
from app.models.actions import ActionResponse, Action

logger = logging.getLogger(__name__)

class AnthropicProvider(BaseProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.anthropic.com/v1/messages"

    async def generate_action(
        self,
        task: str,
        screenshot_base64: str,
        history: List[Dict[str, Any]],
        system_prompt: str
    ) -> ActionResponse:
        if not self.api_key:
            raise ValueError("Anthropic API Key ist nicht konfiguriert.")

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        # Build messages with history and current image
        messages = []
        
        # Add history steps
        for step in history:
            # Add past agent response
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
            
            # Add past result / environment response
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

        # Add current screenshot and user prompt
        current_content = [
            {
                "type": "text",
                "text": f"Aktueller Schritt. Gesamtaufgabe: {task}"
            },
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": screenshot_base64
                }
            }
        ]
        
        messages.append({
            "role": "user",
            "content": current_content
        })

        data = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 2000,
            "system": system_prompt,
            "messages": messages,
            "temperature": 0.0
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = client.post(self.api_url, headers=headers, json=data)
                
            if response.status_code != 200:
                logger.error(f"Anthropic API Fehler ({response.status_code}): {response.text}")
                raise Exception(f"Anthropic API returned status {response.status_code}: {response.text}")

            result = response.json()
            response_text = result["content"][0]["text"].strip()
            
            # Extract JSON from response
            # Sometimes models wrap in markdown ```json ... ```
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
            logger.error(f"Anthropic Provider Exception: {e}")
            # Return a fallback action to prevent loop crashes
            return ActionResponse(
                summary=f"Fehler bei der Kommunikation mit Claude: {str(e)}",
                risk="low",
                requires_confirmation=False,
                action=Action(type="wait", params={"seconds": 5}),
                done=False
            )
