"""Inisialisasi skema dan data demo InventarisKu.

Aman dijalankan berulang kali: data contoh hanya dimasukkan bila tabel terkait kosong,
dan akun demo hanya dibuat bila username belum ada.
"""
import os
from datetime import date

from werkzeug.security import generate_password_hash
from app import app, db, User, Kategori, Lokasi, Barang, Transaksi

KATEGORI = [
    (1, "Elektronik"),
    (2, "Komputer"),
    (3, "Peralatan Kantor"),
    (4, "Furniture"),
    (5, "Peralatan Jaringan"),
    (6, "Alat Tulis"),
    (7, "Peralatan Kebersihan"),
    (8, "Peralatan Laboratorium"),
    (9, "Peralatan Presentasi"),
    (10, "Peralatan Listrik"),
]

LOKASI = [
    (1, "Ruang Admin", "Tempat penyimpanan barang administrasi"),
    (2, "Ruang IT", "Tempat penyimpanan komputer dan laptop"),
    (3, "Gudang Utama", "Gudang penyimpanan barang utama"),
    (4, "Ruang Kelas 1", "Tempat peralatan belajar"),
    (5, "Ruang Kelas 2", "Tempat peralatan belajar"),
    (6, "Laboratorium", "Tempat peralatan praktikum"),
    (7, "Ruang Dosen", "Tempat perlengkapan dosen"),
    (8, "Ruang Rapat", "Tempat peralatan rapat"),
    (9, "Perpustakaan", "Tempat perlengkapan perpustakaan"),
    (10, "Ruang Server", "Tempat perangkat jaringan dan server"),
]

BARANG = [
    (1, "BRG001", "Laptop Asus", 2, 2, 10, "Baik"),
    (2, "BRG002", "Komputer Lenovo", 2, 2, 8, "Baik"),
    (3, "BRG003", "Printer Epson", 1, 1, 5, "Baik"),
    (4, "BRG004", "Meja Kantor", 4, 1, 12, "Baik"),
    (5, "BRG005", "Kursi Kantor", 4, 1, 20, "Baik"),
    (6, "BRG006", "Router TP-Link", 5, 10, 7, "Baik"),
    (7, "BRG007", "Keyboard Logitech", 2, 2, 15, "Baik"),
    (8, "BRG008", "Mouse Wireless", 2, 2, 18, "Baik"),
    (9, "BRG009", "Proyektor Epson", 9, 4, 4, "Baik"),
    (10, "BRG010", "Kabel HDMI", 5, 3, 25, "Baik"),
]

TRANSAKSI = [
    (1, "Masuk", 5, "2026-10-01", "Pembelian laptop baru"),
    (2, "Masuk", 3, "2026-10-02", "Penambahan komputer"),
    (3, "Keluar", 1, "2026-10-03", "Digunakan ruang admin"),
    (4, "Masuk", 5, "2026-10-04", "Pembelian meja kantor"),
    (5, "Keluar", 2, "2026-10-05", "Dipindahkan ke ruang dosen"),
    (6, "Masuk", 4, "2026-10-06", "Pembelian router"),
    (7, "Keluar", 3, "2026-10-07", "Digunakan laboratorium"),
    (8, "Masuk", 6, "2026-10-08", "Penambahan mouse"),
    (9, "Keluar", 1, "2026-10-09", "Digunakan ruang kelas"),
    (10, "Masuk", 10, "2026-10-10", "Pembelian kabel HDMI"),
]

DEMO_USERS = [
    ("Administrator", "admin", os.getenv("ADMIN_INITIAL_PASSWORD", "Admin123!"), "admin"),
    ("Pengguna Demo 01", "user01", "User123!", "user"),
    ("Pengguna Demo 02", "user02", "User123!", "user"),
    ("Pengguna Demo 03", "user03", "User123!", "user"),
    ("Pengguna Demo 04", "user04", "User123!", "user"),
    ("Pengguna Demo 05", "user05", "User123!", "user"),
    ("Pengguna Demo 06", "user06", "User123!", "user"),
    ("Pengguna Demo 07", "user07", "User123!", "user"),
    ("Pengguna Demo 08", "user08", "User123!", "user"),
    ("Pengguna Demo 09", "user09", "User123!", "user"),
]

with app.app_context():
    # Membuat tabel yang belum ada, tanpa menghapus tabel/data yang sudah ada.
    db.create_all()

    if Kategori.query.count() == 0:
        db.session.add_all([
            Kategori(id_kategori=id_, nama_kategori=nama)
            for id_, nama in KATEGORI
        ])
        db.session.flush()

    if Lokasi.query.count() == 0:
        db.session.add_all([
            Lokasi(id_lokasi=id_, nama_lokasi=nama, keterangan=ket)
            for id_, nama, ket in LOKASI
        ])
        db.session.flush()

    if Barang.query.count() == 0:
        db.session.add_all([
            Barang(
                id_barang=id_, kode_barang=kode, nama_barang=nama,
                id_kategori=id_kategori, id_lokasi=id_lokasi,
                stok=stok, kondisi=kondisi
            )
            for id_, kode, nama, id_kategori, id_lokasi, stok, kondisi in BARANG
        ])
        db.session.flush()

    if Transaksi.query.count() == 0:
        db.session.add_all([
            Transaksi(
                id_transaksi=i, id_barang=i, jenis_transaksi=jenis,
                jumlah=jumlah, tanggal=date.fromisoformat(tanggal),
                keterangan=keterangan
            )
            for i, jenis, jumlah, tanggal, keterangan in TRANSAKSI
        ])

    akun_baru = 0
    for nama, username, password, role in DEMO_USERS:
        if not User.query.filter_by(username=username).first():
            db.session.add(User(
                nama=nama,
                username=username,
                password=generate_password_hash(password),
                role=role,
            ))
            akun_baru += 1

    db.session.commit()
    print("Inisialisasi InventarisKu selesai.")
    print(f"Kategori: {Kategori.query.count()} | Lokasi: {Lokasi.query.count()} | Barang: {Barang.query.count()} | Transaksi: {Transaksi.query.count()}")
    print(f"Akun demo baru dibuat: {akun_baru}")
    print("Ganti password demo sebelum membagikan URL kepada orang lain.")
