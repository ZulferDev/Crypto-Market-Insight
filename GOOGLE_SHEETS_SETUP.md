# 📊 Setup Google Sheets untuk Storage

## Mengapa Google Sheets?

Google Sheets adalah solusi storage yang lebih efisien dibanding commit/push ke GitHub karena:
- ✅ **Tidak perlu GitHub Token** untuk push/commit
- ✅ **Real-time updates** - data langsung tersimpan
- ✅ **Mudah dikelola** - bisa edit manual via UI
- ✅ **Free tier generous** - 5 juta cells gratis
- ✅ **Backup otomatis** - Google Drive backup
- ✅ **Queryable** - mudah filter/search data

## 📋 Langkah Setup

### 1. Buat Google Sheet Baru

1. Buka [Google Sheets](https://sheets.google.com)
2. Klik **+ Blank** untuk buat spreadsheet baru
3. Beri nama: `Crypto Market Insight - Processed Links`
4. Rename Sheet1 menjadi: `ProcessedLinks`

### 2. Setup Header Kolom

Di baris pertama, buat header berikut:
```
A1: Link
B1: Title
C1: Summary
D1: Processed At
E1: Author
F1: Image URL
```

### 3. Buat Service Account Google Cloud

#### A. Buat Project di Google Cloud Console

1. Buka [Google Cloud Console](https://console.cloud.google.com)
2. Klik **Select a project** → **New Project**
3. Beri nama: `crypto-market-insight`
4. Klik **Create**

#### B. Enable Google Sheets API

1. Di dashboard project, buka **APIs & Services** → **Library**
2. Search "Google Sheets API"
3. Klik **Enable**

#### C. Buat Service Account

1. Buka **APIs & Services** → **Credentials**
2. Klik **Create Credentials** → **Service Account**
3. Isi detail:
   - **Service account name**: `news-summary-bot`
   - **Description**: `Bot untuk save processed links`
4. Klik **Create and Continue**
5. Skip role assignment (opsional)
6. Klik **Done**

#### D. Download Service Account Key

1. Klik service account yang baru dibuat
2. Pilih tab **Keys**
3. Klik **Add Key** → **Create new key**
4. Pilih format: **JSON**
5. Klik **Create**
6. File JSON akan terdownload otomatis (simpan sebagai `service_account.json`)

### 4. Share Google Sheet ke Service Account

1. Buka file `service_account.json`, copy nilai dari field `client_email`
   ```json
   {
     "type": "service_account",
     "project_id": "...",
     "client_email": "news-summary-bot@crypto-market-insight.iam.gserviceaccount.com",
     ...
   }
   ```
2. Buka Google Sheet yang dibuat di langkah 1
3. Klik tombol **Share** (pojok kanan atas)
4. Paste email service account (`news-summary-bot@...`)
5. Set permission: **Editor**
6. Klik **Send/Done**

### 5. Dapatkan Spreadsheet ID

1. Buka Google Sheet
2. Lihat URL browser:
   ```
   https://docs.google.com/spreadsheets/d/1aBC123xyz456_DEF789/edit#gid=0
   ```
3. Copy string antara `/d/` dan `/edit`:
   ```
   Spreadsheet ID: 1aBC123xyz456_DEF789
   ```

### 6. Setup GitHub Secrets

Di repository GitHub, buka **Settings** → **Secrets and variables** → **Actions**:

Tambahkan secrets berikut:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `USE_GOOGLE_SHEETS` | `true` | Enable Google Sheets storage |
| `GOOGLE_SHEETS_ID` | `1aBC123xyz456_DEF789` | ID dari Google Sheet |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | `service_account.json` | Filename (default) |

### 7. Upload Service Account Key ke GitHub

Ada 2 opsi:

#### Opsi A: Upload sebagai GitHub Secret (Recommended)

1. Buka file `service_account.json`
2. Copy seluruh isi file (termasuk `{` dan `}`)
3. Di GitHub Secrets, buat secret baru:
   - **Name**: `SERVICE_ACCOUNT_JSON`
   - **Value**: Paste isi file JSON
4. Update workflow file untuk decode secret ini

#### Opsi B: Upload sebagai Encrypted File

1. Install gitleaks atau git-crypt untuk encrypt file
2. Commit file `service_account.json` yang sudah diencrypt
3. Decrypt di GitHub Actions menggunakan secret key

### 8. Update Workflow untuk Decode Service Account

Edit file `.github/workflows/news_summary.yml`:

```yaml
- name: Setup Service Account
  run: |
    echo "${{ secrets.SERVICE_ACCOUNT_JSON }}" > service_account.json

- name: Run news summary script
  env:
    # ... existing env vars ...
    GOOGLE_SERVICE_ACCOUNT_FILE: service_account.json
  run: python news_summary.py
```

## 🔧 Troubleshooting

### Error: "Permission denied"

**Solusi:**
- Pastikan email service account sudah di-share ke Google Sheet dengan permission **Editor**
- Cek ulang Spreadsheet ID benar

### Error: "Service account not found"

**Solusi:**
- Pastikan file `service_account.json` ada di root directory saat runtime
- Cek secret `SERVICE_ACCOUNT_JSON` sudah ter-set

### Error: "API not enabled"

**Solusi:**
- Buka Google Cloud Console
- Enable **Google Sheets API** untuk project Anda
- Tunggu beberapa menit untuk propagasi

## 📈 Monitoring & Maintenance

### View Data

- Buka Google Sheet langsung untuk lihat semua processed links
- Gunakan filter/sort untuk analisis
- Export ke CSV jika perlu backup

### Cleanup Old Data

Hapus row lama langsung dari Google Sheets UI untuk menghemat quota.

### Quota Limits

Google Sheets API Free Tier:
- **Read requests**: 300 per 60 seconds per user
- **Write requests**: 60 per 60 seconds per user
- **Total cells**: 5 million cells per spreadsheet

Untuk use case ini (1-5 artikel per 30 menit), quota lebih dari cukup!

## 🎯 Alternatif: Fallback ke Local JSON

Jika tidak ingin setup Google Sheets, sistem akan otomatis fallback ke `processed_links.json`:

```bash
# Set secret ini untuk disable Google Sheets
USE_GOOGLE_SHEETS=false
```

File JSON akan tersimpan di repository dan bisa di-download sebagai artifact setelah workflow selesai.

---

**Setup selesai!** 🎉 Sistem sekarang akan menyimpan semua processed links ke Google Sheets secara otomatis.
