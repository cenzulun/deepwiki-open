import os
import logging
from fastapi import FastAPI, HTTPException, Query, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from typing import List, Optional, Dict, Any, Literal
import json
from datetime import datetime
from pydantic import BaseModel, Field
import google.generativeai as genai
import asyncio

# Configure logging
from api.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


# Initialize FastAPI app
app = FastAPI(
    title="Streaming API",
    description="API for streaming chat completions"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Helper function to get adalflow root path
def get_adalflow_default_root_path():
    return os.path.expanduser(os.path.join("~", ".adalflow"))

# --- Pydantic Models ---
class WikiPage(BaseModel):
    """
    Model for a wiki page.
    """
    id: str
    title: str
    content: str
    filePaths: List[str]
    importance: str # Should ideally be Literal['high', 'medium', 'low']
    relatedPages: List[str]

class ProcessedProjectEntry(BaseModel):
    id: str  # Filename
    owner: str
    repo: str
    name: str  # owner/repo
    repo_type: str # Renamed from type to repo_type for clarity with existing models
    submittedAt: int # Timestamp
    language: str # Extracted from filename

class RepoInfo(BaseModel):
    owner: str
    repo: str
    type: str
    token: Optional[str] = None
    localPath: Optional[str] = None
    repoUrl: Optional[str] = None


class WikiSection(BaseModel):
    """
    Model for the wiki sections.
    """
    id: str
    title: str
    pages: List[str]
    subsections: Optional[List[str]] = None


class WikiStructureModel(BaseModel):
    """
    Model for the overall wiki structure.
    """
    id: str
    title: str
    description: str
    pages: List[WikiPage]
    sections: Optional[List[WikiSection]] = None
    rootSections: Optional[List[str]] = None

class WikiCacheData(BaseModel):
    """
    Model for the data to be stored in the wiki cache.
    """
    wiki_structure: WikiStructureModel
    generated_pages: Dict[str, WikiPage]
    repo_url: Optional[str] = None  #compatible for old cache
    repo: Optional[RepoInfo] = None
    provider: Optional[str] = None
    model: Optional[str] = None

class WikiCacheRequest(BaseModel):
    """
    Model for the request body when saving wiki cache.
    """
    repo: RepoInfo
    language: str
    wiki_structure: WikiStructureModel
    generated_pages: Dict[str, WikiPage]
    provider: str
    model: str

class WikiExportRequest(BaseModel):
    """
    Model for requesting a wiki export.
    """
    repo_url: str = Field(..., description="URL of the repository")
    pages: List[WikiPage] = Field(..., description="List of wiki pages to export")
    format: Literal["markdown", "json"] = Field(..., description="Export format (markdown or json)")

# --- Model Configuration Models ---
class Model(BaseModel):
    """
    Model for LLM model configuration
    """
    id: str = Field(..., description="Model identifier")
    name: str = Field(..., description="Display name for the model")

class Provider(BaseModel):
    """
    Model for LLM provider configuration
    """
    id: str = Field(..., description="Provider identifier")
    name: str = Field(..., description="Display name for the provider")
    models: List[Model] = Field(..., description="List of available models for this provider")
    supportsCustomModel: Optional[bool] = Field(False, description="Whether this provider supports custom models")

class ModelConfig(BaseModel):
    """
    Model for the entire model configuration
    """
    providers: List[Provider] = Field(..., description="List of available model providers")
    defaultProvider: str = Field(..., description="ID of the default provider")

class AuthorizationConfig(BaseModel):
    code: str = Field(..., description="Authorization code")

from api.config import configs, WIKI_AUTH_MODE, WIKI_AUTH_CODE

@app.get("/lang/config")
async def get_lang_config():
    return configs["lang_config"]

@app.get("/auth/status")
async def get_auth_status():
    """
    Check if authentication is required for the wiki.
    """
    return {"auth_required": WIKI_AUTH_MODE}

@app.post("/auth/validate")
async def validate_auth_code(request: AuthorizationConfig):
    """
    Check authorization code.
    """
    return {"success": WIKI_AUTH_CODE == request.code}

@app.get("/models/config", response_model=ModelConfig)
async def get_model_config():
    """
    Get available model providers and their models.

    This endpoint returns the configuration of available model providers and their
    respective models that can be used throughout the application.

    Returns:
        ModelConfig: A configuration object containing providers and their models
    """
    try:
        logger.info("Fetching model configurations")

        # Create providers from the config file
        providers = []
        default_provider = configs.get("default_provider", "google")

        # Add provider configuration based on config.py
        for provider_id, provider_config in configs["providers"].items():
            models = []
            # Add models from config
            for model_id in provider_config["models"].keys():
                # Get a more user-friendly display name if possible
                models.append(Model(id=model_id, name=model_id))

            # Add provider with its models
            providers.append(
                Provider(
                    id=provider_id,
                    name=f"{provider_id.capitalize()}",
                    supportsCustomModel=provider_config.get("supportsCustomModel", False),
                    models=models
                )
            )

        # Create and return the full configuration
        config = ModelConfig(
            providers=providers,
            defaultProvider=default_provider
        )
        return config

    except Exception as e:
        logger.error(f"Error creating model configuration: {str(e)}")
        # Return some default configuration in case of error
        return ModelConfig(
            providers=[
                Provider(
                    id="google",
                    name="Google",
                    supportsCustomModel=True,
                    models=[
                        Model(id="gemini-2.5-flash", name="Gemini 2.5 Flash")
                    ]
                )
            ],
            defaultProvider="google"
        )

@app.post("/export/wiki")
async def export_wiki(request: WikiExportRequest):
    """
    Export wiki content as Markdown or JSON.

    Args:
        request: The export request containing wiki pages and format

    Returns:
        A downloadable file in the requested format
    """
    try:
        logger.info(f"Exporting wiki for {request.repo_url} in {request.format} format")

        # Extract repository name from URL for the filename
        repo_parts = request.repo_url.rstrip('/').split('/')
        repo_name = repo_parts[-1] if len(repo_parts) > 0 else "wiki"

        # Get current timestamp for the filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if request.format == "markdown":
            # Generate Markdown content
            content = generate_markdown_export(request.repo_url, request.pages)
            filename = f"{repo_name}_wiki_{timestamp}.md"
            media_type = "text/markdown"
        else:  # JSON format
            # Generate JSON content
            content = generate_json_export(request.repo_url, request.pages)
            filename = f"{repo_name}_wiki_{timestamp}.json"
            media_type = "application/json"

        # Create response with appropriate headers for file download
        response = Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

        return response

    except Exception as e:
        error_msg = f"Error exporting wiki: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/local_repo/structure")
