import os

def get_llm_config():
    """Returns a default configuration for all LLM agents."""
    return {
        "seed": 42,
        "config_list": [{
            "model": "gpt-4.1",
            "api_key": os.getenv("OPENAI_API_KEY")
        }],
        "temperature": 0
    }