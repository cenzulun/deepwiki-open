"""
智谱AI GLM模型客户端实现
支持GLM-4.6等智谱AI模型
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union
import httpx
from adalflow.core.component import Component

logger = logging.getLogger(__name__)

class ZhipuAIClient(Component):
    """
    智谱AI API客户端
    支持GLM-4.6、GLM-4等模型
    """

    def __init__(self, api_key: str = None, base_url: str = "https://open.bigmodel.cn/api/paas/v4"):
        """
        初始化智谱AI客户端

        Args:
            api_key: 智谱AI API密钥
            base_url: API基础URL
        """
        super().__init__()
        self.api_key = api_key or os.environ.get("ZHIPUAI_API_KEY")
        self.base_url = base_url.rstrip('/')

        if not self.api_key:
            raise ValueError("智谱AI API密钥未设置，请设置ZHIPUAI_API_KEY环境变量")

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "glm-4.6",
        temperature: float = 0.7,
        top_p: float = 0.8,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[Dict[str, Any], str]:
        """
        调用智谱AI聊天完成API

        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            model: 模型名称，默认为glm-4.6
            temperature: 温度参数，控制随机性
            top_p: 核采样参数
            max_tokens: 最大生成token数
            stream: 是否流式返回
            **kwargs: 其他参数

        Returns:
            如果stream=False，返回完整的响应对象
            如果stream=True，返回生成器或流式响应
        """
        # 智谱AI模型名称映射
        model_mapping = {
            "glm-4.6": "glm-4.6",
            "glm-4": "glm-4",
            "glm-4-flash": "glm-4-flash",
            "glm-4-air": "glm-4-air",
            "glm-4-long": "glm-4-long",
            "chatglm3": "chatglm3",
            "glm-3-turbo": "glm-3-turbo"
        }

        # 使用映射后的模型名称
        actual_model = model_mapping.get(model, model)

        # 构建请求数据
        data = {
            "model": actual_model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "stream": stream
        }

        # 添加可选参数
        if max_tokens:
            data["max_tokens"] = max_tokens

        # 添加其他参数
        data.update(kwargs)

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._get_headers(),
                    json=data
                )

                if response.status_code == 200:
                    if stream:
                        return self._handle_stream_response(response)
                    else:
                        return response.json()
                else:
                    error_msg = f"智谱AI API请求失败: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    raise Exception(error_msg)

        except httpx.TimeoutException:
            error_msg = "智谱AI API请求超时"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"智谱AI API请求异常: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    async def _handle_stream_response(self, response):
        """处理流式响应"""
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data = line[6:]
                if data.strip() == "[DONE]":
                    break
                try:
                    yield json.loads(data)
                except json.JSONDecodeError:
                    continue

    def __call__(self, *args, **kwargs):
        """使对象可调用"""
        return self.chat_completion(*args, **kwargs)


# 支持的智谱AI模型配置
ZHIPUAI_MODELS = {
    "glm-4.6": {
        "description": "智谱AI GLM-4.6模型，最新版本，支持复杂推理",
        "context_length": 128000,
        "pricing": {"input": 0.05, "output": 0.15}  # 每千token价格（美元）
    },
    "glm-4": {
        "description": "智谱AI GLM-4模型，高性能版本",
        "context_length": 128000,
        "pricing": {"input": 0.03, "output": 0.09}
    },
    "glm-4-flash": {
        "description": "智谱AI GLM-4-Flash模型，快速响应版本",
        "context_length": 128000,
        "pricing": {"input": 0.01, "output": 0.03}
    },
    "glm-4-air": {
        "description": "智谱AI GLM-4-Air模型，轻量级版本",
        "context_length": 128000,
        "pricing": {"input": 0.005, "output": 0.015}
    },
    "glm-4-long": {
        "description": "智谱AI GLM-4-Long模型，长文本支持",
        "context_length": 1000000,
        "pricing": {"input": 0.1, "output": 0.3}
    },
    "chatglm3": {
        "description": "ChatGLM3模型，经典对话模型",
        "context_length": 32000,
        "pricing": {"input": 0.002, "output": 0.006}
    },
    "glm-3-turbo": {
        "description": "GLM-3-Turbo模型，高速版本",
        "context_length": 128000,
        "pricing": {"input": 0.005, "output": 0.015}
    }
}