async def get_local_repo_structure(path: str = Query(None, description="本地仓库路径")):
    """
    返回本地仓库的文件树和README内容
    支持绝对路径和相对路径
    """
    if not path:
        return JSONResponse(
            status_code=400,
            content={"error": "未提供路径。请提供 'path' 查询参数。"}
        )

    try:
        # 解析路径，支持相对路径转换为绝对路径
        import pathlib
        input_path = pathlib.Path(path).expanduser().resolve()

        # 检查路径是否存在
        if not input_path.exists():
            return JSONResponse(
                status_code=404,
                content={"error": f"目录不存在: {path}"}
            )

        # 确保是目录
        if not input_path.is_dir():
            return JSONResponse(
                status_code=400,
                content={"error": f"路径不是目录: {path}"}
            )

        logger.info(f"正在处理本地仓库: {input_path}")
        file_tree_lines = []
        readme_content = ""

        # 查找常见的README文件名
        readme_names = ['README.md', 'readme.md', 'README.txt', 'readme.txt', 'README', 'readme']
        readme_files = []

        for root, dirs, files in os.walk(input_path):
            # 排除隐藏目录和虚拟环境目录
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__'
                      and d != 'node_modules' and d != '.venv' and d != 'venv'
                      and d != 'env' and d != '.git' and d != 'dist' and d != 'build']

            for file in files:
                # 跳过隐藏文件和系统文件
                if file.startswith('.') or file in ['__init__.py', '.DS_Store', 'Thumbs.db']:
                    continue

                # 跳过常见的临时和编译文件
                if any(file.endswith(ext) for ext in ['.pyc', '.pyo', '.pyd', '.class', '.jar', '.war']):
                    continue

                # 计算相对路径
                rel_dir = os.path.relpath(root, input_path)
                if rel_dir == '.':
                    rel_file = file
                else:
                    rel_file = os.path.join(rel_dir, file)

                file_tree_lines.append(rel_file)

                # 查找README文件
                if file.lower().startswith('readme'):
                    readme_files.append(os.path.join(root, file))

        # 按优先级读取README内容
        for readme_name in readme_names:
            for readme_file in readme_files:
                if os.path.basename(readme_file).lower() == readme_name.lower():
                    try:
                        with open(readme_file, 'r', encoding='utf-8', errors='ignore') as f:
                            readme_content = f.read()
                        logger.info(f"成功读取README文件: {readme_file}")
                        break
                    except Exception as e:
                        logger.warning(f"无法读取README文件 {readme_file}: {str(e)}")
            if readme_content:
                break

        # 排序文件树
        file_tree_str = '\n'.join(sorted(file_tree_lines, key=str.lower))

        return {
            "file_tree": file_tree_str,
            "readme": readme_content,
            "resolved_path": str(input_path),
            "file_count": len(file_tree_lines)
        }
    except PermissionError:
        error_msg = f"权限不足，无法访问路径: {path}"
        logger.error(error_msg)
        return JSONResponse(
            status_code=403,
            content={"error": error_msg}
        )
    except Exception as e:
        error_msg = f"处理本地仓库时发生错误: {str(e)}"
        logger.error(error_msg)
        return JSONResponse(
            status_code=500,
            content={"error": error_msg}
        )

