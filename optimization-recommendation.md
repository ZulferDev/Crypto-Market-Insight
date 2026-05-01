# Optimalisasi Alur AI Summary ke Telegram (Gratis)

## Analisis Alur Saat Ini

**Alur yang diusulkan:**
RSS Feed → Zapier/Relay.app → Webhook CircleCI → Parse RSS → Jina Reader → Gemini API → Telegram Bot

**Masalah dengan alur saat ini:**
1. **CircleCI tidak dirancang untuk workflow seperti ini** - CircleCI adalah CI/CD tool untuk build/test/deploy code, bukan untuk menjalankan automation workflow berbasis event
2. **Over-engineering** - Menggunakan CircleCI hanya untuk memanggil API adalah penggunaan resource yang tidak efisien
3. **Limitasi gratis CircleCI** - 6000 credits/bulan (~1500-2000 menit build), terlalu boros untuk workflow sederhana
4. **Latency tinggi** - CircleCI build startup time bisa 30-60 detik sebelum job benar-benar jalan
5. **Kompleksitas maintenance** - Perlu config `.circleci/config.yml`, Docker image, dll

---

## Saran Optimalisasi (100% Gratis)

### 🏆 **REKOMENDASI UTAMA: Gunakan n8n.cloud atau Make.com**

#### **Opsi 1: n8n.cloud (Paling Direkomendasikan)**
**Platform:** [n8n.cloud](https://n8n.io) (Free tier: 100 executions/hari)

**Alur Optimal:**
```
RSS Feed Trigger → HTTP Request (Jina Reader) → Google Gemini API → Telegram Bot
```

**Keuntungan:**
- ✅ Semua node tersedia native (RSS, HTTP Request, Google Gemini, Telegram)
- ✅ Visual workflow builder, mudah maintenance
- ✅ Error handling built-in
- ✅ Logging dan monitoring
- ✅ Schedule trigger (bisa cek RSS setiap 15-30 menit)
- ✅ 100 executions/hari cukup untuk 40-50 artikel/hari

**Implementasi:**
1. Buat workflow di n8n.cloud
2. Tambahkan node "RSS Read" untuk monitor feed
3. Node "HTTP Request" ke `https://r.jina.ai/{URL}` untuk extract content
4. Node "Google Gemini" untuk generate summary
5. Node "Telegram" untuk kirim ke channel

---

#### **Opsi 2: Make.com (Alternatif jika n8n penuh)**
**Platform:** [Make.com](https://make.com) (Free tier: 1000 operations/bulan)

**Alur:** Sama seperti n8n

**Keuntungan:**
- ✅ 1000 operations/bulan (~33 operations/hari)
- ✅ Interface sangat user-friendly
- ✅ Integrasi Telegram native
- ✅ Support HTTP request ke Jina + Gemini

**Kekurangan:**
- ❌ Operation count lebih ketat daripada n8n
- ❌ Gemini mungkin perlu via HTTP request (tidak ada native node)

---

#### **Opsi 3: GitHub Actions (Sepenuhnya Gratis, Unlimited)**
**Platform:** GitHub Actions (Free: 2000 minutes/bulan)

**Alur:**
```
GitHub Schedule Trigger (cron) → Python Script → Jina Reader → Gemini API → Telegram
```

**Keuntungan:**
- ✅ 2000 menit/bulan GRATIS
- ✅ Sepenuhnya customizable
- ✅ Tidak ada limit executions per hari
- ✅ Version control built-in

**Implementasi:**
```yaml
# .github/workflows/news-summary.yml
name: News Summary to Telegram

on:
  schedule:
    - cron: '*/30 * * * *'  # Setiap 30 menit
  workflow_dispatch:  # Manual trigger

jobs:
  summarize-and-send:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install feedparser requests google-generativeai
      
      - name: Run summary script
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          RSS_FEED_URL: ${{ secrets.RSS_FEED_URL }}
        run: python main.py
```

**Script Python (main.py):**
```python
import feedparser
import requests
import google.generativeai as genai
import os
from datetime import datetime

# Config
GEMINI_API_KEY = os.environ['GEMINI_API_KEY']
TELEGRAM_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
TELEGRAM_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
RSS_URL = os.environ['RSS_FEED_URL']

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Parse RSS
feed = feedparser.parse(RSS_URL)

for entry in feed.entries[:3]:  # Max 3 artikel per run
    # Extract content via Jina Reader
    jina_url = f"https://r.jina.ai/{entry.link}"
    response = requests.get(jina_url)
    content = response.text
    
    # Generate summary
    prompt = f"""
    Buatkan ringkasan berita dalam bahasa Indonesia (max 150 kata):
    
    Judul: {entry.title}
    Konten: {content[:3000]}
    
    Format output:
    📰 {entry.title}
    
    [Ringkasan]
    
    🔗 Sumber: {entry.link}
    """
    
    result = model.generate_content(prompt)
    summary = result.text
    
    # Send to Telegram
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(telegram_url, json={
        'chat_id': TELEGRAM_CHAT_ID,
        'text': summary,
        'parse_mode': 'Markdown'
    })
```

---

#### **Opsi 4: Self-hosted n8n (Gratis Sepenuhnya)**
**Platform:** n8n self-hosted di Railway/Render/Hugging Face Spaces

**Keuntungan:**
- ✅ Unlimited executions
- ✅ Fitur sama dengan n8n.cloud
- ✅ Gratis jika host di platform free tier

**Host gratis options:**
- Hugging Face Spaces (CPU free)
- Render (750 jam/bulan free)
- Railway ($5 credit awal, lalu pay)

---

## Perbandingan Platform

| Platform | Free Limit | Kemudahan | Fleksibilitas | Rekomendasi |
|----------|-----------|-----------|---------------|-------------|
| **n8n.cloud** | 100 exec/hari | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 🏆 Terbaik |
| **GitHub Actions** | 2000 min/bulan | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 🥈 Paling stabil |
| **Make.com** | 1000 ops/bulan | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 🥉 Alternatif |
| **CircleCI** | 6000 credits/bulan | ⭐⭐ | ⭐⭐ | ❌ Tidak direkomendasikan |
| **Zapier** | 100 tasks/bulan | ⭐⭐⭐⭐⭐ | ⭐⭐ | ❌ Limit terlalu ketat |

---

## Stack Teknologi Gratis yang Digunakan

1. **RSS Parser:** Native di n8n/Make atau `feedparser` (Python)
2. **Web Content Extractor:** [Jina Reader](https://jina.ai/reader) - `https://r.jina.ai/{URL}`
   - Gratis, tanpa API key
   - Convert webpage ke markdown/text
3. **AI Model:** [Google Gemini API](https://aistudio.google.com/apikey)
   - Free tier: 15 RPM (requests per minute), 1M tokens/hari
   - Model rekomendasi: `gemini-1.5-flash` (cepat & murah)
4. **Telegram Bot:** [BotFather](https://t.me/BotFather)
   - 100% gratis, unlimited messages
5. **Automation Platform:** n8n.cloud / GitHub Actions

---

## Langkah Implementasi (Rekomendasi: n8n.cloud)

### Step 1: Setup Telegram Bot
```bash
1. Chat ke @BotFather di Telegram
2. /newbot
3. Ikuti instruksi, simpan TOKEN
4. Add bot ke channel sebagai admin
5. Dapatkan CHAT_ID (forward message ke @userinfobot)
```

### Step 2: Dapatkan Gemini API Key
```bash
1. Kunjungi https://aistudio.google.com/apikey
2. Login dengan Google account
3. Create API key
4. Simpan key
```

### Step 3: Buat Workflow di n8n.cloud
```bash
1. Sign up di https://n8n.cloud (gratis)
2. Create new workflow
3. Tambahkan nodes:
   - Trigger: Schedule (setiap 30 menit)
   - Node: RSS Read (input URL feed)
   - Node: HTTP Request (GET https://r.jina.ai/{article_url})
   - Node: Google Gemini (generate summary)
   - Node: Telegram (send message)
4. Test workflow
5. Activate
```

---

## Optimasi Tambahan

### 1. **Deduplikasi Artikel**
- Simpan ID artikel yang sudah diproses (di n8n: use "Merge" node + database sederhana)
- Atau gunakan GitHub Actions dengan file tracking di repo

### 2. **Rate Limiting**
- Gemini: max 15 RPM → delay 4-5 detik antar request
- Telegram: max 30 msg/detik → aman untuk workflow ini

### 3. **Error Handling**
- Retry mechanism jika Jina/Gemini down
- Fallback: skip artikel jika error, lanjut ke berikutnya

### 4. **Format Pesan Telegram**
```markdown
📰 **Judul Artikel**

🗞️ Ringkasan:
[Isi ringkasan 100-150 kata]

🔗 Baca selengkapnya: {link}
⏰ {timestamp}
```

### 5. **Multi-RSS Feed**
- Gabungkan beberapa RSS feed dalam satu workflow
- Filter berdasarkan keyword jika perlu

---

## Estimasi Biaya: Rp 0,- (100% Gratis)

| Komponen | Biaya |
|----------|-------|
| n8n.cloud / GitHub Actions | Gratis |
| Jina Reader | Gratis |
| Google Gemini API | Gratis (1.5M tokens/hari) |
| Telegram Bot | Gratis |
| **Total** | **Rp 0,-** |

---

## Kesimpulan

**Jangan gunakan CircleCI** untuk use case ini karena:
- ❌ Bukan tool yang tepat untuk automation workflow
- ❌ Overhead tinggi (build time, config kompleks)
- ❌ Boros credit limit

**Gunakan salah satu dari:**
1. **n8n.cloud** - Paling mudah, visual, cepat setup (RECOMMENDED)
2. **GitHub Actions** - Paling stabil, unlimited, tapi perlu coding sedikit
3. **Make.com** - Alternatif jika n8n tidak available

Semua opsi di atas 100% gratis untuk skala kecil-menengah (50-100 artikel/hari).
