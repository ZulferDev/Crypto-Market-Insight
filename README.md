# AI News Summary to Telegram

Workflow otomatis untuk mengambil berita dari RSS feed, mengekstrak konten dengan **Crawl4AI**, membuat ringkasan AI dengan **Google Gemini**, dan mengirim ke **Telegram Channel**.

## 🚀 Fitur

- ✅ **RSS Feed Parser** - Monitor sumber berita favorit Anda
- ✅ **Crawl4AI Web Scraper** - Ekstraksi konten lengkap dari artikel (menggantikan Jina Reader)
- ✅ **Google Gemini AI** - Ringkasan cerdas dalam bahasa Indonesia
- ✅ **Telegram Integration** - Kirim otomatis ke channel Telegram
- ✅ **Deduplikasi** - Skip artikel yang sudah diproses
- ✅ **Rate Limiting** - Hindari API limits
- ✅ **Scheduled & Manual Trigger** - Jalankan otomatis atau manual

## 💰 Biaya: **GRATIS (Rp 0,-)**

| Service | Limit Gratis | Cukup Untuk |
|---------|--------------|-------------|
| GitHub Actions | 2000 menit/bulan | ~60-100 run/hari |
| Google Gemini API | 1.5M tokens/hari | ~300-500 artikel/hari |
| Crawl4AI | Unlimited (self-hosted) | Semua kebutuhan |
| Telegram Bot | Unlimited | Semua kebutuhan |

## 📋 Prasyarat

1. **GitHub Account** - Untuk hosting repository dan GitHub Actions
2. **Telegram Bot Token** - Dari [@BotFather](https://t.me/BotFather)
3. **Telegram Channel ID** - Channel tempat mengirim summary
4. **Google Gemini API Key** - Dari [Google AI Studio](https://aistudio.google.com/app/apikey)
5. **RSS Feed URL** - Sumber berita yang ingin dimonitor

## 🔧 Setup Langkah demi Langkah

### 1. Fork/Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/news-summary-telegram.git
cd news-summary-telegram
```

### 2. Buat Telegram Bot

1. Chat dengan [@BotFather](https://t.me/BotFather) di Telegram
2. Kirim `/newbot` dan ikuti instruksi
3. Simpan **BOT TOKEN** yang diberikan
4. Buat channel Telegram (atau gunakan yang sudah ada)
5. Invite bot ke channel sebagai **Admin**
6. Dapatkan **Channel ID** (format: `@channelname` atau `-100xxxxxxxxxx`)
   - Cara dapatkan ID: Forward pesan dari channel ke [@userinfobot](https://t.me/userinfobot)

### 3. Dapatkan Gemini API Key

1. Buka [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Login dengan akun Google
3. Klik **Create API Key**
4. Simpan API key

### 4. Setup GitHub Secrets

1. Buka repository GitHub Anda
2. Go to **Settings** → **Secrets and variables** → **Actions**
3. Klik **New repository secret** dan tambahkan:

| Secret Name | Value | Contoh |
|-------------|-------|--------|
| `TELEGRAM_BOT_TOKEN` | Token dari BotFather | `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz` |
| `TELEGRAM_CHANNEL_ID` | Channel ID | `@mynewschannel` atau `-1001234567890` |
| `GEMINI_API_KEY` | API Key dari Google AI Studio | `AIzaSy...` |
| `RSS_FEED_URL` | URL RSS feed berita | `https://kompas.com/rss` |

### 5. Aktifkan GitHub Actions

1. Go to **Actions** tab di repository GitHub
2. Klik **I understand my workflows, go ahead and enable workflows**
3. Workflow akan berjalan otomatis setiap 30 menit

### 6. Test Manual (Optional)

1. Go to **Actions** → **AI News Summary to Telegram**
2. Klik **Run workflow**
3. Pilih branch `main`
4. Klik **Run workflow**
5. Tunggu proses selesai (~1-2 menit)

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
    
    # Setiap hari jam 8 pagi
    - cron: '0 8 * * *'
```

### Ubah Jumlah Artikel Per Run

Tambahkan secret baru atau edit di script:

```bash
# Di GitHub Secrets
MAX_ARTICLES_PER_RUN = 10  # Default: 5
```

### Custom Prompt AI

Edit fungsi `generate_summary_with_gemini()` di `news_summary.py` untuk mengubah format ringkasan.

## 📁 Struktur File

```
news-summary-telegram/
├── .github/
│   └── workflows/
│       └── news_summary.yml      # GitHub Actions workflow
├── news_summary.py               # Script utama Python
├── requirements.txt              # Dependencies Python
├── processed_links.txt           # (Auto-generated) Track artikel yang sudah diproses
├── crawl_cache/                  # (Auto-generated) Cache Crawl4AI
└── README.md                     # Dokumentasi ini
```

## 🔍 Troubleshooting

### Workflow Gagal dengan Error "Playwright browser not found"

Pastikan langkah install playwright ada di workflow:

```yaml
- name: Install dependencies
  run: |
    pip install crawl4ai playwright
    playwright install chromium --with-deps
```

### Error "Telegram Bot not authorized"

- Pastikan bot sudah diinvite ke channel sebagai **Admin**
- Cek Channel ID format (harus benar, bisa coba dengan `@username` atau `-100xxxxx`)

### Error "Gemini API quota exceeded"

- Limit gratis: 1.5M tokens/hari (~300-500 artikel)
- Kurangi `MAX_ARTICLES_PER_RUN` atau tunggu reset besok

### Artikel Ter-duplikasi

- File `processed_links.txt` menyimpan history
- Reset dengan hapus file tersebut atau edit manual

### Crawl4AI Timeout/Lambat

- Beberapa website punya anti-bot protection
- Increase timeout di konfigurasi Crawl4AI
- Coba website alternatif/source RSS lain

## 🛡️ Best Practices

1. **Rate Limiting**: Jangan set interval terlalu cepat (min 15-30 menit)
2. **Monitor Usage**: Cek GitHub Actions usage di Settings → Actions
3. **Backup Secrets**: Simpan secrets di tempat aman (password manager)
4. **Test Dulu**: Jalankan manual dulu sebelum enable schedule
5. **Error Handling**: Workflow sudah include error handling, tapi monitor logs secara berkala

## 📊 Estimasi Penggunaan

Dengan konfigurasi default (5 artikel per run, setiap 30 menit):

| Resource | Penggunaan/Hari | Penggunaan/Bulan | Limit Gratis |
|----------|-----------------|------------------|--------------|
| GitHub Actions | ~20 menit | ~10 jam | 2000 menit |
| Gemini Tokens | ~50K tokens | ~1.5M tokens | 1.5M/hari |
| Artikel Diproses | ~240 artikel | ~7200 artikel | Unlimited |

**Kesimpulan**: Konfigurasi default **100% gratis** dan sustainable!

## 🔄 Update & Maintenance

### Update Script

```bash
git pull origin main
# Workflow akan auto-run dengan kode terbaru
```

### Reset Processed Links

Hapus file `processed_links.txt` di repository untuk memproses ulang semua artikel.

### Change RSS Source

Update secret `RSS_FEED_URL` di GitHub Secrets.

## 📝 License

MIT License - Bebas digunakan untuk personal maupun commercial project.

## 🤝 Kontribusi

Pull request welcome! Untuk fitur baru atau bug fix.

## 📞 Support

Untuk pertanyaan atau issue, buka **Issues** tab di GitHub repository.

---

**Dibuat dengan ❤️ menggunakan GitHub Actions, Crawl4AI, Google Gemini, dan Telegram Bot API**