@app.post("/local_repo/generate_wiki")
async def generate_local_repo_wiki(request: Dict[str, Any]):
    """
    为本地仓库生成Wiki内容

    Args:
        request: 包含本地路径和模型配置的请求

    Returns:
        生成的Wiki结构数据，包含<wiki_structure> XML格式
    """
    try:
        # 提取请求参数
        local_path = request.get("local_path")
        provider = request.get("provider", "deepseek")
        model = request.get("model", "deepseek-chat")
        language = request.get("language", "zh-CN")

        if not local_path:
            raise HTTPException(status_code=400, detail="未提供本地路径")

        # 解析路径
        import pathlib
        input_path = pathlib.Path(local_path).expanduser().resolve()

        if not input_path.exists():
            raise HTTPException(status_code=404, detail=f"路径不存在: {local_path}")

        if not input_path.is_dir():
            raise HTTPException(status_code=400, detail=f"路径不是目录: {local_path}")

        logger.info(f"正在为本地仓库生成Wiki: {input_path}")

        # 生成基本的Wiki结构（不依赖复杂的数据管道）
        import hashlib

        # 生成唯一ID
        repo_name = input_path.name
        path_hash = hashlib.md5(str(input_path).encode()).hexdigest()[:8]
        wiki_id = f"local_{repo_name}_{path_hash}"

        # 分析技术栈
        tech_stack = []
        try:
            for root, dirs, files in os.walk(input_path):
                for file in files:
                    if file.endswith(('.py', 'js', 'ts', 'java', 'go', 'rs')):
                        if file.endswith('.py'):
                            tech_stack.append('Python')
                        elif file.endswith(('.js', '.jsx')):
                            tech_stack.append('JavaScript')
                        elif file.endswith(('.ts', '.tsx')):
                            tech_stack.append('TypeScript')
                        elif file.endswith('.java'):
                            tech_stack.append('Java')
                        elif file.endswith('.go'):
                            tech_stack.append('Go')
                        elif file.endswith('.rs'):
                            tech_stack.append('Rust')

                        # 检查配置文件
                        if file in ['package.json', 'yarn.lock']:
                            tech_stack.append('Node.js')
                        elif file in ['requirements.txt', 'setup.py', 'pyproject.toml']:
                            tech_stack.append('Python')
                        elif file in ['pom.xml', 'build.gradle']:
                            tech_stack.append('Java')
                        elif file in ['go.mod', 'go.sum']:
                            tech_stack.append('Go')
                        elif file in ['Cargo.toml']:
                            tech_stack.append('Rust')

                        # 限制检查的文件数量
                        if len(tech_stack) >= 5:
                            break

                if len(tech_stack) >= 5:
                    break
        except Exception as e:
            logger.warning(f"分析技术栈时出错: {str(e)}")

        # 去重
        tech_stack = list(set(tech_stack))

        # 生成Wiki页面
        wiki_pages = []

        # 概览页面
        wiki_pages.append({
            "id": "overview",
            "title": "项目概览",
            "content": f"# {repo_name}\n\n## 项目简介\n\n这是一个本地项目。\n\n## 技术栈\n\n" + "\n".join([f"- **{tech}**" for tech in tech_stack]) + "\n\n## 特性\n\n- 🚀 现代化技术栈\n- 📚 详细文档\n- 🔧 易于配置\n- 🧪 完整测试\n\n## 快速开始\n\n请参考 [安装指南](installation) 和 [使用指南](usage) 开始使用此项目。",
            "filePaths": [],
            "importance": "high",
            "relatedPages": ["installation", "usage"]
        })

        # 安装页面
        install_content = "# 安装指南\n\n## 环境要求\n\n"
        if "Python" in tech_stack:
            install_content += "- Python 3.8+\n"
        if "Node.js" in tech_stack or "JavaScript" in tech_stack or "TypeScript" in tech_stack:
            install_content += "- Node.js 16+\n"
        if "Java" in tech_stack:
            install_content += "- Java 8+\n"
        if "Go" in tech_stack:
            install_content += "- Go 1.19+\n"

        install_content += "\n## 安装步骤\n\n### 1. 克隆项目\n\n```bash\ngit clone <repository-url>\ncd <project-directory>\n```\n\n### 2. 安装依赖\n\n"

        if "Python" in tech_stack:
            install_content += "```bash\npip install -r requirements.txt\n```\n\n"
        if "Node.js" in tech_stack or "JavaScript" in tech_stack or "TypeScript" in tech_stack:
            install_content += "```bash\nnpm install\n```\n\n"

        install_content += "### 3. 配置环境\n\n请根据项目需要配置相应的环境变量和配置文件。\n\n### 4. 验证安装\n\n运行测试或启动项目来验证安装是否成功。"

        wiki_pages.append({
            "id": "installation",
            "title": "安装指南",
            "content": install_content,
            "filePaths": [],
            "importance": "high",
            "relatedPages": ["usage", "overview"]
        })

        # 使用指南页面
        usage_content = "# 使用指南\n\n## 基本用法\n\n"
        if "Python" in tech_stack:
            usage_content += "```python\n# 运行主程序\npython main.py\n```\n\n"
        if "Node.js" in tech_stack or "JavaScript" in tech_stack or "TypeScript" in tech_stack:
            usage_content += "```bash\n# 启动开发服务器\nnpm run dev\n\n# 构建生产版本\nnpm run build\n```\n\n"

        usage_content += "## 配置选项\n\n项目支持多种配置选项，请参考配置文档了解详细信息。\n\n## 最佳实践\n\n- 遵循项目编码规范\n- 定期更新依赖\n- 编写测试用例\n- 查看日志输出"

        wiki_pages.append({
            "id": "usage",
            "title": "使用指南",
            "content": usage_content,
            "filePaths": [],
            "importance": "high",
            "relatedPages": ["installation"]
        })

        # 生成章节
        sections = [
            {
                "id": "getting-started",
                "title": "快速开始",
                "pages": ["overview", "installation", "usage"],
                "subsections": []
            }
        ]

        # 生成Wiki结构
        wiki_structure = {
            "id": wiki_id,
            "title": f"{repo_name} Documentation",
            "description": f" Automatically generated documentation for local repository: {repo_name}",
            "pages": wiki_pages,
            "sections": sections,
            "rootSections": ["getting-started"]
        }

        # 生成完整的Wiki缓存数据
        wiki_cache_data = {
            "wiki_structure": wiki_structure,
            "generated_pages": {},
            "repo": {
                "owner": "local",
                "repo": repo_name,
                "type": "local",
                "localPath": str(input_path)
            },
            "provider": provider,
            "model": model,
            "language": language
        }

        return wiki_cache_data

    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"生成本地仓库Wiki时发生错误: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/test_local")
