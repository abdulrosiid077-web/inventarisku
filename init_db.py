"""Buat tabel users yang belum ada dan seed 10 akun demo.
Jalankan SETELAH database db_invetaris.sql diimpor ke MySQL.
"""
from app import app, db, User
from werkzeug.security import generate_password_hash

DEMO_USERS = [
    ("Administrator", "admin", "Admin123!", "admin"),
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
    db.create_all()
    created = 0
    for nama, username, password, role in DEMO_USERS:
        if not User.query.filter_by(username=username).first():
            db.session.add(User(
                nama=nama,
                username=username,
                password=generate_password_hash(password),
                role=role,
            ))
            created += 1
    db.session.commit()
    print(f"Selesai. {created} akun baru dibuat; tabel users siap digunakan.")
    print("Admin demo: username admin | password Admin123!")
    print("User demo: username user01 s.d. user09 | password User123!")
    print("Ganti semua password demo sebelum aplikasi dipublikasikan.")
