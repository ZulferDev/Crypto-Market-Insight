# Google Sheets Storage Integration - Setup Guide

This document explains how to set up and use the Google Sheets-based persistent storage for the AI crypto pipeline.

---

## 🎯 Overview

The system now uses **Google Sheets** as the primary storage for tracking processed article links, replacing the unreliable JSON file approach. This enables:

- ✅ Persistent tracking across GitHub Actions runs
- ✅ No data loss on ephemeral filesystems
- ✅ Scalable storage
- ✅ Idempotent processing (no duplicates)
- ✅ Graceful fallback to JSON if Sheets fails

---

## 📋 Prerequisites

1. **Google Cloud Project** with Sheets API enabled
2. **Service Account** with appropriate credentials
3. **Google Sheet** created and shared with the service account

---

## 🔧 Step 1: Create Google Cloud Project & Service Account

### 1.1 Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing one)
3. Name it something like `crypto-pipeline-storage`

### 1.2 Enable Google Sheets API

1. In your project, go to **APIs & Services** → **Library**
2. Search for "Google Sheets API"
3. Click **Enable**

### 1.3 Create Service Account

1. Go to **IAM & Admin** → **Service Accounts**
2. Click **Create Service Account**
3. Fill in:
   - **Name**: `crypto-pipeline-sheets`
   - **Description**: Service account for storing processed article links
4. Click **Create and Continue**
5. Skip role assignment (not needed for Sheets access)
6. Click **Done**

### 1.4 Generate Service Account Key

1. Click on the newly created service account
2. Go to the **Keys** tab
3. Click **Add Key** → **Create new key**
4. Select **JSON** format
5. Click **Create**
6. Download the JSON file (keep it secure!)

---

## 📊 Step 2: Create Google Sheet

### 2.1 Create New Spreadsheet

