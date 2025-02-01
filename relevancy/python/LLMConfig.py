class LLMConfig:
    """Configuration settings for LLM interactions"""
    def __init__(self):
        self.api_key = "cmsc-35360"
        self.base_url = "http://lambda13.cels.ano.gov:9999/v1"
        self.model = "llama31-405b-fp8"
        self.temperature = 1.0 
        
        self.logfile = "logfile"
