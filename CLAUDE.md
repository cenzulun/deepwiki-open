# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Claude 

## 
****:  & 
****:  (zh-CN)
****: WebDevOps

## 
### 
-  
-  (Docstring)
-  
-  

### 
-  
-  
-  API
-  

### 
-  ``
-  
-  /

## 
### 
```python
# 
def connect_database(connection_string):
    """
    
    
    :
        connection_string (str): 
    :
        Connection: 
    :
        DatabaseError: 
    """
    try:
        # 
        conn = create_connection(connection_string)
        return conn
    except Exception as e:
        # 
        logging.error(f": {str(e)}")
        raise DatabaseError(f": {str(e)}")

## Development Commands

### Frontend Development
- `npm run dev` - Start Next.js development server with Turbopack on port 3000
- `npm run build` - Build the Next.js application for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint to check code quality

### Backend Development
- `python -m pip install poetry==1.8.2 && poetry install -C api` - Install Python dependencies using Poetry
- `python -m api.main` - Start the FastAPI server (runs on port 8001 by default)

### Testing
- `python -m tests.run_tests` - Run all tests
- Individual test files are in `tests/unit/` and `tests/integration/`

### Docker Setup
- `docker-compose up` - Run both frontend and backend with Docker
- `docker build -t deepwiki-open .` - Build Docker image locally

## Architecture Overview

DeepWiki is a full-stack application that automatically generates interactive documentation for code repositories. The architecture consists of:

### Backend (FastAPI/Python)
- **API Server** (`api/api.py`): Main FastAPI application with endpoints for chat, wiki generation, and caching
- **Configuration System** (`api/config.py`): Manages multiple AI model providers (Google, OpenAI, OpenRouter, Azure, Ollama) and embedding models
- **Data Pipeline** (`api/data_pipeline.py`): Handles repository cloning, file processing, and code analysis
- **RAG System** (`api/rag.py`): Implements Retrieval Augmented Generation for the Ask feature
- **Chat System** (`api/simple_chat.py`, `api/websocket_wiki.py`): Handles streaming responses and WebSocket connections
- **Model Clients**: Individual clients for different AI providers (OpenAI, Google, OpenRouter, etc.)

### Frontend (Next.js/React/TypeScript)
- **App Router Structure**: Uses Next.js 13+ app directory structure
- **Main Page** (`src/app/page.tsx`): Repository input interface with configuration modal
- **Wiki Display** (`src/app/[owner]/[repo]/page.tsx`): Dynamic route for displaying generated wikis
- **Components**:
  - `Mermaid.tsx`: Diagram rendering component
  - `ConfigurationModal.tsx`: Model and settings configuration
  - `ProcessedProjects.tsx`: Display of previously processed repositories
- **Internationalization**: Multi-language support via `src/contexts/LanguageContext.tsx`
- **Theme Support**: Dark/light mode using next-themes

### Key Features
- **Multi-Provider Support**: Supports Google Gemini, OpenAI, OpenRouter, Azure OpenAI, and local Ollama models
- **Repository Sources**: GitHub, GitLab, BitBucket, and local repositories
- **Wiki Caching**: Server-side caching in `~/.adalflow/wikicache/`
- **Embedding Flexibility**: OpenAI, Google AI, or local Ollama embeddings
- **Export Functionality**: Markdown and JSON export options
- **Authentication**: Optional authorization mode via `DEEPWIKI_AUTH_MODE`

## Configuration System

The application uses a sophisticated configuration system:

### Environment Variables
- **Required**: `GOOGLE_API_KEY`, `OPENAI_API_KEY` (at least one)
- **Optional**: `OPENROUTER_API_KEY`, `AZURE_OPENAI_API_KEY`, `OLLAMA_HOST`, `DEEPWIKI_EMBEDDER_TYPE`
- **Authorization**: `DEEPWIKI_AUTH_MODE`, `DEEPWIKI_AUTH_CODE`

### Configuration Files (`api/config/`)
- **`generator.json`**: Model provider configurations and parameters
- **`embedder.json`**: Embedding model settings (OpenAI, Google, Ollama)
- **`repo.json`**: Repository processing rules and file filters
- **`lang.json`**: Supported languages for internationalization

## Data Flow

1. **Repository Input**: User enters repo URL/local path in frontend
2. **Configuration**: Model provider, embedding type, and processing options selected
3. **Repository Analysis**: Backend clones and processes the repository
4. **Embedding Creation**: Code chunks are embedded using selected provider
5. **Wiki Generation**: AI generates documentation with Mermaid diagrams
6. **Caching**: Results cached for future use
7. **Display**: Interactive wiki shown in frontend

## File Processing

The application intelligently processes code files:
- **Default Exclusions**: `node_modules`, `.git`, `__pycache__`, build artifacts
- **Supported Languages**: JavaScript, TypeScript, Python, Java, Go, Rust, etc.
- **Content Analysis**: Extracts functions, classes, and relationships for documentation

## Development Notes

- **Development Mode**: Backend automatically reloads on file changes (excluding logs and cache)
- **Logging**: Configurable logging via `LOG_LEVEL` and `LOG_FILE_PATH` environment variables
- **Port Configuration**: Backend defaults to 8001, configurable via `PORT` environment variable
- **CORS**: Backend configured to allow all origins for development

## Testing and Quality

- **Unit Tests**: Located in `tests/unit/` for individual components
- **Integration Tests**: Located in `tests/integration/` for end-to-end workflows
- **TypeScript**: Full type safety in frontend with strict type checking
- **ESLint**: Code quality enforcement for frontend JavaScript/TypeScript