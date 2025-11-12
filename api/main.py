import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from api.logging_config import setup_logging

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

# Configure watchfiles logger to show file paths
watchfiles_logger = logging.getLogger("watchfiles.main")
watchfiles_logger.setLevel(logging.DEBUG)  # Enable DEBUG to see file paths

# Add the current directory to the path so we can import the api package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Apply watchfiles monkey patch BEFORE uvicorn import
is_development = os.environ.get("NODE_ENV") != "production"
if is_development:
    import watchfiles
    current_dir = os.path.dirname(os.path.abspath(__file__))
    logs_dir = os.path.join(current_dir, "logs")
    
    original_watch = watchfiles.watch
    def patched_watch(*args, **kwargs):
        # Only watch the api directory but exclude logs subdirectory
        # Instead of watching the entire api directory, watch specific subdirectories
        api_subdirs = []
        for item in os.listdir(current_dir):
            item_path = os.path.join(current_dir, item)
            if os.path.isdir(item_path) and item != "logs":
                api_subdirs.append(item_path)
        
        # Also add Python files in the api root directory
        api_subdirs.append(current_dir + "/*.py")
        
        return original_watch(*api_subdirs, **kwargs)
    watchfiles.watch = patched_watch

import uvicorn

# Check for API keys - support mock mode when SKIP_EMBEDDING is enabled
skip_embedding = os.environ.get('SKIP_EMBEDDING', '').lower() in ['true', '1', 't']
embedder_type = os.environ.get('DEEPWIKI_EMBEDDER_TYPE', '').lower()

if skip_embedding and embedder_type == 'mock':
    logger.info("运行在模拟嵌入模式，跳过API密钥检查")
else:
    # Check for at least one working API key
    api_keys = {
        'GOOGLE_API_KEY': os.environ.get('GOOGLE_API_KEY'),
        'OPENAI_API_KEY': os.environ.get('OPENAI_API_KEY'),
        'ZHIPUAI_API_KEY': os.environ.get('ZHIPUAI_API_KEY'),
        'DEEPSEEK_API_KEY': os.environ.get('DEEPSEEK_API_KEY')
    }

    available_keys = [key for key, value in api_keys.items() if value and value.strip() and value != 'dummy-key-for-bypass-embed-check']

    if not available_keys:
        logger.warning("未找到有效的API密钥")
        logger.warning("请配置至少一个API密钥: GOOGLE_API_KEY, OPENAI_API_KEY, ZHIPUAI_API_KEY, DEEPSEEK_API_KEY")
        logger.warning("或者在.env文件中设置 SKIP_EMBEDDING=true 和 DEEPWIKI_EMBEDDER_TYPE=mock")
    else:
        logger.info(f"找到可用的API密钥: {', '.join(available_keys)}")

# Configure Google Generative AI
import google.generativeai as genai
from api.config import GOOGLE_API_KEY

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
else:
    logger.warning("GOOGLE_API_KEY not configured")

if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", 8001))

    # Import the app here to ensure environment variables are set first
    from api.api import app

    logger.info(f"Starting Streaming API on port {port}")

    # Run the FastAPI app with uvicorn
    uvicorn.run(
        "api.api:app",
        host="0.0.0.0",
        port=port,
        reload=is_development,
        reload_excludes=["**/logs/*", "**/__pycache__/*", "**/*.pyc"] if is_development else None,
    )
