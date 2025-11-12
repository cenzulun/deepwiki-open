# GitHub 上传指南

由于权限限制，无法直接通过命令行推送到您的仓库。请按以下步骤手动上传：

## 方法1：使用GitHub网页界面

1. **访问您的仓库**：
   - 打开 https://github.com/cenzulun/deepwiki-open

2. **上传文件**：
   - 点击 "Upload files" 按钮
   - 或者在仓库页面拖拽整个项目文件夹

3. **上传信息**：
   - Commit message: `feat: 添加本地路径解析和国产AI模型支持`
   - 选择 "Create a new branch"
   - Branch name: `feature/local-path-and-chinese-models`
   - 点击 "Propose changes"

## 方法2：使用GitHub Desktop

1. **克隆您的仓库**到本地
2. **复制项目文件**到克隆的目录
3. **通过GitHub Desktop提交并推送**

## 方法3：使用个人访问令牌

如果您想使用命令行，需要：

1. **创建GitHub个人访问令牌**：
   - 访问 https://github.com/settings/tokens
   - 点击 "Generate new token (classic)"
   - 选择 "repo" 权限
   - 复制生成的token

2. **使用token推送**：
   ```bash
   git remote set-url origin https://YOUR_TOKEN@github.com/cenzulun/deepwiki-open.git
   git push -u origin main
   ```

## 方法4：直接从GitHub网页创建仓库

如果仓库不存在：

1. 访问 https://github.com/new
2. Repository name: `deepwiki-open`
3. Description: `DeepWiki-Open with enhanced local path support and Chinese AI models`
4. 选择 Public/Private
5. 不要初始化README、.gitignore或license
6. 点击 "Create repository"
7. 按照GitHub的指示推送现有代码

## 重要说明

✅ **已完成的增强功能**：
- 本地路径解析支持（绝对路径、相对路径、Windows路径）
- 您的特殊格式：`mac/github-local/project-name`
- 智谱AI GLM-4.6模型支持
- DeepSeek模型支持
- 多种国产模型通用适配器
- 完整的测试套件和文档

📦 **需要上传的文件**：
- 所有源代码文件（api/, src/目录）
- 配置文件（package.json, pyproject.toml, Dockerfile等）
- 文档文件（README, CHINESE_MODELS_SETUP.md等）
- 测试文件

🚀 **上传后使用方法**：
1. 配置环境变量（见.env.example）
2. 安装依赖：`npm install` 和 `poetry install -C api`
3. 启动服务：`npm run dev` 和 `python -m api.main`
4. 访问 http://localhost:3000

如有问题，请参考 `CHINESE_MODELS_SETUP.md` 文件中的详细配置说明。