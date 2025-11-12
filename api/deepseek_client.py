"""
DeepSeek模型客户端实现
支持deepseek-chat、deepseek-coder等模型
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union
import httpx
from adalflow.core.component import Component

logger = logging.getLogger(__name__)

class DeepSeekClient(Component):
    """
    DeepSeek API客户端
    支持deepseek-chat、deepseek-coder等模型
    """

    def __init__(self, api_key: str = None, base_url: str = "https://api.deepseek.com/v1"):
        """
        初始化DeepSeek客户端

        Args:
            api_key: DeepSeek API密钥
            base_url: API基础URL
        """
        super().__init__()
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        self.base_url = base_url.rstrip('/')

        if not self.api_key:
            raise ValueError("DeepSeek API密钥未设置，请设置DEEPSEEK_API_KEY环境变量")

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "deepseek-chat",
        temperature: float = 0.7,
        top_p: float = 0.8,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        stop: Optional[Union[str, List[str]]] = None,
        **kwargs
    ) -> Union[Dict[str, Any], str]:
        """
        调用DeepSeek聊天完成API

        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            model: 模型名称，默认为deepseek-chat
            temperature: 温度参数，控制随机性
            top_p: 核采样参数
            max_tokens: 最大生成token数
            stream: 是否流式返回
            frequency_penalty: 频率惩罚参数
            presence_penalty: 存在惩罚参数
            stop: 停止词
            **kwargs: 其他参数

        Returns:
            如果stream=False，返回完整的响应对象
            如果stream=True，返回生成器或流式响应
        """
        # DeepSeek模型名称映射
        model_mapping = {
            "deepseek-chat": "deepseek-chat",
            "deepseek-coder": "deepseek-coder",
            "deepseek-chat-v1.5": "deepseek-chat-v1.5",
            "deepseek-coder-v1.5": "deepseek-coder-v1.5"
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
        if frequency_penalty is not None:
            data["frequency_penalty"] = frequency_penalty
        if presence_penalty is not None:
            data["presence_penalty"] = presence_penalty
        if stop:
            data["stop"] = stop

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
                    error_msg = f"DeepSeek API请求失败: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    raise Exception(error_msg)

        except httpx.TimeoutException:
            error_msg = "DeepSeek API请求超时"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"DeepSeek API请求异常: {str(e)}"
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


# 支持的DeepSeek模型配置
DEEPSEEK_MODELS = {
    "deepseek-chat": {
        "description": "DeepSeek Chat模型，通用对话模型",
        "context_length": 64000,
        "pricing": {"input": 0.14, "output": 0.28}  # 每百万token价格（美元）
    },
    "deepseek-coder": {
        "description": "DeepSeek Coder模型，专门用于代码生成和理解",
        "context_length": 16000,
        "pricing": {"input": 0.14, "output": 0.28}
    },
    "deepseek-chat-v1.5": {
        "description": "DeepSeek Chat V1.5模型，增强版对话模型",
        "context_length": 64000,
        "pricing": {"input": 0.14, "output": 0.28}
    },
    "deepseek-coder-v1.5": {
        "description": "DeepSeek Coder V1.5模型，增强版代码模型",
        "context_length": 16000,
        "pricing": {"input": 0.14, "output": 0.28}
    }
}