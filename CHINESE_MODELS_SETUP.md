# 国产模型集成使用指南

本文档说明如何在 DeepWiki-Open 中配置和使用国产AI模型。

## 支持的国产模型

### 1. 智谱AI GLM系列
- **GLM-4.6**: 最新版本，支持复杂推理
- **GLM-4**: 高性能版本
- **GLM-4-Flash**: 快速响应版本
- **GLM-4-Air**: 轻量级版本
- **GLM-4-Long**: 长文本支持（100万token上下文）
- **ChatGLM3**: 经典对话模型
- **GLM-3-Turbo**: 高速版本

### 2. DeepSeek系列
- **DeepSeek-Chat**: 通用对话模型
- **DeepSeek-Coder**: 专门用于代码生成和理解
- **DeepSeek-Chat-V1.5**: 增强版对话模型
- **DeepSeek-Coder-V1.5**: 增强版代码模型

### 3. 其他国产模型（通过通用适配器）
- **月之暗面 Kimi**: 8K/32K/128K上下文版本
- **百度文心一言**: ERNIE-Bot系列
- **零一万物 Yi**: Yi-Large/Yi-Medium/Yi-Small
- **MiniMax**: ABAB6.5系列模型
- **字节跳动豆包**: Lite/Pro版本
- **阶跃星辰 Step**: Step-1系列模型
- **科大讯飞 Spark**: Lite/Pro/Max版本

## 配置步骤

### 1. 环境变量配置

复制环境变量示例文件：
```bash
cp .env.example .env
```

编辑 `.env` 文件，添加所需的API密钥：

```bash
# 智谱AI API密钥（用于GLM模型）
ZHIPUAI_API_KEY=your_zhipuai_api_key_here

# DeepSeek API密钥
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# 阿里云通义千问API密钥
DASHSCOPE_API_KEY=your_dashscope_api_key_here

# 启用国产模型配置
ENABLE_CHINESE_MODELS=true

# 其他可选的国产模型密钥
# MOONSHOT_API_KEY=your_moonshot_api_key_here
# WENXIN_API_KEY=your_wenxin_api_key_here
# LINGYI_API_KEY=your_lingyi_api_key_here
# MINIMAX_API_KEY=your_minimax_api_key_here
# DOUBAO_API_KEY=your_doubao_api_key_here
# STEPFUN_API_KEY=your_stepfun_api_key_here
# XUNFEI_API_KEY=your_xunfei_api_key_here
```

### 2. API密钥获取

#### 智谱AI (GLM-4.6)
1. 访问 [智谱AI开放平台](https://open.bigmodel.cn/)
2. 注册并登录
3. 创建API Key
4. 设置环境变量 `ZHIPUAI_API_KEY`

#### DeepSeek
1. 访问 [DeepSeek开放平台](https://platform.deepseek.com/)
2. 注册并登录
3. 创建API Key
4. 设置环境变量 `DEEPSEEK_API_KEY`

#### 其他国产模型
参考各平台的官方文档获取API密钥。

### 3. 启动服务

```bash
# 启动后端服务
python -m api.main

# 启动前端服务
npm run dev
```

## 使用方法

### 1. 在前端选择模型

1. 打开 [http://localhost:3000](http://localhost:3000)
2. 输入仓库URL或本地路径
3. 点击"生成Wiki"按钮
4. 在配置弹窗中选择模型提供商：
   - 选择 "智谱AI" 使用GLM-4.6
   - 选择 "DeepSeek" 使用DeepSeek模型
   - 选择其他国产模型（如果已启用）

### 2. 支持的本地路径格式

系统现在支持多种本地路径格式：

- **绝对路径**: `/Users/username/project` 或 `C:\Users\username\project`
- **相对路径**: `./api`, `../test`, `src/components`
- **当前目录**: `.`
- **用户目录**: `~/project`
- **您的GitHub格式**: `mac/github-local/project-name`

### 3. 配置选项

每个模型支持不同的配置参数：

- **温度参数**: 控制生成内容的随机性（0.0-1.0）
- **Top-p**: 核采样参数（0.0-1.0）
- **最大Token数**: 限制生成内容的长度

## 故障排除

### 1. 导入错误

如果遇到模块导入错误：
```bash
# 安装依赖
python -m pip install poetry
poetry install -C api
```

### 2. API密钥错误

确保：
- API密钥正确设置
- 账户有足够的余额
- API密钥有相应的权限

### 3. 模型调用失败

检查：
- 网络连接
- API密钥是否有效
- 模型名称是否正确

## 性能优化建议

### 1. 模型选择

- **代码分析**: 推荐使用DeepSeek-Coder或GLM-4
- **文档生成**: 推荐使用GLM-4.6或DeepSeek-Chat
- **快速响应**: 使用Flash或Turbo版本
- **长文档**: 使用GLM-4-Long或Yi-Large

### 2. 参数调优

- **代码任务**: 温度 0.3-0.5，追求准确性
- **创意任务**: 温度 0.7-0.9，增加创造性
- **摘要任务**: 温度 0.3-0.5，保持简洁

### 3. 成本控制

- 使用Flash/Lite版本降低成本
- 合理设置最大Token数
- 利用缓存避免重复计算

## 测试

运行测试脚本验证配置：

```bash
# 测试路径解析功能
python3 test_path_parsing.py

# 测试国产模型集成
python3 test_chinese_models.py

# 测试本地路径API（需要后端服务运行）
python3 test_local_path.py
```

## 更新和扩展

### 添加新的国产模型

1. 在 `api/chinese_models_client.py` 中添加新提供商配置
2. 在 `api/config/chinese_models.json` 中添加模型配置
3. 更新环境变量支持
4. 运行测试验证

### 贡献代码

欢迎提交Pull Request来支持更多国产模型！

## 技术支持

如果遇到问题：
1. 查看日志文件：`api/logs/application.log`
2. 运行测试脚本诊断问题
3. 检查环境变量配置
4. 验证API密钥有效性

## 许可证

本项目遵循 MIT 许可证。