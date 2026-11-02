# Checklist Pengujian Fungsional

Isi kolom hasil berdasarkan pengujian yang benar-benar dilakukan. Jangan menandai Lulus sebelum mencoba langsung.

| No | Skenario | Hasil yang diharapkan | Hasil aktual |
|---:|---|---|---|
| 1 | Login dengan akun Admin valid | Masuk ke dashboard dan role Admin terbaca | Belum diuji |
| 2 | Login dengan akun User valid | Masuk ke dashboard dan role User terbaca | Belum diuji |
| 3 | Login dengan password salah | Pesan kesalahan tampil, tidak masuk aplikasi | Belum diuji |
| 4 | User membuka URL tambah barang | Akses ditolak dan kembali ke dashboard | Belum diuji |
| 5 | Admin menambah barang dengan kode baru | Data tersimpan dan muncul di daftar | Belum diuji |
| 6 | Admin menambahkan kode barang duplikat | Data ditolak dengan pesan validasi | Belum diuji |
| 7 | Admin mengedit barang | Perubahan tampil pada daftar barang | Belum diuji |
| 8 | Admin menghapus barang tanpa transaksi | Data terhapus | Belum diuji |
| 9 | Admin mencatat transaksi Masuk | Stok barang bertambah | Belum diuji |
| 10 | Admin mencatat transaksi Keluar dengan stok cukup | Stok barang berkurang | Belum diuji |
| 11 | Admin mencatat transaksi Keluar melebihi stok | Transaksi ditolak dan stok tidak negatif | Belum diuji |
| 12 | User membuka laporan | Laporan dapat dilihat dan diekspor | Belum diuji |
| 13 | Logout | Session berakhir dan kembali ke login | Belum diuji |