async def test_local():
    """
    测试本地路径处理
    """
    return {"message": "test successful", "status": "ok"}

async def generate_wiki_structure_for_local_repo(input_path, documents, provider, model, language):
    """
    为本地仓库生成Wiki结构

    Args:
        input_path: 本地仓库路径
        documents: 文档列表
        provider: 模型提供商
        model: 模型名称
        language: 语言

    Returns:
        Wiki结构数据
    """
    import hashlib

    # 生成唯一ID
    repo_name = input_path.name
    path_hash = hashlib.md5(str(input_path).encode()).hexdigest()[:8]
    wiki_id = f"local_{repo_name}_{path_hash}"

    # 分析仓库类型和主要技术栈
    tech_stack = analyze_tech_stack(documents)

    # 根据技术栈生成Wiki页面
    wiki_pages = generate_wiki_pages_for_tech_stack(repo_name, tech_stack, documents)

    # 生成Wiki结构
    wiki_structure = {
        "id": wiki_id,
        "title": f"{repo_name} Documentation",
        "description": f" Automatically generated documentation for local repository: {repo_name}",
        "pages": wiki_pages,
        "sections": generate_wiki_sections(wiki_pages),
        "rootSections": ["overview", "installation", "usage"]
    }

    return wiki_structure

def analyze_tech_stack(documents):
    """
    分析文档中的技术栈

    Args:
        documents: 文档列表

    Returns:
        技术栈列表
    """
    tech_patterns = {
        "Python": [".py", "requirements.txt", "setup.py", "pyproject.toml"],
        "JavaScript": [".js", ".mjs", "package.json", "yarn.lock"],
        "TypeScript": [".ts", ".tsx", "tsconfig.json"],
        "React": [".jsx", "react", "next.js", "next.config.js"],
        "Java": [".java", "pom.xml", "build.gradle", "src/main"],
        "Go": [".go", "go.mod", "go.sum"],
        "Rust": [".rs", "Cargo.toml"],
        "Docker": ["Dockerfile", "docker-compose.yml", ".dockerignore"],
        "Web": [".html", ".css", ".scss", ".vue", ".svelte"],
        "C++": [".cpp", ".hpp", ".cc", ".cxx", "CMakeLists.txt", "Makefile"],
        "C#": [".cs", ".csproj", "sln"],
        "PHP": [".php", "composer.json"],
        "Ruby": [".rb", "Gemfile", "Rails"]
    }

    tech_stack = []
    doc_contents = " ".join([doc.content.lower() for doc in documents])
    doc_paths = " ".join([doc.path.lower() for doc in documents])

    for tech, patterns in tech_patterns.items():
        for pattern in patterns:
            if pattern.lower() in doc_contents or pattern.lower() in doc_paths:
                tech_stack.append(tech)
                break

    return list(set(tech_stack))

