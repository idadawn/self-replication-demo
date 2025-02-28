import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

class Settings:
    # LLM配置
    QWEN_API_KEY = os.getenv('QWEN_API_KEY')
    QWEN_MODEL_NAME = os.getenv('QWEN_MODEL_NAME', 'Qwen/Qwen-72B-Instruct')
    QWEN_API_BASE = os.getenv('QWEN_API_BASE', 'https://api.qwen.ai/v1')
    
    # 生成参数
    MAX_TOKENS = int(os.getenv('MAX_TOKENS', 512))
    TEMPERATURE = float(os.getenv('TEMPERATURE', 0.7))
    TOP_P = float(os.getenv('TOP_P', 0.9))
    
    # 验证配置
    @classmethod
    def validate(cls):
        if not cls.QWEN_API_KEY:
            raise ValueError("QWEN_API_KEY not found in environment variables")
            
        if not cls.QWEN_API_BASE:
            raise ValueError("QWEN_API_BASE not found in environment variables")

settings = Settings() 