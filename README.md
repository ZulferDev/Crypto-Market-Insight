# AI News Summary to Telegram

Automated workflow yang mengambil berita dari RSS Feed, membuat ringkasan AI dengan Google Gemini, dan mengirimkannya ke Telegram Channel.

## 🚀 Alur Workflow

```
RSS Feed → Jina Reader (Extract Content) → Gemini AI (Summary) → Telegram Channel
```

## 📋 Prerequisites

1. **GitHub Account** - Untuk menjalankan GitHub Actions
2. **Telegram Bot** - Bot untuk mengirim pesan ke channel
3. **Google Gemini API Key** - Untuk generate summary
4. **RSS Feed URL** - Sumber berita

## 🔧 Setup Langkah-demi-Langkah

### 1. Buat Telegram Bot

1. Buka Telegram dan cari `@BotFather`
2. Kirim perintah `/newbot`
3. Ikuti instruksi untuk membuat bot
4. Simpan **Bot Token** yang diberikan

### 2. Buat Telegram Channel

1. Buat channel baru di Telegram
2. Invite bot Anda ke channel sebagai **Admin**
3. Dapatkan **Channel ID**:
   - Untuk public channel: `@nama_channel`
   - Untuk private channel: Forward pesan dari channel ke `@userinfobot` atau gunakan `@getmyid_bot`
   - Format ID: `-100xxxxxxxxxx`

### 3. Dapatkan Google Gemini API Key

1. Kunjungi [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Login dengan akun Google
3. Klik **Create API Key**
4. Simpan API key Anda

**Free Tier:** 1.5 juta tokens/hari (cukup untuk ~300-500 artikel/hari)

### 4. Setup GitHub Repository

```bash
# Clone repository ini
git clone https://github.com/username-anda/repo-anda.git
cd repo-anda

# Atau push kode yang sudah ada
git init
git add .
git commit -m "Initial commit: AI News Summary workflow"
git branch -M main
git remote add origin https://github.com/username-anda/repo-anda.git
git push -u origin main
```

### 5. Konfigurasi GitHub Secrets

Di GitHub repository Anda:

1. Pergi ke **Settings** → **Secrets and variables** → **Actions**
2. Klik **New repository secret**
3. Tambahkan secrets berikut:

| Secret Name | Value | Contoh |
|-------------|-------|--------|
| `TELEGRAM_BOT_TOKEN` | Token dari BotFather | `123456789:ABCdefGHIjklMNOpqrsTUVwxyz` |
| `TELEGRAM_CHANNEL_ID` | Channel ID | `-1001234567890` atau `@mychannel` |
| `GEMINI_API_KEY` | API Key dari Google AI Studio | `AIzaSy...` |
| `RSS_FEED_URL` | URL RSS feed berita | `https://kompas.id/rss` |

### 6. (Optional) Sesuaikan Konfigurasi

Edit file `.github/workflows/news_summary.yml`:

```yaml
# Ubah jadwal eksekusi (cron format)
schedule:
  - cron: '*/30 * * * *'  # Setiap 30 menit

# Atau tambahkan environment variables opsional
env:
  MAX_ARTICLES_PER_RUN: 5      # Max artikel per eksekusi
  SUMMARY_MAX_LENGTH: 1500     # Max karakter summary
```

### 7. Enable GitHub Actions

1. Pergi ke tab **Actions** di repository
2. Jika diminta, klik **I understand my workflows, go ahead and enable them**
3. Workflow akan otomatis jalan sesuai jadwal atau manual trigger

### 8. Test Manual

1. Di tab **Actions**, pilih workflow **AI News Summary to Telegram**
2. Klik **Run workflow**
3. Pilih branch `main`
4. Klik **Run workflow**
5. Monitor log eksekusi

## 📊 Monitoring

- **Logs:** Lihat di tab Actions → Workflow run → Job logs
- **Processed Links:** File `processed_links.txt` akan di-commit otomatis
- **Telegram:** Cek channel untuk melihat summary yang terkirim

## 🎛️ Kustomisasi Lanjutan

### Multiple RSS Feeds

Edit `news_summary.py` untuk support multiple feeds:

```python
RSS_FEED_URLS = os.getenv("RSS_FEED_URLS", "").split(",")

for feed_url in RSS_FEED_URLS:
    articles = fetch_rss_feed(feed_url.strip())
    # ... process each feed
```

### Custom Summary Prompt

Edit fungsi `generate_summary_with_gemini()` di `news_summary.py`:

```python
prompt = f"""
[Custom prompt Anda di sini]
...
"""
```

### Filter Berdasarkan Kategori

Tambahkan filter di `main()`:

```python
# Hanya proses artikel dengan keyword tertentu
keywords = ['teknologi', 'AI', 'startup']
filtered_articles = [
    a for a in new_articles 
    if any(k.lower() in a['title'].lower() for k in keywords)
]
```

## ⚠️ Troubleshooting

### Workflow tidak jalan
- Pastikan Actions enabled di repository
- Cek schedule cron format di [crontab.guru](https://crontab.guru)

### Error: Missing environment variables
- Pastikan semua secrets sudah ditambahkan di GitHub Settings
- Restart workflow setelah menambah secrets

### Error: Telegram message not sent
- Pastikan bot adalah **Admin** di channel
- Cek format Channel ID (harus ada `-` untuk numeric ID)
- Test bot token: `https://api.telegram.org/bot<YOUR_TOKEN>/getMe`

### Error: Gemini API quota exceeded
- Free tier: 1.5M tokens/hari (~300-500 artikel)
- Kurangi `MAX_ARTICLES_PER_RUN`
- Upgrade ke paid tier di [Google AI Studio](https://aistudio.google.com)

### Artikel ter-process berulang
- Pastikan `processed_links.txt` di-commit dan di-push
- Jangan hapus file tersebut dari repository

## 💰 Cost Breakdown (100% FREE)

| Service | Free Tier | Cukup Untuk |
|---------|-----------|-------------|
| GitHub Actions | 2000 menit/bulan | ~400-600 runs/bulan |
| Google Gemini API | 1.5M tokens/hari | ~300-500 artikel/hari |
| Jina Reader | Unlimited (no API key) | Unlimited |
| Telegram Bot | Unlimited | Unlimited |
| **Total** | **Rp 0** | **~15,000 artikel/bulan** |

## 📝 License

MIT License - Feel free to use and modify!

## 🤝 Contributing

Pull requests welcome! Untuk fitur request, silakan buka issue.

---

**Happy Automating! 🚀**
