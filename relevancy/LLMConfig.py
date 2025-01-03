class LLMConfig:
    """Configuration settings for LLM interactions"""
    def __init__(self):
        self.api_key = "EMPTY"
        self.base_url = "http://localhost:9999/v1"
        self.model = "llama31-405b-fp8"
        self.temperature = 1.0 

