"""
国产模型通用适配器
支持多种国产AI模型提供商，包括：
- 月之暗面 Kimi
- 百度文心一言
- 零一万物 Yi
- MiniMax
- 字节跳动豆包
等
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union
import httpx
from adalflow.core.component import Component

logger = logging.getLogger(__name__)

class ChineseModelsClient(Component):
    """
    国产模型通用客户端
    支持多种国产AI模型提供商
    """

    def __init__(self, provider: str, api_key: str = None, base_url: str = None):
        """
        初始化国产模型客户端

        Args:
            provider: 模型提供商名称
            api_key: API密钥
            base_url: API基础URL
        """
        super().__init__()
        self.provider = provider.lower()

        # 不同提供商的配置
        provider_configs = {
            "moonshot": {
                "env_key": "MOONSHOT_API_KEY",
                "default_base_url": "https://api.moonshot.cn/v1",
                "models": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"]
            },
            "wenxin": {
                "env_key": "WENXIN_API_KEY",
                "default_base_url": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop",
                "models": ["ernie-bot", "ernie-bot-turbo", "ernie-bot-4"]
            },
            "lingyi": {
                "env_key": "LINGYI_API_KEY",
                "default_base_url": "https://api.lingyiwanwu.com/v1",
                "models": ["yi-large", "yi-medium", "yi-small", "yi-vision"]
            },
            "minimax": {
                "env_key": "MINIMAX_API_KEY",
                "default_base_url": "https://api.minimax.chat/v1",
                "models": ["abab6.5", "abab6.5-chat", "abab5.5-chat"]
            },
            "doubao": {
                "env_key": "DOUBAO_API_KEY",
                "default_base_url": "https://ark.cn-beijing.volces.com/api/v3",
                "models": ["doubao-lite-4k", "doubao-lite-32k", "doubao-lite-128k", "doubao-pro-4k", "doubao-pro-32k"]
            },
            "stepfun": {
                "env_key": "STEPFUN_API_KEY",
                "default_base_url": "https://api.stepfun.com/v1",
                "models": ["step-1-8k", "step-1-32k", "step-1-128k", "step-1-256k"]
            },
            "xunfei": {
                "env_key": "XUNFEI_API_KEY",
                "default_base_url": "https://spark-api.xf-yun.com/v1",
                "models": ["spark-lite", "spark-pro", "spark-max"]
            }
        }

        if self.provider not in provider_configs:
            raise ValueError(f"不支持的模型提供商: {provider}")

        config = provider_configs[self.provider]
        self.api_key = api_key or os.environ.get(config["env_key"])
        self.base_url = (base_url or config["default_base_url"]).rstrip('/')
        self.available_models = config["models"]

        if not self.api_key:
            raise ValueError(f"{provider} API密钥未设置，请设置{config['env_key']}环境变量")

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        # 特殊处理某些提供商的认证方式
        if self.provider == "wenxin":
            # 百度文心一言使用特殊的认证方式
            headers["Authorization"] = f"token {self.api_key}"
        elif self.provider == "minimax":
            # MiniMax可能需要额外的认证信息
            headers["X-Source"] = "openapi"

        return headers

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 0.7,
        top_p: float = 0.8,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[Dict[str, Any], str]:
        """
        调用国产模型聊天完成API

        Args:
            messages: 消息列表
            model: 模型名称，如果为None则使用默认模型
            temperature: 温度参数
            top_p: 核采样参数
            max_tokens: 最大生成token数
            stream: 是否流式返回
            **kwargs: 其他参数

        Returns:
            API响应结果
        """
        # 如果没有指定模型，使用第一个可用模型
        if not model:
            model = self.available_models[0]

        # 检查模型是否受支持
        if model not in self.available_models:
            logger.warning(f"模型 {model} 可能不受 {self.provider} 支持，但仍然尝试调用")

        # 构建请求数据
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "stream": stream
        }

        # 添加可选参数
        if max_tokens:
            data["max_tokens"] = max_tokens

        # 特殊处理某些提供商的参数格式
        if self.provider == "wenxin":
            # 百度文心一言的参数格式略有不同
            data = {
                "messages": messages,
                "temperature": temperature,
                "top_p": top_p,
                "stream": stream
            }
            if max_tokens:
                data["max_output_tokens"] = max_tokens
        elif self.provider == "minimax":
            # MiniMax可能需要特殊参数
            data["beam_width"] = 1

        # 添加其他参数
        data.update(kwargs)

        try:
            # 构建请求URL
            if self.provider == "wenxin":
                # 百度文心一言需要access_token
                url = await self._get_wenxin_url()
            else:
                url = f"{self.base_url}/chat/completions"

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    url,
                    headers=self._get_headers(),
                    json=data
                )

                if response.status_code == 200:
                    if stream:
                        return self._handle_stream_response(response)
                    else:
                        return response.json()
                else:
                    error_msg = f"{self.provider} API请求失败: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    raise Exception(error_msg)

        except httpx.TimeoutException:
            error_msg = f"{self.provider} API请求超时"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"{self.provider} API请求异常: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    async def _get_wenxin_url(self) -> str:
        """获取百度文心一言的完整URL（包含access_token）"""
        # 这里需要实现获取百度access_token的逻辑
        # 简化版本，实际应用中需要获取真实的access_token
        return f"{self.base_url}/chat/eb-instant"

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


# 支持的国产模型配置
CHINESE_MODELS_CONFIG = {
    "moonshot": {
        "name": "月之暗面 Kimi",
        "models": {
            "moonshot-v1-8k": {"context_length": 8000, "description": "Kimi 8K上下文模型"},
            "moonshot-v1-32k": {"context_length": 32000, "description": "Kimi 32K上下文模型"},
            "moonshot-v1-128k": {"context_length": 128000, "description": "Kimi 128K上下文模型"}
        }
    },
    "wenxin": {
        "name": "百度文心一言",
        "models": {
            "ernie-bot": {"context_length": 8000, "description": "文心一言 3.5"},
            "ernie-bot-turbo": {"context_length": 8000, "description": "文心一言 Turbo"},
            "ernie-bot-4": {"context_length": 8000, "description": "文心一言 4.0"}
        }
    },
    "lingyi": {
        "name": "零一万物 Yi",
        "models": {
            "yi-large": {"context_length": 200000, "description": "Yi Large 模型"},
            "yi-medium": {"context_length": 200000, "description": "Yi Medium 模型"},
            "yi-small": {"context_length": 200000, "description": "Yi Small 模型"},
            "yi-vision": {"context_length": 16000, "description": "Yi Vision 多模态模型"}
        }
    },
    "minimax": {
        "name": "MiniMax",
        "models": {
            "abab6.5": {"context_length": 200000, "description": "MiniMax ABAB6.5 模型"},
            "abab6.5-chat": {"context_length": 200000, "description": "MiniMax ABAB6.5 对话模型"},
            "abab5.5-chat": {"context_length": 32000, "description": "MiniMax ABAB5.5 对话模型"}
        }
    },
    "doubao": {
        "name": "字节跳动豆包",
        "models": {
            "doubao-lite-4k": {"context_length": 4000, "description": "豆包 Lite 4K"},
            "doubao-lite-32k": {"context_length": 32000, "description": "豆包 Lite 32K"},
            "doubao-lite-128k": {"context_length": 128000, "description": "豆包 Lite 128K"},
            "doubao-pro-4k": {"context_length": 4000, "description": "豆包 Pro 4K"},
            "doubao-pro-32k": {"context_length": 32000, "description": "豆包 Pro 32K"}
        }
    },
    "stepfun": {
        "name": "阶跃星辰 Step",
        "models": {
            "step-1-8k": {"context_length": 8000, "description": "Step-1 8K 模型"},
            "step-1-32k": {"context_length": 32000, "description": "Step-1 32K 模型"},
            "step-1-128k": {"context_length": 128000, "description": "Step-1 128K 模型"},
            "step-1-256k": {"context_length": 256000, "description": "Step-1 256K 模型"}
        }
    },
    "xunfei": {
        "name": "科大讯飞 Spark",
        "models": {
            "spark-lite": {"context_length": 4000, "description": "讯飞 Spark Lite"},
            "spark-pro": {"context_length": 8000, "description": "讯飞 Spark Pro"},
            "spark-max": {"context_length": 32000, "description": "讯飞 Spark Max"}
        }
    }
}