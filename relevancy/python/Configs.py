from dataclasses import dataclass

@dataclass
class LLMConfig:
    """Configuration settings for LLM interactions"""
    api_key: str
    base_url: str
    model: str
    temperature: float
    logfile: str

@dataclass
class LitScanConfig:
    """Configuration class to manage API endpoints and settings"""
    retmax: int=40 
    openai_api_key: str="EMPTY"
    openai_base_url: str="http://lambda13.cels.anl.gov:9999/v1"
    openai_model: str="llama31-405b-fp8"

@dataclass
class PPIScanConfig:
    """Configuration settings for the literature scanning application."""
    # Partner interaction settings
    PARTNER_LIMIT = 50
    PARTNER_SCORE_THRESHOLD = 0.925
