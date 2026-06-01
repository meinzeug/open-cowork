from app.providers.openai_provider import OpenAIProvider


class OpenRouterProvider(OpenAIProvider):
    def __init__(self, api_key: str):
        super().__init__(
            api_key=api_key,
            api_url="https://openrouter.ai/api/v1/chat/completions",
            default_model="openai/gpt-4o",
            provider_name="OpenRouter",
            extra_headers={
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "Open Cowork"
            }
        )