1. Go to [Google Sheets](https://sheets.google.com/)
2. Create a new spreadsheet
3. Name it: `Crypto Pipeline - Processed Links`
4. Note the **Sheet ID** from the URL:
   ```
   https://docs.google.com/spreadsheets/d/1aBcDeFgHiJkLmNoPqRsTuVwXyZ/edit
                                          ^^^^^^^^^^^^^^^^^^^^^^^^
                                          This is your SHEET_ID
   ```

### 2.2 Create Worksheet

1. Rename the default sheet to: `processed_links` (lowercase, underscores)
2. Add headers in row 1:
   ```
   | url | title | source | processed_at | hash |
   ```
   
   | Column A | Column B | Column C | Column D | Column E |
   |----------|----------|----------|----------|----------|
   | url      | title    | source   | processed_at | hash   |

### 2.3 Share with Service Account

1. Click **Share** button in top-right
2. Copy the **service account email** from your JSON key file (look for `client_email`)
   - Format: `crypto-pipeline-sheets@project-id.iam.gserviceaccount.com`
3. Paste the email and give **Editor** access
4. Click **Send**

---

## 🔐 Step 3: Configure Environment Variables

### For Local Development

Create/update your `.env` file:

```bash
# Enable Google Sheets storage
USE_GOOGLE_SHEETS=true

# Google Sheet ID (from the URL)
GOOGLE_SHEET_ID=1aBcDeFgHiJkLmNoPqRsTuVwXyZ

# Service Account JSON (paste entire JSON content as single line)
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"your-project","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"crypto-pipeline-sheets@your-project.iam.gserviceaccount.com","client_id":"...","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"https://www.googleapis.com/robot/v1/metadata/x509/..."}

# Optional: Legacy file-based auth (for local dev)
GOOGLE_SERVICE_ACCOUNT_FILE=/path/to/service_account.json
```

### For GitHub Actions

In your repository settings:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Add these secrets:

```
USE_GOOGLE_SHEETS=true
GOOGLE_SHEET_ID=1aBcDeFgHiJkLmNoPqRsTuVwXyZ
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}  # Full JSON as single line
```

3. The workflow files have been updated to use these secrets. Example configuration:

```yaml
jobs:
  process-articles:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run pipeline
        env:
          USE_GOOGLE_SHEETS: ${{ secrets.USE_GOOGLE_SHEETS }}
          GOOGLE_SHEET_ID: ${{ secrets.GOOGLE_SHEET_ID }}
          GOOGLE_SERVICE_ACCOUNT_JSON: ${{ secrets.GOOGLE_SERVICE_ACCOUNT_JSON }}
          # ... other env vars (TELEGRAM_BOT_TOKEN, GEMINI_API_KEYS, etc.)
        run: python main.py
```

**Note**: The workflow no longer requires creating a local `service_account.json` file. Credentials are passed directly via the `GOOGLE_SERVICE_ACCOUNT_JSON` environment variable.

---

## 📦 Required Dependencies

Add to your `requirements.txt`:

```txt
gspread>=5.12.0
google-auth>=2.27.0
```

Install:

```bash
pip install gspread google-auth
```

---

## 🚀 Usage

### Basic Usage (Automatic)

The storage service automatically uses Google Sheets when configured:

```python
from services.storage import StorageService, ProcessedArticle

# Initialize (auto-detects Google Sheets config)
storage = StorageService()

# Load previously processed articles
processed_data = storage.load_processed_data()

# Check if article was already processed
if storage.is_processed(article_link, processed_data):
    print("Already processed, skipping...")
    continue

# After processing, add to storage
article = ProcessedArticle(
    link=article_link,
    title=article_title,
    summary=summary,
    processed_at=datetime.now().isoformat(),
    author=author
)
storage.add_article(processed_data, article)

# At end of run, flush to Google Sheets
storage.save_processed_data(processed_data)
```

### Direct Sheets Storage Usage

```python
from services.storage import SheetsStorage

# Initialize
sheets = SheetsStorage()

# Fetch all processed links (cached in memory)
processed_urls = sheets.fetch_processed_links()

# Check if URL is processed (uses hash comparison too)
if sheets.is_processed(url):
    print("Skip")

# Mark as processed (adds to pending batch)
sheets.mark_as_processed(
    url="https://example.com/article",
    title="Article Title",
    source="CoinDesk"
)

# Flush all pending writes at once (batch operation)
sheets.flush_processed_links()
```

---

## 🏗️ Architecture

### Flow

```
┌─────────────────────────────────────────────────────────────┐
│  Pipeline Start                                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  1. fetch_processed_links()                                  │
│     - Fetch ALL processed URLs from Google Sheets ONCE       │
│     - Store in memory (set) for O(1) lookup                  │
│     - Also store SHA256 hashes for dedup                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  2. For each article:                                        │
│     - if url in processed_set → SKIP                         │
│     - Process article                                        │
│     - mark_as_processed() → adds to pending batch            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  3. End of run: flush_processed_links()                      │
│     - Batch insert ALL new rows at once                      │
│     - Single API call (not per-item!)                        │
└─────────────────────────────────────────────────────────────┘
```

### Key Features

| Feature | Implementation |
|---------|---------------|
| **No per-item API calls** | Fetch once at start, batch write at end |
| **Hash-based dedup** | SHA256(URL) handles tracking params |
| **Exact URL match** | Direct string comparison |
| **Graceful fallback** | If Sheets fails, continues with JSON |
| **GitHub Actions ready** | Credentials from env var, no files |

---

## 🛡️ Error Handling

The system is designed to **never crash** due to Google Sheets issues:

```python
try:
    # Try Google Sheets
    if sheets_available and sheets_configured:
        use_google_sheets()
except Exception as e:
    print(f"⚠️ Sheets error: {e}")
    # Automatically falls back to JSON
    use_json_fallback()
```

If Google Sheets fails:
- ❌ Logs error message
- ✅ Continues pipeline execution
- ✅ Saves to local JSON as backup
- ✅ Does NOT crash the system

---

## 📊 Sheet Structure

The `processed_links` worksheet has this structure:

| Column | Name | Type | Description |
|--------|------|------|-------------|
| A | `url` | String | Full article URL |
| B | `title` | String | Article title |
| C | `source` | String | Source name (e.g., "CoinDesk") |
| D | `processed_at` | ISO Timestamp | When it was processed |
| E | `hash` | SHA256 | Hash of URL for dedup |

Example row:
```
| https://coindesk.com/article | Bitcoin Hits $100K | CoinDesk | 2025-01-15T10:30:00 | a1b2c3d4... |
```

---

## 🔍 Troubleshooting

### "GOOGLE_SHEET_ID not set"

**Solution**: Set the environment variable:
```bash
export GOOGLE_SHEET_ID=your-sheet-id
```

### "GOOGLE_SERVICE_ACCOUNT_JSON not set"

**Solution**: Paste the full JSON content:
```bash
export GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'
```

For GitHub Actions, add as a secret.

### "Permission denied"

**Solution**: Share the Google Sheet with the service account email:
1. Copy `client_email` from your JSON key
2. Share the sheet with that email (Editor access)

### "Worksheet 'processed_links' not found"

**Solution**: Rename your worksheet tab to exactly `processed_links` (lowercase, underscore).

---

## 🧪 Testing

Test locally:

```bash
# Set environment
export USE_GOOGLE_SHEETS=true
export GOOGLE_SHEET_ID=your-sheet-id
export GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'

# Run pipeline
python main.py
```

Check logs for:
- `✅ Google Sheets storage initialized: processed_links`
- `📊 Fetched X processed links from Google Sheets`
- `📊 Flushed X processed links to Google Sheets`

---

## 📝 Migration from JSON

Existing `processed_links.json` is kept as **backup**. The system:

1. Tries Google Sheets first
2. Falls back to JSON if Sheets unavailable
3. Always saves to JSON as secondary storage

No manual migration needed!

---

## 🔒 Security Best Practices

1. **Never commit** service account JSON to git
2. Use **GitHub Secrets** for CI/CD
3. Restrict service account permissions (only Sheets access)
4. Rotate keys periodically
5. Monitor Sheets API usage in Google Cloud Console

---

## 📈 Performance

| Operation | Old (per-item) | New (batch) |
|-----------|----------------|-------------|
| Read at start | N API calls | 1 API call |
| Write per article | 1 API call each | 0 (buffered) |
| Flush at end | N/A | 1 API call |
| **Total for 10 articles** | ~10 calls | **2 calls** |

**5x reduction in API calls!**

---

## ✅ Checklist

Before deploying:

- [ ] Google Cloud project created
- [ ] Sheets API enabled
- [ ] Service account created
- [ ] JSON key downloaded
- [ ] Google Sheet created
- [ ] Worksheet named `processed_links`
- [ ] Headers added (url, title, source, processed_at, hash)
- [ ] Sheet shared with service account
- [ ] Environment variables configured
- [ ] Dependencies installed (`gspread`, `google-auth`)
- [ ] Tested locally
- [ ] GitHub Secrets configured

---

## 📞 Support

Issues? Check:
1. Logs for error messages
2. Google Cloud Console for API errors
3. Sheet sharing permissions
4. Environment variable values

---

**Happy tracking! 🚀**
