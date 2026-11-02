# InventarisKu — Sistem Informasi Inventaris Barang

Aplikasi web tugas kuliah berbasis **Python Flask + MySQL/MariaDB**. Project ini disiapkan berdasarkan dump database `db_invetaris.sql` yang diberikan: tabel `barang`, `kategori`, `lokasi`, dan `transaksi` tetap dipakai. Aplikasi menambahkan tabel `users` untuk autentikasi dan role.

## Fitur

- Login dan logout dengan password hash.
- Dua role: **Admin** dan **User**.
- Admin: CRUD barang, kategori, lokasi, transaksi, dan akun pengguna.
- User: melihat dashboard, data barang, kategori, lokasi, transaksi, dan laporan.
- Dashboard ringkasan stok, kategori, lokasi, barang stok rendah, dan transaksi terbaru.
- Transaksi masuk/keluar otomatis memperbarui stok. Stok keluar tidak boleh melebihi stok tersedia.
- Tiga laporan: inventaris, stok, dan transaksi; dapat dicetak ke PDF melalui browser atau diunduh sebagai CSV.
- Search dan filter data barang/transaksi.
- CSRF protection untuk form POST.
- UI responsif dengan CSS sendiri; Google Fonts hanya untuk font tambahan.

## Isi folder penting

```text
inventaris_web/
├── app.py                  # Aplikasi Flask dan seluruh route
├── init_db.py              # Membuat tabel users dan 10 akun demo
├── requirements.txt
├── .env.example            # Contoh konfigurasi lokal
├── Procfile                # Start command hosting
├── render.yaml             # Template deploy Render
├── sql/
│   ├── db_invetaris.sql    # Dump database awal yang diberikan
│   ├── 01_tabel_users.sql  # Struktur tabel autentikasi
│   └── 02_contoh_query.sql # 6 query contoh untuk tugas
├── docs/ERD.mmd            # ERD Mermaid
├── templates/              # Halaman HTML Jinja
└── static/css/style.css    # Desain UI
```

## Menjalankan di Windows

1. Pastikan Python 3.10+ dan MySQL/MariaDB aktif (XAMPP juga bisa).
2. Buat database bernama `db_invetaris` di phpMyAdmin.
3. Import `sql/db_invetaris.sql` ke database tersebut. Dump ini berisi 4 tabel awal beserta 10 data contoh pada setiap tabel.
4. Buka folder project di VS Code.
5. Buat virtual environment dan install library:

   ```powershell
   python -m venv venv
   .\venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

   Aktivasi environment **tidak wajib**. Semua perintah berikut bisa dipanggil melalui `venv\Scripts\python.exe`. Bila ingin aktivasi PowerShell, jalankan `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` lalu `\.\venv\Scripts\Activate.ps1`.

6. Buka file `.env` yang sudah disertakan, lalu sesuaikan `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, dan `DB_PASSWORD` dengan MySQL lokal. Jika `.env` tidak ada, salin `.env.example` menjadi `.env`. Jangan unggah `.env` ke GitHub.
7. Buat tabel users dan 10 akun contoh:

   ```powershell
   venv\Scripts\python.exe init_db.py
   ```

8. Jalankan aplikasi:

   ```powershell
   venv\Scripts\python.exe app.py
   ```

9. Buka `http://127.0.0.1:5000`.

### Akun demo lokal

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `Admin123!` |
| User | `user01` sampai `user09` | `User123!` |

**Penting:** ganti password akun demo melalui menu Profil atau Pengguna sebelum aplikasi dipublikasikan. Jangan gunakan password demo sebagai password permanen.

## Hosting gratis (untuk demo tugas)

Arsitektur yang direkomendasikan: **Render Free Web Service** untuk menjalankan Flask dan **Aiven Free MySQL** untuk database cloud. Paket ini bukan untuk aplikasi produksi; layanan gratis memiliki batas penggunaan dan dapat tidur/nonaktif.

### A. Siapkan database cloud di Aiven

