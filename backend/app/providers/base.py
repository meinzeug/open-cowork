from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.models.actions import ActionResponse

class BaseProvider(ABC):
    @abstractmethod
    async def generate_action(
        self,
        task: str,
        screenshot_base64: str,
        history: List[Dict[str, Any]],
        system_prompt: str
    ) -> ActionResponse:
        """
        Sends the task, current screenshot and step history to the LLM.
        Returns the structured ActionResponse.
        """
        pass
