# News Summary Service - Microservices Architecture

## 📋 Overview

This project has been refactored from a monolithic script into a clean, maintainable microservices architecture. Each service is responsible for a single concern, making the codebase easier to test, maintain, and extend.

## 🏗️ Architecture

```
/workspace
├── main.py                      # Main entry point & workflow orchestrator
├── config/
│   └── settings.py              # Centralized configuration management
├── utils/
│   ├── __init__.py
│   └── hash_utils.py            # Utility functions (hash generation)
├── services/
│   ├── __init__.py
│   ├── rss/                     # RSS Feed Service
│   │   ├── __init__.py
│   │   └── rss_service.py       # Fetch and parse RSS feeds
│   ├── storage/                 # Storage Service
│   │   ├── __init__.py
│   │   └── storage_service.py   # Google Sheets + JSON storage
│   ├── content/                 # Content Extraction Service
│   │   ├── __init__.py
│   │   └── content_service.py   # 3-layer web scraping
│   ├── ai/                      # AI Summary Service
│   │   ├── __init__.py
│   │   └── summary_service.py   # Gemini AI summarization
│   ├── image/                   # Image Extraction Service
│   │   ├── __init__.py
│   │   └── image_service.py     # Image extraction from articles
│   └── telegram/                # Telegram Service
│       ├── __init__.py
│       └── telegram_service.py  # Send messages to Telegram
└── news_summary.py              # Original monolithic file (deprecated)
```

## 🔧 Services

### 1. **RSS Feed Service** (`services/rss/`)
- Fetches and parses RSS feeds
- Extracts article metadata (title, link, author, published date)
- Extracts images from RSS media tags

### 2. **Storage Service** (`services/storage/`)
- Manages persistence of processed articles
- Supports Google Sheets integration
- Automatic fallback to local JSON storage
- Provides data models (`ProcessedArticle`)

### 3. **Content Extraction Service** (`services/content/`)
- 3-layer scraping system:
  1. **Layer 1**: Requests + BeautifulSoup (fast, free)
  2. **Layer 2**: Jina AI Reader (for JS-heavy sites)
  3. **Layer 3**: Tavily Extract (for difficult sites)

### 4. **AI Summary Service** (`services/ai/`)
- Generates article summaries using Google Gemini AI
- Multiple model fallback strategy
- Configurable temperature and response schema
- Automatic truncation for Telegram limits

### 5. **Image Extraction Service** (`services/image/`)
- Priority-based image extraction:
  1. RSS Media tags
  2. OpenGraph images
  3. Twitter Card images
  4. First relevant article image
  5. Clearbit Logo API (fallback)

### 6. **Telegram Service** (`services/telegram/`)
- Sends messages to Telegram channels
- Supports text-only and photo with caption
- HTML parse mode support

## 🚀 Usage

### Running the Workflow

```bash
# Set environment variables
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHANNEL_ID="your_channel_id"
export GEMINI_API_KEY="your_gemini_api_key"
export RSS_FEED_URL="https://example.com/feed.xml"

# Run the main workflow
python main.py
```

### Using Individual Services

```python
from services.rss import RSSFeedService
from services.ai import AISummaryService
from services.telegram import TelegramService

# Initialize services
rss_service = RSSFeedService()
ai_service = AISummaryService()
telegram_service = TelegramService()

# Fetch RSS feed
articles = rss_service.fetch_feed("https://example.com/feed.xml")

# Generate summary
summary = ai_service.generate_summary(
    title=articles[0].title,
    content="article content here...",
    author=articles[0].author,
    source_url=articles[0].link
)

# Send to Telegram
telegram_service.send_message(summary, image_url="https://example.com/image.jpg")
```

## ⚙️ Configuration

All configuration is centralized in `config/settings.py` and managed via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | Required |
| `TELEGRAM_CHANNEL_ID` | Telegram channel ID | Required |
| `GEMINI_API_KEY` | Google Gemini API key | Required |
| `RSS_FEED_URL` | RSS feed URL | Required |
| `USE_GOOGLE_SHEETS` | Enable Google Sheets storage | `false` |
| `GOOGLE_SHEETS_ID` | Google Sheets spreadsheet ID | `""` |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | Path to service account JSON | `service_account.json` |
| `MAX_ARTICLES_PER_RUN` | Max articles to process per run | `5` |
| `SUMMARY_MAX_LENGTH` | Maximum summary length | `1500` |
| `TAVILY_API_KEY` | Tavily API key (optional) | `None` |

## 🎯 Benefits of Refactoring

1. **Single Responsibility**: Each service has one clear purpose
2. **Testability**: Services can be tested independently
3. **Maintainability**: Changes are isolated to specific services
4. **Reusability**: Services can be used in other projects
5. **Readability**: Clean, well-documented code with type hints
6. **Extensibility**: Easy to add new features or modify existing ones
7. **Error Handling**: Better error isolation and handling

## 📝 Migration Notes

The original `news_summary.py` file is kept for reference but is now deprecated. All new development should use the new microservices architecture in `main.py`.

### Key Changes:
- Configuration extracted to `config/settings.py`
- Functions converted to service classes with clear interfaces
- Data models using Python dataclasses
- Type hints throughout the codebase
- Better error handling and logging
- Consistent naming conventions

## 🧪 Testing

Each service can be tested independently:

```python
# Example: Testing RSS Service
from services.rss import RSSFeedService

def test_rss_fetch():
    service = RSSFeedService()
    articles = service.fetch_feed("https://example.com/feed.xml")
    assert len(articles) > 0
    assert articles[0].title is not None
```

## 📄 License

Same as original project.