1. Buat akun Aiven dan buat layanan **MySQL Free**.
2. Catat host, port, nama database, username, dan password dari halaman connection information.
3. Unduh CA certificate yang disediakan Aiven. Simpan sebagai `certs/ca.pem` di project jika koneksinya memerlukan sertifikat CA.
4. Buat database baru dengan nama `db_invetaris` (atau gunakan database yang disediakan dan samakan nama `DB_NAME`).
5. Import `sql/db_invetaris.sql` ke database cloud melalui phpMyAdmin/klien MySQL yang mendukung koneksi remote dan TLS.
6. Setelah import berhasil, jalankan `init_db.py` dengan konfigurasi database cloud untuk membuat tabel `users` dan akun demo. Alternatif: jalankan SQL `sql/01_tabel_users.sql`, lalu seed akun melalui `init_db.py`.

### B. Deploy aplikasi di Render

1. Upload folder project ini ke repository GitHub. Pastikan `.env` tidak ikut ter-upload; `.gitignore` sudah mengabaikannya.
2. Di Render pilih **New → Web Service**, hubungkan repository tersebut.
3. Pilih runtime Python, plan Free, build command `pip install -r requirements.txt`, start command `gunicorn app:app`.
4. Tambahkan environment variables di Render:
   - `SECRET_KEY`: string acak yang panjang.
   - `COOKIE_SECURE`: `true`.
   - `FLASK_DEBUG`: `false`.
   - `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`: ambil dari Aiven.
   - `DB_SSL_CA`: path file CA certificate yang ikut tersedia dalam project, misalnya `certs/ca.pem`.
5. Deploy dan buka URL `onrender.com` yang diberikan Render. Tes login, lihat data, tambah transaksi, dan halaman laporan.

**Catatan paket gratis:** Render dapat menidurkan web service setelah periode tidak ada trafik sehingga kunjungan pertama setelah idle bisa lambat. Aiven Free MySQL memiliki batas resource dan dapat dimatikan setelah lama tidak aktif; periksa status layanan sebelum demo dosen. Jangan menyimpan data sensitif atau memakai akun demo di luar keperluan tugas.

## Role dan hak akses

| Fitur | Admin | User |
|---|:---:|:---:|
| Dashboard | ✓ | ✓ |
| Melihat barang/kategori/lokasi | ✓ | ✓ |
| Tambah, edit, hapus barang | ✓ | — |
| Kelola kategori dan lokasi | ✓ | — |
| Catat/edit/hapus transaksi | ✓ | — |
| Melihat laporan dan export | ✓ | ✓ |
| Kelola akun pengguna | ✓ | — |
| Ganti password sendiri | ✓ | ✓ |

## Catatan database dan tugas dosen

- 4 tabel inti dari dump: `barang`, `kategori`, `lokasi`, `transaksi`.
- Tabel tambahan autentikasi: `users`.
- Primary key dan foreign key berada pada tabel inti sesuai dump awal.
- `sql/02_contoh_query.sql` berisi 6 contoh query (lebih dari minimum 5).
- Halaman Laporan berisi 3 bentuk laporan: data inventaris, stok, dan transaksi.
- ERD ada di `docs/ERD.mmd`. File Mermaid dapat dibuka di editor yang mendukung Mermaid atau ditempel di Mermaid Live Editor untuk diekspor menjadi gambar.
- Untuk berkas PDF tugas, ambil screenshot aplikasi setelah menjalankan data sendiri. Laporan cetak pada menu Laporan bisa disimpan sebagai PDF dari dialog Print browser.

## Troubleshooting singkat

- `Access denied`: periksa username/password dan hak akses MySQL.
- `Unknown database`: buat database `db_invetaris` atau samakan `DB_NAME`.
- `Table 'users' doesn't exist`: jalankan `python init_db.py` setelah database awal diimport.
- `Can't connect to MySQL`: pastikan service MySQL hidup, host dan port benar, dan remote access diizinkan pada hosting database.
- Tampilan font berbeda saat offline: aplikasi tetap berfungsi; Google Fonts hanya font tambahan.