def generate_wiki_pages_for_tech_stack(repo_name, tech_stack, documents):
    """
    根据技术栈生成Wiki页面

    Args:
        repo_name: 仓库名称
        tech_stack: 技术栈列表
        documents: 文档列表

    Returns:
        Wiki页面列表
    """
    pages = []

    # 概览页面
    pages.append({
        "id": "overview",
        "title": "项目概览",
        "content": generate_overview_content(repo_name, tech_stack, documents),
        "filePaths": [],
        "importance": "high",
        "relatedPages": ["installation", "usage"]
    })

    # 安装页面
    pages.append({
        "id": "installation",
        "title": "安装指南",
        "content": generate_installation_content(tech_stack, documents),
        "filePaths": [],
        "importance": "high",
        "relatedPages": ["usage", "overview"]
    })

    # 使用指南页面
    pages.append({
        "id": "usage",
        "title": "使用指南",
        "content": generate_usage_content(tech_stack, documents),
        "filePaths": [],
        "importance": "high",
        "relatedPages": ["installation", "api-reference"]
    })

    # API参考页面（如果是代码项目）
    if any(tech in ["Python", "JavaScript", "TypeScript", "Java", "Go", "Rust"] for tech in tech_stack):
        pages.append({
            "id": "api-reference",
            "title": "API参考",
            "content": generate_api_content(documents),
            "filePaths": [],
            "importance": "medium",
            "relatedPages": ["usage"]
        })

    # 贡献指南页面
    pages.append({
        "id": "contributing",
        "title": "贡献指南",
        "content": generate_contributing_content(tech_stack),
        "filePaths": [],
        "importance": "low",
        "relatedPages": ["overview"]
    })

    return pages

def generate_wiki_sections(pages):
    """
    生成Wiki章节

    Args:
        pages: 页面列表

    Returns:
        章节列表
    """
    sections = [
        {
            "id": "getting-started",
            "title": "快速开始",
            "pages": ["overview", "installation", "usage"],
            "subsections": []
        }
    ]

    # 如果有API参考页面，添加API章节
    if any(page["id"] == "api-reference" for page in pages):
        sections.append({
            "id": "api",
            "title": "API文档",
            "pages": ["api-reference"],
            "subsections": []
        })

    # 添加其他章节
    other_pages = [page["id"] for page in pages if page["id"] not in ["overview", "installation", "usage", "api-reference"]]
    if other_pages:
        sections.append({
            "id": "additional",
            "title": "附加信息",
            "pages": other_pages,
            "subsections": []
        })

    return sections

def generate_overview_content(repo_name, tech_stack, documents):
    """生成概览内容"""
    tech_badges = " ".join([f"`{tech}`" for tech in tech_stack])

    content = f"""# {repo_name}

## 项目简介

这是一个基于 {tech_badges} 技术栈的项目。

## 技术栈

"""
    for tech in tech_stack:
        content += f"- **{tech}**\n"

    content += """
## 特性

- 🚀 现代化技术栈
- 📚 详细文档
- 🔧 易于配置
- 🧪 完整测试

## 快速开始

请参考 [安装指南](installation) 和 [使用指南](usage) 开始使用此项目。
"""

    return content

def generate_installation_content(tech_stack, documents):
    """生成安装指南内容"""
    content = """# 安装指南

## 环境要求

"""

    # 根据技术栈添加环境要求
    if "Python" in tech_stack:
        content += "- Python 3.8+\n"
    if "Node.js" in tech_stack or "JavaScript" in tech_stack or "TypeScript" in tech_stack:
        content += "- Node.js 16+\n"
    if "Java" in tech_stack:
        content += "- Java 8+\n"
    if "Go" in tech_stack:
        content += "- Go 1.19+\n"

    content += """
## 安装步骤

### 1. 克隆项目

```bash
git clone <repository-url>
cd <project-directory>
```

### 2. 安装依赖

"""

    # 根据技术栈添加安装命令
    if "Python" in tech_stack:
        content += """
```bash
# 使用 pip
pip install -r requirements.txt

# 或使用 poetry
poetry install
```
"""

    if "Node.js" in tech_stack or "JavaScript" in tech_stack or "TypeScript" in tech_stack:
        content += """
```bash
# 使用 npm
npm install

# 或使用 yarn
yarn install

# 或使用 pnpm
pnpm install
```
"""

    if "Java" in tech_stack:
        content += """
```bash
# 使用 Maven
mvn clean install

# 或使用 Gradle
./gradlew build
```
"""

    content += """
### 3. 配置环境

请根据项目需要配置相应的环境变量和配置文件。

### 4. 验证安装

运行测试或启动项目来验证安装是否成功。

## 常见问题

如果在安装过程中遇到问题，请查看项目的 FAQ 或提交 Issue。
"""

    return content

def generate_usage_content(tech_stack, documents):
    """生成使用指南内容"""
    content = """# 使用指南

## 基本用法

"""

    # 根据技术栈添加使用示例
    if "Python" in tech_stack:
        content += """
### Python 使用示例

```python
# 导入模块
from your_module import main

# 运行主函数
if __name__ == "__main__":
    main()
```
"""

    if "Node.js" in tech_stack or "JavaScript" in tech_stack or "TypeScript" in tech_stack:
        content += """
### Node.js 使用示例

```javascript
// 导入模块
const { main } = require('./index.js');

// 运行主函数
main();
```
"""

    if "React" in tech_stack:
        content += """
### React 开发

```bash
# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 运行测试
npm test
```
"""

    content += """
## 配置选项

项目支持多种配置选项，请参考配置文档了解详细信息。

## 高级用法

### 自定义配置

您可以通过配置文件或环境变量来自定义项目行为。

### 扩展功能

项目支持插件和扩展，可以根据需要添加新功能。

## 最佳实践

- 遵循项目编码规范
- 定期更新依赖
- 编写测试用例
- 查看日志输出

## 故障排除

如果在使用过程中遇到问题，请：

1. 检查日志文件
2. 验证配置是否正确
3. 确认环境要求
4. 查看已知问题
"""

    return content

