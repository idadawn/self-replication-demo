import os
import json
import aiohttp
from typing import Dict, List, Optional
from dotenv import load_dotenv
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers import BitsAndBytesConfig
from .monitoring.logger import ActivityLogger

# 加载环境变量
load_dotenv()

class BaseAdapter:
    def __init__(self):
        self.logger = ActivityLogger()
        
    async def generate_response(self, prompt: str, params: Dict) -> str:
        """
        生成响应的基类方法
        """
        raise NotImplementedError
        
    def _log_generation(self, prompt: str, response: str, params: Dict):
        """
        记录生成过程
        """
        self.logger.log_activity('llm_generation', {
            'prompt': prompt,
            'response': response,
            'parameters': params
        })

class QwenAdapter(BaseAdapter):
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv('QWEN_API_KEY')
        self.model_name = os.getenv('QWEN_MODEL_NAME')
        self.api_base = os.getenv('QWEN_API_BASE')
        
        if not self.api_key:
            raise ValueError("QWEN_API_KEY not found in environment variables")
            
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        self.logger.log_activity('qwen_initialized', {
            'model': self.model_name,
            'api_base': self.api_base
        })
            
    async def generate_response(
        self, 
        prompt: str, 
        params: Optional[Dict] = None
    ) -> str:
        """
        通过API生成响应
        """
        if params is None:
            params = {}
            
        try:
            # 设置默认参数
            request_data = {
                'model': self.model_name,
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': int(os.getenv('MAX_TOKENS', 512)),
                'temperature': float(os.getenv('TEMPERATURE', 0.7)),
                'top_p': float(os.getenv('TOP_P', 0.9)),
                **params
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/chat/completions",
                    headers=self.headers,
                    json=request_data
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"API调用失败: {error_text}")
                        
                    result = await response.json()
                    
                    if 'choices' not in result or not result['choices']:
                        raise Exception("API返回结果格式错误")
                        
                    response_text = result['choices'][0]['message']['content']
                    
                    # 记录生成过程
                    self._log_generation(prompt, response_text, request_data)
                    
                    return response_text
                    
        except Exception as e:
            self.logger.log_activity('generation_error', {
                'error': str(e),
                'prompt': prompt
            })
            raise
            
    async def generate_plan(self, observation: Dict) -> List[Dict]:
        """
        生成行动计划
        """
        prompt = self._format_planning_prompt(observation)
        response = await self.generate_response(prompt)
        return self._parse_plan(response)
        
    def _format_planning_prompt(self, observation: Dict) -> str:
        """
        格式化规划提示
        """
        return f"""
        基于当前环境观察生成行动计划:
        
        环境状态:
        {json.dumps(observation, ensure_ascii=False, indent=2)}
        
        请生成一个3步行动计划，包含以下内容:
        1. 每步行动的具体操作
        2. 预期结果
        3. 可能的风险
        
        以JSON格式返回计划。
        """
        
    def _parse_plan(self, response: str) -> List[Dict]:
        """
        解析生成的计划
        """
        try:
            return json.loads(response)
        except:
            return [{
                'action': 'error',
                'error': '计划解析失败'
            }]

class LlamaAdapter(BaseAdapter):
    def __init__(self, model_path: str = "meta-llama/Llama-2-70b-chat-hf"):
        super().__init__()
        # Llama模型的具体实现
        # 类似于QwenAdapter的实现
        pass

class ModelFactory:
    @staticmethod
    def create_model(model_type: str, **kwargs) -> BaseAdapter:
        """
        创建模型实例的工厂方法
        """
        models = {
            'qwen': QwenAdapter,
            'llama': LlamaAdapter
        }
        
        if model_type not in models:
            raise ValueError(f"不支持的模型类型: {model_type}")
            
        return models[model_type](**kwargs) 