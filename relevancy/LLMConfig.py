class LLMConfig:
    """Configuration settings for LLM interactions"""
    def __init__(self):
        self.api_key = "cmsc-35360"
        self.base_url = "http://localhost:9999/v1"
        self.model = "llama31-405b-fp8"
        self.temperature = 0.7