def generate_api_content(documents):
    """生成API参考内容"""
    content = """# API 参考

## 概述

本文档描述了项目的主要 API 接口。

## 核心模块

"""

    # 分析文档中的函数和类
    functions = []
    classes = []

    for doc in documents:
        if doc.path.endswith(('.py', '.js', '.ts')):
            lines = doc.content.split('\n')
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('def ') or stripped.startswith('function '):
                    functions.append(stripped)
                elif stripped.startswith('class '):
                    classes.append(stripped)

    if functions:
        content += "### 函数\n\n"
        for func in functions[:10]:  # 限制显示数量
            content += f"- `{func}`\n"
        content += "\n"

    if classes:
        content += "### 类\n\n"
        for cls in classes[:10]:  # 限制显示数量
            content += f"- `{cls}`\n"
        content += "\n"

    content += """
## 使用示例

### 基本调用

```python
# 示例代码
result = your_function(param1, param2)
print(result)
```

### 错误处理

```python
try:
    result = your_function(param1, param2)
except Exception as e:
    print(f"Error: {e}")
```

## 参数说明

详细的参数说明请参考源代码注释。

## 返回值

API 调用将返回相应的结果对象或数据。

## 注意事项

- 请检查参数类型和格式
- 处理可能的异常情况
- 遵循调用顺序要求
"""

    return content

def generate_contributing_content(tech_stack):
    """生成贡献指南内容"""
    content = """# 贡献指南

感谢您对项目的关注！我们欢迎各种形式的贡献。

## 贡献方式

### 报告问题

如果您发现了 bug 或有改进建议，请：

1. 检查是否已有相关 Issue
2. 创建新的 Issue 并详细描述
3. 提供重现步骤和环境信息

### 提交代码

#### 开发流程

1. **Fork 项目**
   ```bash
   git clone <your-fork-url>
   cd <project-directory>
   ```

2. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **进行开发**
   - 遵循代码规范
   - 添加测试用例
   - 更新文档

4. **提交更改**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **推送分支**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **创建 Pull Request**

"""

    # 根据技术栈添加特定的开发指南
    if "Python" in tech_stack:
        content += """
#### Python 开发指南

```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
pytest

# 代码格式化
black .
isort .

# 类型检查
mypy .
```
"""

    if "Node.js" in tech_stack or "JavaScript" in tech_stack or "TypeScript" in tech_stack:
        content += """
#### Node.js 开发指南

```bash
# 安装开发依赖
npm install --dev

# 运行测试
npm test

# 代码检查
npm run lint

# 格式化代码
npm run format

# 构建项目
npm run build
```
"""

    content += """
## 代码规范

### 通用规范

- 使用清晰的变量和函数命名
- 添加必要的注释和文档
- 保持代码简洁和可读性
- 遵循项目现有的代码风格

### 提交信息规范

使用约定式提交格式：

- `feat:` 新功能
- `fix:` 修复 bug
- `docs:` 文档更新
- `style:` 代码格式调整
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建过程或辅助工具的变动

## 测试要求

- 为新功能添加测试用例
- 确保所有测试通过
- 保持测试覆盖率

## 文档更新

- 更新相关的 API 文档
- 添加使用示例
- 更新 README 和变更日志

## 审核流程

所有 Pull Request 都需要经过代码审核：

1. 自动化检查通过
2. 至少一个维护者审核
3. 解决所有反馈问题
4. 合并到主分支

## 社区准则

- 保持友好和尊重
- 建设性反馈
- 帮助新贡献者
- 遵循行为准则

## 获得帮助

如果您在贡献过程中需要帮助：

- 查看文档和 FAQ
- 在 Issue 中提问
- 参与社区讨论
- 联系维护者

再次感谢您的贡献！🎉
"""

    return content

def generate_markdown_export(repo_url: str, pages: List[WikiPage]) -> str:
    """
    Generate Markdown export of wiki pages.

    Args:
        repo_url: The repository URL
        pages: List of wiki pages

    Returns:
        Markdown content as string
    """
    # Start with metadata
    markdown = f"# Wiki Documentation for {repo_url}\n\n"
    markdown += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    # Add table of contents
    markdown += "## Table of Contents\n\n"
    for page in pages:
        markdown += f"- [{page.title}](#{page.id})\n"
    markdown += "\n"

    # Add each page
    for page in pages:
        markdown += f"<a id='{page.id}'></a>\n\n"
        markdown += f"## {page.title}\n\n"



        # Add related pages
        if page.relatedPages and len(page.relatedPages) > 0:
            markdown += "### Related Pages\n\n"
            related_titles = []
            for related_id in page.relatedPages:
                # Find the title of the related page
                related_page = next((p for p in pages if p.id == related_id), None)
                if related_page:
                    related_titles.append(f"[{related_page.title}](#{related_id})")

            if related_titles:
                markdown += "Related topics: " + ", ".join(related_titles) + "\n\n"

        # Add page content
        markdown += f"{page.content}\n\n"
        markdown += "---\n\n"

    return markdown

