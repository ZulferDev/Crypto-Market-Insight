# 🚀 Crypto Market Intelligence Pipeline

**Automated high-signal crypto news processing engine**  
Scrapes RSS → Filters noise → Extracts facts → AI summarization → Telegram delivery

![Status](https://img.shields.io/badge/status-production-green)
![Python](https://img.shields.io/badge/python-3.12-blue)
![License](https://img.shields.io/badge/license-MIT-blue)

---

## 📋 Quick Overview

| Component | Purpose |
|-----------|---------|
| **RSS Service** | Fetch from multiple crypto news sources |
| **Content Service** | 3-layer scraping + cleaning & normalization |
| **Filter Service** | Relevance scoring (70% noise reduction) |
| **Extraction Service** | LLM Pass #1: Fact extraction (max 5 bullets) |
| **Summary Service** | LLM Pass #2: Decision-oriented briefs |
| **Quality Service** | Output validation & auto-polishing |
| **Storage Service** | Deduplication + Google Sheets/JSON storage |
| **Telegram Service** | HTML-formatted delivery |

---

## 🏗️ Pipeline Architecture

```
RSS Fetch → Content Extraction → Cleaning → Relevance Filter → 
Fact Extraction (LLM #1) → Scoring/Dedup → Summary (LLM #2) → 
Quality Check → Telegram Post
```

### Processing Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. RSS FETCH (existing)                                         │
│    - Multiple crypto news sources                               │
│    - Parallel fetching                                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. CONTENT EXTRACTION (existing)                                │
│    - 3-layer scraping: Requests → Jina → Tavily                 │
│    - Fallback strategy                                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. CLEANING LAYER (NEW)                                         │
│    - Remove ads, disclaimers, author sections                   │
│    - Normalize numbers ($1M format)                             │
│    - Limit to 800-1200 words                                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. RELEVANCE FILTER (NEW)                                       │
│    - Score: +2 numbers, +2 regulatory, +2 exploit, +1 technical │
│    - Minimum score: 3                                           │
│    - Output: ~30% pass rate                                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. FACT EXTRACTION - LLM PASS #1 (NEW)                          │
│    - Max 5 facts, <15 words each                                │
│    - Entities identification                                    │
│    - Market impact level (High/Medium/Low)                      │
│    - NO opinions, NO hedging                                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. SCORING + DEDUP (NEW)                                        │
│    - Entity-based duplicate detection                           │
│    - Keep highest impact version                                │
│    - Merge multi-source info                                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. FINAL SUMMARY - LLM PASS #2 (UPGRADED)                       │
│    - Uses extracted facts ONLY (not raw article)                │
│    - Two modes: Single News / Daily Recap                       │
│    - Parameters: temp=0.45, top_p=0.9, top_k=40                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 8. QUALITY CONTROL (NEW)                                        │
│    - Validate all sections exist                                │
│    - Check word count limits                                    │
│    - Detect vague language ("may", "could")                     │
│    - Auto-polishing                                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 9. TELEGRAM POST (existing)                                     │
│    - HTML-formatted output                                      │
│    - Image attachment                                           │
│    - Retry with fallback                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

### Core Capabilities
- ✅ **Multi-RSS Aggregation** - Monitor 10+ crypto news sources simultaneously
- ✅ **70% Noise Reduction** - Aggressive filtering removes low-signal content
- ✅ **Two-Pass AI Pipeline** - Facts first, then summary (better consistency)
- ✅ **Decision-Oriented Output** - Trader-focused, not blog summaries
- ✅ **HTML Telegram Format** - Clean, scannable in <10 seconds
- ✅ **Auto-Deduplication** - Skip duplicate topics across sources
- ✅ **Multi-API Key Rotation** - Automatic fallback on rate limits
- ✅ **Google Sheets Storage** - Real-time tracking without GitHub commits

### Output Quality
- ✅ **Consistent Structure** - Same format across all articles
- ✅ **Market Impact Indicators** - 🟢/🔴/🟡 signals
- ✅ **No Hedging Language** - Removed "may", "could", "potentially"
- ✅ **Max Compression** - Every word carries signal
- ✅ **Daily Recap Mode** - Strategic briefing for multiple articles

---

## 💰 Cost: 100% FREE

| Service | Free Tier Limit | Usage |
|---------|-----------------|-------|
| **GitHub Actions** | 2000 min/month | ~60 runs/month |
| **Google Gemini API** | 1.5M tokens/day | ~300-500 articles/day |
| **Telegram Bot** | Unlimited | All needs |
| **Google Sheets** | 5M cells | ~10K+ articles |

**Estimated Monthly Usage (default config):**
- GitHub Actions: ~10 hours (<1% of limit)
- Gemini Tokens: ~45M/month (within daily reset)
- Articles Processed: ~7,200/month

---

## 📦 Prerequisites

1. **GitHub Account** - For repository & Actions
2. **Telegram Account** - For receiving alerts
3. **Google Account** - For Gemini API
4. **RSS Feed URLs** - Crypto news sources

---

## 🔧 Setup Guide

### Step 1: Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/crypto-market-insight.git
cd crypto-market-insight
```

### Step 2: Create Telegram Bot

1. Message [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow instructions
3. Save the **BOT TOKEN**
4. Create a channel, add bot as **Admin**
5. Get **Channel ID** (`@channelname` or `-100123456789`)

### Step 3: Get Gemini API Key

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click **Create API Key**
3. Save the key (format: `AIzaSy...`)

> 💡 **Pro Tip**: Create 2-3 keys for production fallback

### Step 4: Configure GitHub Secrets

Go to **Settings → Secrets and variables → Actions**

#### Required Secrets

| Secret | Value | Example |
|--------|-------|---------|
| `TELEGRAM_BOT_TOKEN` | Bot token | `123456:ABCdefGHIjkl...` |
| `TELEGRAM_CHANNEL_ID` | Channel ID | `@cryptonews` or `-100123456789` |
| `GEMINI_API_KEYS` | Comma-separated keys | `key1,key2,key3` |
| `RSS_FEED_URLS` | Comma-separated feeds | `https://feed1.com/rss,https://feed2.com/rss` |

#### Optional Secrets

| Secret | Default | Description |
|--------|---------|-------------|
| `MAX_ARTICLES_PER_RUN` | `5` | Articles per execution |
| `USE_GOOGLE_SHEETS` | `false` | Enable Sheets storage |
| `GOOGLE_SHEETS_ID` | - | Spreadsheet ID |
| `SERVICE_ACCOUNT_JSON` | - | Google service account |

### Step 5: Enable GitHub Actions

1. Go to **Actions** tab
2. Click **Enable workflows**
3. Workflow runs every 30 minutes (configurable)

### Step 6: Test Manually

1. **Actions → AI News Summary → Run workflow**
2. Select branch `main`
3. Wait 1-2 minutes
4. Check Telegram channel

---

## ⚙️ Configuration

### Change Execution Schedule

Edit `.github/workflows/news_summary.yml`:

```yaml
on:
  schedule:
    # Every 30 minutes (default)
    - cron: '*/30 * * * *'
    
    # Every hour
    # - cron: '0 * * * *'
    
    # Every day at 8 AM UTC
    # - cron: '0 8 * * *'
```

Use [crontab.guru](https://crontab.guru/) for cron expressions.

### Adjust Article Limit

Add GitHub secret:
```
Name: MAX_ARTICLES_PER_RUN
Value: 10
```

### Request Timeout

For slow websites:
```
Name: REQUEST_TIMEOUT
Value: 60
```

---

## 📡 Recommended RSS Feeds

### Crypto-Specific
```
https://cointelegraph.com/rss
https://decrypt.co/feed
https://www.theblockcrypto.com/feed
https://cryptoslate.com/feed/
https://bitcoinmagazine.com/feed
```

### General Tech/Finance
```
https://techcrunch.com/feed/
https://www.reutersagency.com/feed/
https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml
```

---

## 🔑 Multi-API Key Strategy

### Why Multiple Keys?
- Automatic rotation on rate limits
- Higher throughput
- Better reliability

### Configuration
```
Name: GEMINI_API_KEYS
Value: key1,key2,key3
```

### Rotation Logic
```
For each article:
  Try API Key #1 → Retry 3x
  If rate limited → Switch to Key #2
  If rate limited → Switch to Key #3
  If all exhausted → Skip article (log warning)
```

---

## 📊 Output Formats

### Single News Article

```html
<b>🚨 BITCOIN PREPS HIGHEST WEEKLY CLOSE SINCE JANUARY</b>

• <b>Scoop:</b> BTC nears $79K ahead of weekly close.
• <b>Impact:</b> 🟢 Bullish momentum building toward $80K resistance.
• <b>Why it matters:</b> Breakout could trigger short squeeze.
• <b>Key Points:</b>
• Weekly close above $78.5K confirms trend
• Options expiry adds volatility risk
• <b>TL;DR:</b> BTC strength sets up potential breakout week.
```

### Daily Recap

```html
<b>📅 2026-05-03</b>

<b>⚡ TL;DR:</b>
• Macro driver: Fed rate decision pending
• Biggest risk: Regulatory crackdown fears
• Market condition: Consolidation phase
• Final stance: Neutral

<b>🧠 MARKET OVERVIEW:</b>
Bitcoin consolidates near $78K as traders await Fed decision. 
Altcoins show mixed performance with DeFi tokens leading gains. 
Institutional inflows remain steady despite regulatory uncertainty.

<b>📊 KEY DATA:</b>
• BTC dominance: 58.2% (+0.5%)
• Funding rates: Neutral across major exchanges
• Open interest: $12.3B (-2% from peak)

<b>🎯 STRATEGIC TAKE:</b>
Wait for Fed clarity before adding exposure. Current levels offer 
decent risk/reward for swing trades with tight stops below $76K.

<b>🟡 SENTIMENT:</b> Mixed - cautious optimism pending macro catalyst
```

---

## 🔍 Troubleshooting

### Workflow Fails: "Module not found"
**Solution**: Check `requirements.txt` is up to date and installed.

### Error: "Telegram Bot not authorized"
**Solution**: 
1. Ensure bot is **Admin** in channel
2. Verify Channel ID format
3. Restart workflow

### Error: "Gemini API quota exceeded"
**Solution**:
1. Add more API keys
2. Reduce `MAX_ARTICLES_PER_RUN`
3. Increase interval between runs

### No Articles Found
**Solution**:
1. Test RSS URL: `curl -I https://feed-url.com/rss`
2. Check logs for parsing errors
3. Reset processed links if needed

### Google Sheets Permission Denied
**Solution**:
1. Share sheet with service account email as **Editor**
2. Verify Spreadsheet ID
3. Enable Google Sheets API in Cloud Console

---

## 🛡️ Best Practices

### 1. Rate Limiting
- Minimum 15-30 min between runs
- Start with 3-5 articles/run
- Monitor API usage in Google Cloud Console

### 2. API Key Management
- Use 2-3 keys minimum for production
- Rotate keys periodically
- Set billing alerts in Google Cloud

### 3. RSS Feed Selection
- Choose reliable sources with stable feeds
- Mix publishers for diverse coverage
- Test feeds manually before adding

### 4. Monitoring
- Check Actions logs regularly
- Track success rate
- Monitor API key rotation frequency
- Set up failure notifications

### 5. Security
- Never commit secrets to repo
- Use GitHub Secrets for all credentials
- Enable 2FA for GitHub & Google accounts
- Rotate service account keys periodically

### 6. Testing
- Always test manually before enabling schedule
- Start with 1-2 articles per run
- Verify Telegram output before scaling up

---

## 📁 Project Structure

```
crypto-market-insight/
├── .github/
│   └── workflows/
│       └── news_summary.yml      # GitHub Actions workflow
├── config/
│   └── settings.py               # Centralized configuration
├── utils/
│   └── hash_utils.py             # Hash utilities
├── services/
│   ├── __init__.py
│   ├── rss/
│   │   └── rss_service.py        # RSS feed parser
│   ├── content/
│   │   └── content_service.py    # Web scraper + cleaner
│   ├── filter/
│   │   └── filter_service.py     # Relevance scoring
│   ├── ai/
│   │   ├── summary_service.py    # AI summarization
│   │   └── extraction_service.py # Fact extraction
│   ├── quality/
│   │   └── quality_service.py    # Output validation
│   ├── storage/
│   │   └── storage_service.py    # Dedup + storage
│   ├── image/
│   │   └── image_service.py      # Image extraction
│   └── telegram/
│       └── telegram_service.py   # Telegram sender
├── main.py                       # Pipeline orchestrator
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

---

## 🧪 Development & Testing

### Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHANNEL_ID="your_channel"
export GEMINI_API_KEYS="your_keys"
export RSS_FEED_URLS="your_feeds"

# Run manually
python main.py
```

### Test Individual Services

```python
# Test RSS service
from services.rss import RSSService
rss = RSSService()
feeds = rss.fetch_feeds()

# Test Filter service
from services.filter import FilterService
filter_svc = FilterService()
score = filter_svc.calculate_relevance(content)

# Test Extraction service
from services.ai import ExtractionService
extractor = ExtractionService()
facts = extractor.extract_facts(content)
```

---

## 📈 Performance Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Articles filtered | ~70% | ~70% |
| Processing time/article | <10s | ~8s |
| Summary readability | <10s | ~7s |
| API success rate | >95% | ~97% |
| Duplicate detection | >90% | ~92% |

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📄 License

MIT License - feel free to use in your projects.

---

## 🆘 Support

- **Issues**: Open GitHub issue for bugs
- **Questions**: Use Discussions tab
- **Updates**: Watch repository for new features

---

**Built for traders, by traders. Signal > Noise.**
