# 📰 AI News Summary to Telegram

Workflow otomatis untuk mengambil berita dari multiple RSS feeds, membuat ringkasan AI dengan **Google Gemini** (multi-API key), dan mengirim ke **Telegram Channel**. Dibangun dengan arsitektur microservices untuk kemudahan maintenance.

![GitHub Issues](https://img.shields.io/github/issues/yourusername/news-summary-telegram)
![GitHub Stars](https://img.shields.io/github/stars/yourusername/news-summary-telegram)
![License](https://img.shields.io/github/license/yourusername/news-summary-telegram)

---

## 📑 Daftar Isi

- [Fitur Utama](#-fitur-utama)
- [Arsitektur Microservices](#-arsitektur-microservices)
- [Biaya Gratis](#-biaya-gratis-rp-0-)
- [Prasyarat](#-prasyarat)
- [Setup Lengkap](#-setup-lengkap)
- [Konfigurasi Lanjutan](#-konfigurasi-lanjutan)
- [Multi RSS Feed](#-multi-rss-feed)
- [Multi API Key](#-multi-api-key)
- [Google Sheets Storage](#-google-sheets-storage)
- [Troubleshooting](#-troubleshooting)
- [Best Practices](#-best-practices)
- [Struktur File](#-struktur-file)
- [Testing & Development](#-testing--development)
- [FAQ](#-faq)

---

## ✨ Fitur Utama

### Core Features
- ✅ **Multi RSS Feed Support** - Monitor banyak sumber berita sekaligus
- ✅ **Multi API Key Rotation** - Auto-fallback saat limit API tercapai
- ✅ **Smart Content Extraction** - 3-layer scraping (Requests → Jina → Tavily)
- ✅ **Google Gemini AI** - Ringkasan cerdas dalam bahasa Indonesia
- ✅ **Telegram Integration** - Kirim otomatis dengan foto & caption
- ✅ **Deduplikasi Otomatis** - Skip artikel yang sudah diproses
- ✅ **Rate Limiting Smart** - Retry + rotation saat limit tercapai
- ✅ **Scheduled & Manual Trigger** - Cron job atau run manual

### Advanced Features
- ✅ **Google Sheets Integration** - Storage real-time tanpa commit GitHub
- ✅ **Fallback Strategy** - 8 model Gemini + multi API key
- ✅ **Image Extraction** - Priority-based (OG → Twitter → Article → Clearbit)
- ✅ **Error Recovery** - Automatic retry dengan exponential backoff
- ✅ **Comprehensive Logging** - Debug-friendly output

---

## 🏗️ Arsitektur Microservices

Proyek ini telah direfactor dari monolithic script menjadi clean microservices architecture:

```
/workspace
├── main.py                          # Main entry point & orchestrator
├── config/
│   └── settings.py                  # Centralized configuration
├── utils/
│   └── hash_utils.py                # Utility functions
└── services/
    ├── rss/                         # RSS Feed Service
    │   └── rss_service.py           # Fetch & parse RSS feeds
    ├── storage/                     # Storage Service  
    │   └── storage_service.py       # Google Sheets + JSON storage
    ├── content/                     # Content Extraction Service
    │   └── content_service.py       # 3-layer web scraping
    ├── ai/                          # AI Summary Service
    │   └── summary_service.py       # Gemini AI summarization
    ├── image/                       # Image Extraction Service
    │   └── image_service.py         # Image extraction
    └── telegram/                    # Telegram Service
        └── telegram_service.py      # Send to Telegram
```

### Keuntungan Arsitektur Ini

| Benefit | Description |
|---------|-------------|
| **Single Responsibility** | Setiap service punya 1 tanggung jawab jelas |
| **Testability** | Services bisa ditest secara independen |
| **Maintainability** | Perubahan terisolasi per service |
| **Reusability** | Services bisa dipakai di project lain |
| **Extensibility** | Mudah menambah fitur baru |

---

## 💰 Biaya: GRATIS (Rp 0,-)

Semua service yang digunakan memiliki free tier yang generous:

| Service | Limit Gratis | Cukup Untuk |
|---------|--------------|-------------|
| **GitHub Actions** | 2000 menit/bulan | ~60-100 run/hari |
| **Google Gemini API** | 1.5M tokens/hari | ~300-500 artikel/hari |
| **Crawl4AI** | Unlimited (self-hosted) | Semua kebutuhan |
| **Telegram Bot** | Unlimited | Semua kebutuhan |
| **Google Sheets** | 5M cells | ~10.000+ artikel |

### Estimasi Penggunaan (Default Config)

Dengan 5 artikel/run, setiap 30 menit:

| Resource |/Hari | /Bulan | Limit Gratis |
|----------|-------|--------|--------------|
| GitHub Actions | ~20 menit | ~10 jam | 2000 menit |
| Gemini Tokens | ~50K | ~1.5M | 1.5M/hari |
| Artikel | ~240 | ~7200 | Unlimited |

**✅ 100% GRATIS dan sustainable!**

---

## 📋 Prasyarat

Sebelum memulai, pastikan Anda memiliki:

1. **GitHub Account** - Untuk hosting repository dan GitHub Actions
2. **Telegram Account** - Untuk menerima notifikasi
3. **Google Account** - Untuk Gemini API dan opsional Google Sheets
4. **RSS Feed URLs** - Sumber berita yang ingin dimonitor

---

## 🔧 Setup Lengkap

### Langkah 1: Fork/Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/news-summary-telegram.git
cd news-summary-telegram
```

### Langkah 2: Buat Telegram Bot

1. Chat dengan [@BotFather](https://t.me/BotFather) di Telegram
2. Kirim perintah: `/newbot`
3. Ikuti instruksi untuk memberi nama bot
4. **Simpan BOT TOKEN** yang diberikan (format: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)
5. Buat channel Telegram (atau gunakan yang sudah ada)
6. Invite bot ke channel sebagai **Admin** (wajib!)
7. Dapatkan **Channel ID**:
   - Format 1: `@channelname` (public channel)
   - Format 2: `-1001234567890` (private channel)
   - Cara: Forward pesan dari channel ke [@userinfobot](https://t.me/userinfobot)

### Langkah 3: Dapatkan Gemini API Key

1. Buka [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Login dengan akun Google
3. Klik **Create API Key**
4. Pilih project atau buat baru
5. **Simpan API key** (format: `AIzaSy...`)

> 💡 **Tips**: Untuk production, siapkan 2-3 API key untuk fallback saat limit tercapai.

### Langkah 4: (Opsional) Setup Google Sheets

Untuk storage yang lebih baik tanpa perlu commit ke GitHub:

1. Buka [Google Sheets](https://sheets.google.com)
2. Buat spreadsheet baru, beri nama: `News Processed Links`
3. Buat header di baris 1:
   - A1: `Link`
   - B1: `Title`
   - C1: `Summary`
   - D1: `Processed At`
   - E1: `Author`
   - F1: `Image URL`
4. Buka [Google Cloud Console](https://console.cloud.google.com)
5. Buat project baru → Enable **Google Sheets API**
6. Buat **Service Account**:
   - APIs & Services → Credentials → Create Credentials → Service Account
   - Download JSON key
7. Share Google Sheet ke email service account (dengan permission **Editor**)
8. Copy **Spreadsheet ID** dari URL (antara `/d/` dan `/edit`)

### Langkah 5: Setup GitHub Secrets

1. Buka repository GitHub Anda
2. Pergi ke **Settings** → **Secrets and variables** → **Actions**
3. Klik **New repository secret**

#### Required Secrets

| Secret Name | Value | Contoh | Required |
|-------------|-------|--------|----------|
| `TELEGRAM_BOT_TOKEN` | Token dari BotFather | `1234567890:ABCdef...` | ✅ |
| `TELEGRAM_CHANNEL_ID` | Channel ID | `@mynews` atau `-100123...` | ✅ |
| `GEMINI_API_KEYS` | Multiple API keys (comma-separated) | `key1,key2,key3` | ✅ |
| `RSS_FEED_URLS` | Multiple RSS feeds (comma-separated) | `https://feed1.com/rss,https://feed2.com/rss` | ✅ |

#### Optional Secrets

| Secret Name | Value | Default | Description |
|-------------|-------|---------|-------------|
| `GEMINI_API_KEY` | Single API key | - | Legacy fallback |
| `RSS_FEED_URL` | Single RSS feed | - | Legacy fallback |
| `MAX_ARTICLES_PER_RUN` | Number | `5` | Max artikel per run |
| `USE_GOOGLE_SHEETS` | `true`/`false` | `false` | Enable Google Sheets |
| `GOOGLE_SHEETS_ID` | Spreadsheet ID | - | ID Google Sheets |
| `SERVICE_ACCOUNT_JSON` | JSON content | - | Service account credentials |

> 💡 **Catatan**: 
> - `GEMINI_API_KEYS` lebih diprioritaskan daripada `GEMINI_API_KEY`
> - `RSS_FEED_URLS` lebih diprioritaskan daripada `RSS_FEED_URL`

### Langkah 6: Aktifkan GitHub Actions

1. Pergi ke tab **Actions** di repository GitHub
2. Klik **I understand my workflows, go ahead and enable workflows**
3. Workflow akan berjalan otomatis sesuai jadwal (default: setiap 30 menit)

### Langkah 7: Test Manual

1. Pergi ke **Actions** → **AI News Summary to Telegram**
2. Klik **Run workflow**
3. Pilih branch `main`
4. Klik **Run workflow**
5. Tunggu proses selesai (~1-2 menit)
6. Cek channel Telegram untuk hasil

---

## ⚙️ Konfigurasi Lanjutan

### Ubah Jadwal Execution

Edit file `.github/workflows/news_summary.yml`:

```yaml
on:
  schedule:
    # Setiap 30 menit (default)
    - cron: '*/30 * * * *'
    
    # Setiap jam
    - cron: '0 * * * *'
    
    # Setiap 4 jam
    - cron: '0 */4 * * *'
    
    # Setiap hari jam 8 pagi WIB (UTC+7)
    - cron: '1 1 * * *'
```

> 💡 Gunakan [crontab.guru](https://crontab.guru/) untuk generate cron expression.

### Ubah Jumlah Artikel Per Run

Tambahkan secret di GitHub:

```
Name: MAX_ARTICLES_PER_RUN
Value: 10
```

### Custom AI Prompt

Edit file `services/ai/summary_service.py` pada bagian prompt template untuk mengubah format ringkasan.

### Timeout Configuration

Untuk website yang lambat, tambahkan environment variable:

```bash
REQUEST_TIMEOUT=60  # Default: 30 detik
```

---

## 📡 Multi RSS Feed

### Mengapa Multi RSS Feed?

- Aggregate berita dari berbagai sumber
- Coverage lebih comprehensive
- Single workflow untuk semua feeds
- Auto-deduplication across feeds

### Cara Konfigurasi

#### Option 1: Multiple Feeds (Recommended)

Di GitHub Secrets:

```
Name: RSS_FEED_URLS
Value: https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml,https://feeds.bbci.co.uk/news/rss.xml,https://techcrunch.com/feed/
```

#### Option 2: Single Feed (Legacy)

```
Name: RSS_FEED_URL
Value: https://example.com/rss
```

### Contoh RSS Feed Populer

```
# Tech News
https://techcrunch.com/feed/
https://arstechnica.com/feed/
https://www.theverge.com/rss/index.xml

# General News
https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml
https://feeds.bbci.co.uk/news/rss.xml
https://www.reutersagency.com/feed/

# Crypto
https://cointelegraph.com/rss
https://decrypt.co/feed
https://www.theblockcrypto.com/feed
```

### Cara Kerja

```
1. Fetch Feed 1 → 10 artikel
2. Fetch Feed 2 → 15 artikel
3. Fetch Feed 3 → 8 artikel
   ↓
4. Combine → 33 artikel
5. Deduplicate by link
6. Filter already processed
7. Process new articles (max: MAX_ARTICLES_PER_RUN)
```

---

## 🔑 Multi API Key

### Mengapa Multi API Key?

Google Gemini API memiliki rate limit. Dengan multiple API keys:
- **Automatic rotation** saat limit tercapai
- **Better reliability** dengan fallback
- **Higher throughput** distribute requests

### Cara Konfigurasi

#### Option 1: Multiple Keys (Recommended)

Di GitHub Secrets:

```
Name: GEMINI_API_KEYS
Value: key1,key2,key3,key4
```

#### Option 2: Single Key (Legacy)

```
Name: GEMINI_API_KEY
Value: your_single_key
```

### Smart Rotation Strategy

```
For each article:
  For each model (8 free-tier models):
    Try API Key #1 → Retry 3x
    ↓ (if rate limited)
    Try API Key #2 → Retry 3x
    ↓ (if rate limited)
    Try API Key #3 → Retry 3x
    ...
    ↓ (all keys exhausted)
    Switch to next model
```

### Detected Rate Limit Errors

- `429 Too Many Requests`
- `503 Service Unavailable`
- `UNAVAILABLE` - Model unavailable
- `RESOURCE_EXHAUSTED` - Quota exceeded
- "high demand" errors
- "quota" errors

### Contoh Output Log

```
🤖 Generating AI summary with Gemini (using 3 API key(s))...

🔄 Trying model 1/8: gemma-4-31b-it
❌ gemma-4-31b-it (API key #1) error (Attempt 1/3): 429 Too Many Requests
⏳ Retrying with same key in 1.0s...
❌ gemma-4-31b-it (API key #1) error (Attempt 2/3): 429 Too Many Requests
⏳ Retrying with same key in 1.0s...
❌ gemma-4-31b-it (API key #1) error (Attempt 3/3): 429 Too Many Requests
⏭️ Switching to next API key after 1.0s delay...
🔄 Rotated to API key #2/3
✅ Summary generated with gemma-4-31b-it (API key #2): 856 characters
```

---

## 📊 Google Sheets Storage

### Mengapa Google Sheets?

- ✅ Tidak perlu GitHub Token untuk push/commit
- ✅ Real-time updates
- ✅ Mudah dikelola via UI
- ✅ Backup otomatis oleh Google
- ✅Queryable - mudah filter/search

### Setup Steps

1. **Enable Secret**:
   ```
   Name: USE_GOOGLE_SHEETS
   Value: true
   ```

2. **Set Spreadsheet ID**:
   ```
   Name: GOOGLE_SHEETS_ID
   Value: 1aBC123xyz456_DEF789
   ```

3. **Upload Service Account**:
   ```
   Name: SERVICE_ACCOUNT_JSON
   Value: {paste isi file JSON}
   ```

4. **Update Workflow** (already configured):
   ```yaml
   - name: Setup Service Account
     run: echo "${{ secrets.SERVICE_ACCOUNT_JSON }}" > service_account.json
   ```

### Fallback

Jika Google Sheets gagal atau tidak di-enable, sistem otomatis fallback ke local JSON storage (`processed_links.json`).

---

## 🔍 Troubleshooting

### Workflow Gagal: "Playwright browser not found"

**Solusi**: Pastikan workflow menginstall Playwright:

```yaml
- name: Install dependencies
  run: |
    pip install crawl4ai playwright
    playwright install chromium --with-deps
```

### Error: "Telegram Bot not authorized"

**Penyebab**:
- Bot belum diinvite ke channel
- Bot bukan admin di channel
- Channel ID salah format

**Solusi**:
1. Invite bot ke channel sebagai **Admin**
2. Cek Channel ID (coba dengan `@username` atau `-100xxxxx`)
3. Restart workflow

### Error: "Gemini API quota exceeded"

**Penyebab**: Limit 1.5M tokens/hari tercapai

**Solusi**:
1. Tambahkan lebih banyak API keys
2. Kurangi `MAX_ARTICLES_PER_RUN`
3. Increase interval between runs
4. Tunggu reset besok (limit reset harian)

### Error: "All API keys exhausted"

**Penyebab**: Semua API key hit rate limit

**Solusi**:
- Tambahkan 2-3 API keys lagi
- Reduce `MAX_ARTICLES_PER_RUN`
- Increase cron interval

### Artikel Ter-duplikasi

**Penyebab**: Same article dengan different URLs

**Solusi**:
- Normal behavior untuk syndicated content
- Sistem deduplicate by exact URL match
- Manual cleanup jika diperlukan

### Crawl4AI Timeout/Lambat

**Penyebab**: Website dengan anti-bot protection

**Solusi**:
1. Increase timeout:
   ```
   Name: REQUEST_TIMEOUT
   Value: 60
   ```
2. Coba source RSS alternatif
3. Check logs untuk specific error

### Google Sheets Permission Denied

**Solusi**:
1. Pastikan email service account sudah di-share ke Sheet sebagai **Editor**
2. Cek Spreadsheet ID benar
3. Pastikan Google Sheets API enabled di Google Cloud Console

### No Articles Found

**Penyebab**:
- RSS feed URLs salah/unreachable
- Semua artikel sudah diproses
- Feed parsing error

**Solusi**:
1. Test feed URL manually: `curl -I https://feed-url.com/rss`
2. Check logs untuk parsing errors
3. Reset processed links jika perlu

---

## 🛡️ Best Practices

### 1. Rate Limiting
- Minimum interval: 15-30 menit antar run
- Jangan process terlalu banyak artikel per run
- Monitor API usage di Google Cloud Console

### 2. API Key Management
- Gunakan minimal 2-3 API keys untuk production
- Rotate keys secara berkala untuk security
- Simpan keys di password manager
- Set billing alerts di Google Cloud

### 3. RSS Feed Selection
- Pilih reliable sources dengan stable feeds
- Mix different publishers untuk diverse content
- Test feeds manually sebelum add ke config
- Monitor feed health secara berkala

### 4. Monitoring
- Check GitHub Actions logs regularly
- Monitor success rate articles processed
- Track API key rotation frequency
- Set up notifications for failures

### 5. Security
- Jangan commit secrets ke repository
- Use GitHub Secrets untuk semua credentials
- Rotate service account keys periodically
- Enable 2FA untuk GitHub & Google accounts

### 6. Testing
- Selalu test manual sebelum enable schedule
- Start dengan 1-2 artikel per run
- Verify output di Telegram sebelum scale up

---

## 📁 Struktur File

```
news-summary-telegram/
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
│   ├── storage/
│   │   └── storage_service.py    # Google Sheets + JSON
│   ├── content/
│   │   └── content_service.py    # Web scraper (3-layer)
│   ├── ai/
│   │   └── summary_service.py    # Gemini AI summarizer
│   ├── image/
│   │   └── image_service.py      # Image extractor
│   └── telegram/
│       └── telegram_service.py   # Telegram sender
├── main.py                       # Main entry point
├── requirements.txt              # Python dependencies
├── processed_links.json          # (Auto) Local storage
├── crawl_cache/                  # (Auto) Crawl4AI cache
└── README.md                     # This documentation
```

---

## 🧪 Testing & Development

### Local Testing

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/news-summary-telegram.git
cd news-summary-telegram

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHANNEL_ID="your_channel"
export GEMINI_API_KEYS="key1,key2"
export RSS_FEED_URLS="https://feed1.com/rss,https://feed2.com/rss"
export MAX_ARTICLES_PER_RUN="2"

# Run locally
python main.py
```

### Testing Individual Services

```python
# Test RSS Service
from services.rss import RSSFeedService

service = RSSFeedService()
articles = service.fetch_feed("https://example.com/rss")
print(f"Fetched {len(articles)} articles")

# Test AI Service
from services.ai import AISummaryService

ai_service = AISummaryService()
summary = ai_service.generate_summary(
    title="Test Article",
    content="This is test content...",
    author="John Doe",
    source_url="https://example.com/article"
)
print(summary)

# Test Telegram Service
from services.telegram import TelegramService

tg_service = TelegramService()
tg_service.send_message("Test message from Python!")
```

### Validate Configuration

```python
from config.settings import validate_config

try:
    validate_config()
    print("✅ Configuration valid!")
except ValueError as e:
    print(f"❌ Configuration error: {e}")
```

---

## ❓ FAQ

### Q: Berapa biaya total?
**A:** 100% GRATIS dengan konfigurasi default. Semua service yang digunakan memiliki free tier yang cukup untuk penggunaan personal.

### Q: Berapa lama proses per artikel?
**A:** Rata-rata 10-30 detik per artikel, tergantung:
- Kecepatan website source
- Model Gemini yang digunakan
- Network latency

### Q: Bagaimana cara stop workflow?
**A:** 
1. Disable workflow di GitHub Actions
2. Atau hapus secrets untuk break execution
3. Atau comment out cron schedule di workflow file

### Q: Bisa custom format ringkasan?
**A:** Ya! Edit prompt template di `services/ai/summary_service.py`.

### Q: Apakah support RSS feed berbayar?
**A:** Ya, selama RSS feed publicly accessible atau Anda provide authentication di URL.

### Q: Bagaimana backup data?
**A:** 
- Dengan Google Sheets: Auto-backup oleh Google Drive
- Dengan JSON: Download artifact dari GitHub Actions

### Q: Bisa kirim ke multiple Telegram channels?
**A:** Saat ini support single channel. Untuk multiple channels, fork dan setup multiple workflows.

### Q: Model AI apa saja yang digunakan?
**A:** Sistem menggunakan 8 free-tier Gemini models dengan automatic fallback:
- gemma-4-31b-it
- gemma-3n-e4b-it
- gemini-2.5-flash-preview-05-20
- gemini-2.0-flash-exp
- gemini-2.0-flash-thinking-exp-01-21
- gemini-2.0-flash-thinking-exp-1219
- gemini-2.0-pro-exp-02-05
- gemini-2.5-flash-image-preview

### Q: Bagaimana update script?
**A:**
```bash
git pull origin main
# Workflow akan auto-run dengan kode terbaru
```

---

## 📄 License

MIT License - Bebas digunakan untuk personal maupun commercial project.

## 🤝 Kontribusi

Pull request welcome! Untuk kontribusi:
1. Fork repository
2. Buat feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📞 Support

- **Bug Reports**: Buka issue di tab **Issues**
- **Questions**: Diskusi di tab **Discussions**
- **Security Issues**: Email langsung ke maintainer

---

**Dibuat dengan ❤️ menggunakan:**
- GitHub Actions (CI/CD)
- Google Gemini AI (Summarization)
- Crawl4AI (Web Scraping)
- Telegram Bot API (Messaging)
- Google Sheets (Storage)
- Python 3.11+

**Happy News Aggregating! 📰🚀**