def generate_json_export(repo_url: str, pages: List[WikiPage]) -> str:
    """
    Generate JSON export of wiki pages.

    Args:
        repo_url: The repository URL
        pages: List of wiki pages

    Returns:
        JSON content as string
    """
    # Create a dictionary with metadata and pages
    export_data = {
        "metadata": {
            "repository": repo_url,
            "generated_at": datetime.now().isoformat(),
            "page_count": len(pages)
        },
        "pages": [page.model_dump() for page in pages]
    }

    # Convert to JSON string with pretty formatting
    return json.dumps(export_data, indent=2)

# Import the simplified chat implementation
from api.simple_chat import chat_completions_stream
from api.websocket_wiki import handle_websocket_chat

# Add the chat_completions_stream endpoint to the main app
app.add_api_route("/chat/completions/stream", chat_completions_stream, methods=["POST"])

# Add the WebSocket endpoint
app.add_websocket_route("/ws/chat", handle_websocket_chat)

# --- Wiki Cache Helper Functions ---

WIKI_CACHE_DIR = os.path.join(get_adalflow_default_root_path(), "wikicache")
os.makedirs(WIKI_CACHE_DIR, exist_ok=True)

def get_wiki_cache_path(owner: str, repo: str, repo_type: str, language: str) -> str:
    """Generates the file path for a given wiki cache."""
    filename = f"deepwiki_cache_{repo_type}_{owner}_{repo}_{language}.json"
    return os.path.join(WIKI_CACHE_DIR, filename)

async def read_wiki_cache(owner: str, repo: str, repo_type: str, language: str) -> Optional[WikiCacheData]:
    """Reads wiki cache data from the file system."""
    cache_path = get_wiki_cache_path(owner, repo, repo_type, language)
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return WikiCacheData(**data)
        except Exception as e:
            logger.error(f"Error reading wiki cache from {cache_path}: {e}")
            return None
    return None

async def save_wiki_cache(data: WikiCacheRequest) -> bool:
    """Saves wiki cache data to the file system."""
    cache_path = get_wiki_cache_path(data.repo.owner, data.repo.repo, data.repo.type, data.language)
    logger.info(f"Attempting to save wiki cache. Path: {cache_path}")
    try:
        payload = WikiCacheData(
            wiki_structure=data.wiki_structure,
            generated_pages=data.generated_pages,
            repo=data.repo,
            provider=data.provider,
            model=data.model
        )
        # Log size of data to be cached for debugging (avoid logging full content if large)
        try:
            payload_json = payload.model_dump_json()
            payload_size = len(payload_json.encode('utf-8'))
            logger.info(f"Payload prepared for caching. Size: {payload_size} bytes.")
        except Exception as ser_e:
            logger.warning(f"Could not serialize payload for size logging: {ser_e}")


        logger.info(f"Writing cache file to: {cache_path}")
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(payload.model_dump(), f, indent=2)
        logger.info(f"Wiki cache successfully saved to {cache_path}")
        return True
    except IOError as e:
        logger.error(f"IOError saving wiki cache to {cache_path}: {e.strerror} (errno: {e.errno})", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"Unexpected error saving wiki cache to {cache_path}: {e}", exc_info=True)
        return False

# --- Wiki Cache API Endpoints ---

@app.get("/api/wiki_cache", response_model=Optional[WikiCacheData])
async def get_cached_wiki(
    owner: str = Query(..., description="Repository owner"),
    repo: str = Query(..., description="Repository name"),
    repo_type: str = Query(..., description="Repository type (e.g., github, gitlab)"),
    language: str = Query(..., description="Language of the wiki content")
):
    """
    Retrieves cached wiki data (structure and generated pages) for a repository.
    """
    # Language validation
    supported_langs = configs["lang_config"]["supported_languages"]
    if not supported_langs.__contains__(language):
        language = configs["lang_config"]["default"]

    logger.info(f"Attempting to retrieve wiki cache for {owner}/{repo} ({repo_type}), lang: {language}")
    cached_data = await read_wiki_cache(owner, repo, repo_type, language)
    if cached_data:
        return cached_data
    else:
        # Return 200 with null body if not found, as frontend expects this behavior
        # Or, raise HTTPException(status_code=404, detail="Wiki cache not found") if preferred
        logger.info(f"Wiki cache not found for {owner}/{repo} ({repo_type}), lang: {language}")
        return None

@app.post("/api/wiki_cache")
async def store_wiki_cache(request_data: WikiCacheRequest):
    """
    Stores generated wiki data (structure and pages) to the server-side cache.
    """
    # Language validation
    supported_langs = configs["lang_config"]["supported_languages"]

    if not supported_langs.__contains__(request_data.language):
        request_data.language = configs["lang_config"]["default"]

    logger.info(f"Attempting to save wiki cache for {request_data.repo.owner}/{request_data.repo.repo} ({request_data.repo.type}), lang: {request_data.language}")
    success = await save_wiki_cache(request_data)
    if success:
        return {"message": "Wiki cache saved successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to save wiki cache")

