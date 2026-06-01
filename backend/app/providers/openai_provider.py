import json
import logging
import httpx
from typing import List, Dict, Any
from app.providers.base import BaseProvider
from app.models.actions import ActionResponse, Action

logger = logging.getLogger(__name__)

class OpenAIProvider(BaseProvider):
    def __init__(
        self,
        api_key: str,
        api_url: str = "https://api.openai.com/v1/chat/completions",
        default_model: str = "gpt-4o",
        provider_name: str = "OpenAI",
        extra_headers: Dict[str, str] | None = None
    ):
        self.api_key = api_key
        self.api_url = api_url
        self.default_model = default_model
        self.provider_name = provider_name
        self.extra_headers = extra_headers or {}

    async def generate_action(
        self,
        task: str,
        screenshot_base64: str,
        history: List[Dict[str, Any]],
        system_prompt: str,
        previous_screenshot_base64: str | None = None,
        focused_screenshot_base64: str | None = None,
        model: str | None = None
    ) -> ActionResponse:
        if not self.api_key:
            raise ValueError(f"{self.provider_name} API Key ist nicht konfiguriert.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            **self.extra_headers
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

        # Add current screenshot and optional previous frame for visual reflection.
        current_content = [
            {
                "type": "text",
                "text": f"Aktueller Schritt. Gesamtaufgabe: {task}"
            }
        ]
        if previous_screenshot_base64:
            current_content.extend([
                {
                    "type": "text",
                    "text": "Vorheriger Screenshot vor der letzten Aktion. Vergleiche ihn mit dem aktuellen Screenshot."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{previous_screenshot_base64}"
                    }
                },
                {
                    "type": "text",
                    "text": "Aktueller Screenshot nach der letzten Aktion:"
                }
            ])
        if focused_screenshot_base64:
            current_content.extend([
                {
                    "type": "text",
                    "text": "Zuletzt angeforderter vergrößerter Ausschnitt. Nutze ihn für präzise Texterkennung und Koordinatenplanung:"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{focused_screenshot_base64}"
                    }
                }
            ])
        current_content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{screenshot_base64}"
                }
            }
        )

        messages.append({
            "role": "user",
            "content": current_content
        })

        data = {
            "model": model or self.default_model,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0.0,
            "max_tokens": 1500
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(self.api_url, headers=headers, json=data)

            if response.status_code != 200:
                logger.error(f"{self.provider_name} API Fehler ({response.status_code}): {response.text}")
                raise Exception(f"{self.provider_name} API returned status {response.status_code}: {response.text}")

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
            logger.error(f"{self.provider_name} Provider Exception: {e}")
            return ActionResponse(
                summary=f"Fehler bei der Kommunikation mit {self.provider_name}: {str(e)}",
                risk="low",
                requires_confirmation=False,
                action=Action(type="wait", params={"seconds": 5}),
                done=False
            )
