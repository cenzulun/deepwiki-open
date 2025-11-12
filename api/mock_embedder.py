"""
临时模拟嵌入客户端
用于在没有API密钥的情况下提供基础嵌入功能
"""

import adalflow as adal
from adalflow.core.model_client import ModelClient

class MockEmbedderClient(ModelClient):
    """模拟嵌入客户端，生成固定维度的随机向量"""

    def __init__(self, **kwargs):
        super().__init__()
        self.model_kwargs = kwargs.get('model_kwargs', {})
        self.dimensions = 256  # 默认维度

    def call(self, input, model_kwargs=None, **kwargs):
        """为文本生成模拟嵌入向量"""
        import random
        import hashlib

        if isinstance(input, str):
            input = [input]

        embeddings = []
        for text in input:
            # 基于文本内容生成一致的随机向量
            hash_obj = hashlib.md5(text.encode())
            random.seed(hash_obj.hexdigest())

            # 生成固定维度的向量
            embedding = [random.uniform(-1, 1) for _ in range(self.dimensions)]
            embeddings.append(embedding)

        return {"embeddings": embeddings}

    def encode(self, texts, **kwargs):
        """为文本生成模拟嵌入向量（兼容性方法）"""
        result = self.call(texts, **kwargs)
        return result.get("embeddings", [])

    def get_embedding_dimension(self):
        """返回嵌入向量维度"""
        return self.dimensions

    def _combine_input_and_model_kwargs(self, input, model_kwargs):
        """组合输入和模型参数的方法"""
        return {
            "input": input,
            **model_kwargs
        }