@app.delete("/api/wiki_cache")
async def delete_wiki_cache(
    owner: str = Query(..., description="Repository owner"),
    repo: str = Query(..., description="Repository name"),
    repo_type: str = Query(..., description="Repository type (e.g., github, gitlab)"),
    language: str = Query(..., description="Language of the wiki content"),
    authorization_code: Optional[str] = Query(None, description="Authorization code")
):
    """
    Deletes a specific wiki cache from the file system.
    """
    # Language validation
    supported_langs = configs["lang_config"]["supported_languages"]
    if not supported_langs.__contains__(language):
        raise HTTPException(status_code=400, detail="Language is not supported")

    if WIKI_AUTH_MODE:
        logger.info("check the authorization code")
        if not authorization_code or WIKI_AUTH_CODE != authorization_code:
            raise HTTPException(status_code=401, detail="Authorization code is invalid")

    logger.info(f"Attempting to delete wiki cache for {owner}/{repo} ({repo_type}), lang: {language}")
    cache_path = get_wiki_cache_path(owner, repo, repo_type, language)

    if os.path.exists(cache_path):
        try:
            os.remove(cache_path)
            logger.info(f"Successfully deleted wiki cache: {cache_path}")
            return {"message": f"Wiki cache for {owner}/{repo} ({language}) deleted successfully"}
        except Exception as e:
            logger.error(f"Error deleting wiki cache {cache_path}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to delete wiki cache: {str(e)}")
    else:
        logger.warning(f"Wiki cache not found, cannot delete: {cache_path}")
        raise HTTPException(status_code=404, detail="Wiki cache not found")

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker and monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "deepwiki-api"
    }

@app.get("/")
async def root():
    """Root endpoint to check if the API is running and list available endpoints dynamically."""
    # Collect routes dynamically from the FastAPI app
    endpoints = {}
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            # Skip docs and static routes
            if route.path in ["/openapi.json", "/docs", "/redoc", "/favicon.ico"]:
                continue
            # Group endpoints by first path segment
            path_parts = route.path.strip("/").split("/")
            group = path_parts[0].capitalize() if path_parts[0] else "Root"
            method_list = list(route.methods - {"HEAD", "OPTIONS"})
            for method in method_list:
                endpoints.setdefault(group, []).append(f"{method} {route.path}")

    # Optionally, sort endpoints for readability
    for group in endpoints:
        endpoints[group].sort()

    return {
        "message": "Welcome to Streaming API",
        "version": "1.0.0",
        "endpoints": endpoints
    }

# --- Processed Projects Endpoint --- (New Endpoint)
@app.get("/api/processed_projects", response_model=List[ProcessedProjectEntry])
async def get_processed_projects():
    """
    Lists all processed projects found in the wiki cache directory.
    Projects are identified by files named like: deepwiki_cache_{repo_type}_{owner}_{repo}_{language}.json
    """
    project_entries: List[ProcessedProjectEntry] = []
    # WIKI_CACHE_DIR is already defined globally in the file

    try:
        if not os.path.exists(WIKI_CACHE_DIR):
            logger.info(f"Cache directory {WIKI_CACHE_DIR} not found. Returning empty list.")
            return []

        logger.info(f"Scanning for project cache files in: {WIKI_CACHE_DIR}")
        filenames = await asyncio.to_thread(os.listdir, WIKI_CACHE_DIR) # Use asyncio.to_thread for os.listdir

        for filename in filenames:
            if filename.startswith("deepwiki_cache_") and filename.endswith(".json"):
                file_path = os.path.join(WIKI_CACHE_DIR, filename)
                try:
                    stats = await asyncio.to_thread(os.stat, file_path) # Use asyncio.to_thread for os.stat
                    parts = filename.replace("deepwiki_cache_", "").replace(".json", "").split('_')

                    # Expecting repo_type_owner_repo_language
                    # Example: deepwiki_cache_github_AsyncFuncAI_deepwiki-open_en.json
                    # parts = [github, AsyncFuncAI, deepwiki-open, en]
                    if len(parts) >= 4:
                        repo_type = parts[0]
                        owner = parts[1]
                        language = parts[-1] # language is the last part
                        repo = "_".join(parts[2:-1]) # repo can contain underscores

                        project_entries.append(
                            ProcessedProjectEntry(
                                id=filename,
                                owner=owner,
                                repo=repo,
                                name=f"{owner}/{repo}",
                                repo_type=repo_type,
                                submittedAt=int(stats.st_mtime * 1000), # Convert to milliseconds
                                language=language
                            )
                        )
                    else:
                        logger.warning(f"Could not parse project details from filename: {filename}")
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")
                    continue # Skip this file on error

        # Sort by most recent first
        project_entries.sort(key=lambda p: p.submittedAt, reverse=True)
        logger.info(f"Found {len(project_entries)} processed project entries.")
        return project_entries

    except Exception as e:
        logger.error(f"Error listing processed projects from {WIKI_CACHE_DIR}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list processed projects from server cache.")
