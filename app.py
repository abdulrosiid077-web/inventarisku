import csv
import io
import os
from datetime import date, datetime
from functools import wraps

from dotenv import load_dotenv
from flask import (
    Flask, Response, abort, flash, make_response, redirect,
    render_template, request, url_for
)
from flask_login import (
    LoginManager, UserMixin, current_user, login_required,
    login_user, logout_user
)
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import URL, func, or_
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix

load_dotenv()

app = Flask(__name__)
# Hormati header HTTPS dari reverse proxy pada hosting.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-only-change-this-key")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.getenv("COOKIE_SECURE", "false").lower() == "true"

# Bisa memakai DATABASE_URL di hosting, atau variabel DB_* untuk MySQL lokal.
_database_url = os.getenv("DATABASE_URL", "").strip()
if _database_url:
    # Beberapa hosting memberikan postgres:// atau mysql://; sesuaikan driver MySQL.
    if _database_url.startswith("mysql://"):
        _database_url = _database_url.replace("mysql://", "mysql+pymysql://", 1)
    elif _database_url.startswith("postgres://"):
        _database_url = _database_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = _database_url
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = URL.create(
        drivername="mysql+pymysql",
        username=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=os.getenv("DB_NAME", "db_invetaris"),
        query={"charset": "utf8mb4"},
    )

# Untuk tes/development lokal bisa memakai DATABASE_URL=sqlite:///inventaris.db.
# Sertifikat CA MySQL opsional untuk provider cloud yang mewajibkan TLS.
_db_ssl_ca = os.getenv("DB_SSL_CA", "").strip()
if _db_ssl_ca and os.path.isfile(_db_ssl_ca):
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"connect_args": {"ssl": {"ca": _db_ssl_ca}}}

db = SQLAlchemy(app)
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Silakan login terlebih dahulu."
login_manager.login_message_category = "warning"


# ---------------------------------------------------------------------------
# MODEL DATABASE: menyesuaikan struktur db_invetaris.sql milik pengguna.
# ---------------------------------------------------------------------------
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id_user = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nama = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum("admin", "user"), nullable=False, default="user")
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.current_timestamp())

    def get_id(self):
        return str(self.id_user)


class Kategori(db.Model):
    __tablename__ = "kategori"

    id_kategori = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nama_kategori = db.Column(db.String(100), nullable=False)
    barang = db.relationship("Barang", back_populates="kategori")


class Lokasi(db.Model):
    __tablename__ = "lokasi"

    id_lokasi = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nama_lokasi = db.Column(db.String(100), nullable=False)
    keterangan = db.Column(db.Text)
    barang = db.relationship("Barang", back_populates="lokasi")


class Barang(db.Model):
    __tablename__ = "barang"

    id_barang = db.Column(db.Integer, primary_key=True, autoincrement=True)
    kode_barang = db.Column(db.String(20), nullable=False, unique=True)
    nama_barang = db.Column(db.String(100), nullable=False)
    id_kategori = db.Column(db.Integer, db.ForeignKey("kategori.id_kategori"))
    id_lokasi = db.Column(db.Integer, db.ForeignKey("lokasi.id_lokasi"))
    stok = db.Column(db.Integer, default=0)
    kondisi = db.Column(db.String(50))

    kategori = db.relationship("Kategori", back_populates="barang")
    lokasi = db.relationship("Lokasi", back_populates="barang")
    transaksi = db.relationship("Transaksi", back_populates="barang")


class Transaksi(db.Model):
    __tablename__ = "transaksi"

    id_transaksi = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_barang = db.Column(db.Integer, db.ForeignKey("barang.id_barang"))
    jenis_transaksi = db.Column(db.String(20))
    jumlah = db.Column(db.Integer, nullable=False)
    tanggal = db.Column(db.Date)
    keterangan = db.Column(db.Text)

    barang = db.relationship("Barang", back_populates="transaksi")


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        if current_user.role != "admin":
            flash("Fitur ini hanya dapat diakses oleh Admin.", "danger")
            return redirect(url_for("dashboard"))
        return view(*args, **kwargs)
    return wrapped


def positive_int(value, label="Jumlah"):
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label} harus berupa angka.")
    if number < 0:
        raise ValueError(f"{label} tidak boleh negatif.")
    return number


def parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise ValueError("Tanggal wajib diisi dengan format yang benar.")


def apply_transaction(barang, jenis, jumlah):
    """Terapkan dampak transaksi ke stok. Keluar tidak boleh membuat stok minus."""
    if jenis == "Masuk":
        barang.stok = (barang.stok or 0) + jumlah
    elif jenis == "Keluar":
        if (barang.stok or 0) < jumlah:
            raise ValueError(f"Stok {barang.nama_barang} tidak mencukupi. Stok tersedia: {barang.stok}.")
        barang.stok = (barang.stok or 0) - jumlah
    else:
        raise ValueError("Jenis transaksi harus Masuk atau Keluar.")


def reverse_transaction(barang, jenis, jumlah):
    """Batalkan dampak transaksi lama, misalnya saat transaksi diedit/dihapus."""
    if jenis == "Masuk":
        if (barang.stok or 0) < jumlah:
            raise ValueError("Transaksi tidak dapat dibatalkan karena stok saat ini tidak mencukupi.")
        barang.stok = (barang.stok or 0) - jumlah
    elif jenis == "Keluar":
        barang.stok = (barang.stok or 0) + jumlah


@app.context_processor
def inject_globals():
    return {"tahun_sekarang": date.today().year, "tanggal_hari_ini": date.today().strftime("%d %B %Y")}


@app.route("/")
def index():
    return redirect(url_for("dashboard" if current_user.is_authenticated else "login"))


@app.route("/favicon.ico")
def favicon():
    # No custom favicon yet; return an empty success response instead of a 404.
    return "", 204


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash(f"Selamat datang, {user.nama}!", "success")
            next_url = request.args.get("next", "")
            # Hindari redirect ke alamat eksternal.
            if next_url.startswith("/") and not next_url.startswith("//"):
                return redirect(next_url)
            return redirect(url_for("dashboard"))
        flash("Username atau password tidak sesuai.", "danger")
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Kamu berhasil logout.", "success")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    total_jenis = Barang.query.count()
    total_stok = db.session.query(func.coalesce(func.sum(Barang.stok), 0)).scalar() or 0
    total_kategori = Kategori.query.count()
    total_lokasi = Lokasi.query.count()
    total_masuk = db.session.query(func.coalesce(func.sum(Transaksi.jumlah), 0)).filter_by(jenis_transaksi="Masuk").scalar() or 0
    total_keluar = db.session.query(func.coalesce(func.sum(Transaksi.jumlah), 0)).filter_by(jenis_transaksi="Keluar").scalar() or 0
    stok_rendah = Barang.query.filter(Barang.stok <= 5).order_by(Barang.stok.asc()).limit(6).all()
    transaksi_terbaru = Transaksi.query.order_by(Transaksi.tanggal.desc(), Transaksi.id_transaksi.desc()).limit(6).all()
    month_expr = (func.strftime("%Y-%m", Transaksi.tanggal)
                  if db.engine.dialect.name == "sqlite"
                  else func.date_format(Transaksi.tanggal, "%Y-%m"))
    bulan = db.session.query(
        month_expr.label("bulan"),
        Transaksi.jenis_transaksi,
        func.sum(Transaksi.jumlah).label("total")
    ).group_by("bulan", Transaksi.jenis_transaksi).order_by("bulan").all()
    chart_labels = sorted({row.bulan for row in bulan if row.bulan})[-6:]
    chart_masuk = [int(next((r.total for r in bulan if r.bulan == b and r.jenis_transaksi == "Masuk"), 0) or 0) for b in chart_labels]
    chart_keluar = [int(next((r.total for r in bulan if r.bulan == b and r.jenis_transaksi == "Keluar"), 0) or 0) for b in chart_labels]
    return render_template(
        "dashboard.html", total_jenis=total_jenis, total_stok=total_stok,
        total_kategori=total_kategori, total_lokasi=total_lokasi,
        total_masuk=total_masuk, total_keluar=total_keluar,
        stok_rendah=stok_rendah, transaksi_terbaru=transaksi_terbaru,
        chart_labels=chart_labels, chart_masuk=chart_masuk, chart_keluar=chart_keluar
    )


# ---------------------------------------------------------------------------
# BARANG
# ---------------------------------------------------------------------------
@app.route("/barang")
@login_required
def barang_index():
    q = request.args.get("q", "").strip()
    kategori_id = request.args.get("kategori", "").strip()
    query = Barang.query.join(Kategori, isouter=True).join(Lokasi, isouter=True)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Barang.kode_barang.ilike(like), Barang.nama_barang.ilike(like)))
    if kategori_id.isdigit():
        query = query.filter(Barang.id_kategori == int(kategori_id))
    barang = query.order_by(Barang.id_barang.desc()).all()
    kategori = Kategori.query.order_by(Kategori.nama_kategori).all()
    return render_template("barang/index.html", barang=barang, kategori=kategori, q=q, kategori_id=kategori_id)


@app.route("/barang/tambah", methods=["GET", "POST"])
@login_required
@admin_required
def barang_tambah():
    kategori = Kategori.query.order_by(Kategori.nama_kategori).all()
    lokasi = Lokasi.query.order_by(Lokasi.nama_lokasi).all()
    if request.method == "POST":
        kode = request.form.get("kode_barang", "").strip()
        nama = request.form.get("nama_barang", "").strip()
        try:
            stok = positive_int(request.form.get("stok", "0"), "Stok")
            if not kode or not nama:
                raise ValueError("Kode dan nama barang wajib diisi.")
            if Barang.query.filter_by(kode_barang=kode).first():
                raise ValueError("Kode barang sudah digunakan.")
            item = Barang(
                kode_barang=kode, nama_barang=nama,
                id_kategori=int(request.form["id_kategori"]) if request.form.get("id_kategori") else None,
                id_lokasi=int(request.form["id_lokasi"]) if request.form.get("id_lokasi") else None,
                stok=stok, kondisi=request.form.get("kondisi", "Baik").strip() or "Baik"
            )
            db.session.add(item)
            db.session.commit()
            flash("Barang berhasil ditambahkan.", "success")
            return redirect(url_for("barang_index"))
        except (ValueError, KeyError) as error:
            db.session.rollback()
            flash(str(error), "danger")
    return render_template("barang/form.html", mode="tambah", item=None, kategori=kategori, lokasi=lokasi)


@app.route("/barang/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def barang_edit(item_id):
    item = db.get_or_404(Barang, item_id)
    kategori = Kategori.query.order_by(Kategori.nama_kategori).all()
    lokasi = Lokasi.query.order_by(Lokasi.nama_lokasi).all()
    if request.method == "POST":
        try:
            kode = request.form.get("kode_barang", "").strip()
            nama = request.form.get("nama_barang", "").strip()
            stok = positive_int(request.form.get("stok", "0"), "Stok")
            duplicate = Barang.query.filter(Barang.kode_barang == kode, Barang.id_barang != item_id).first()
            if not kode or not nama:
                raise ValueError("Kode dan nama barang wajib diisi.")
            if duplicate:
                raise ValueError("Kode barang sudah digunakan barang lain.")
            item.kode_barang = kode
            item.nama_barang = nama
            item.id_kategori = int(request.form["id_kategori"]) if request.form.get("id_kategori") else None
            item.id_lokasi = int(request.form["id_lokasi"]) if request.form.get("id_lokasi") else None
            item.stok = stok
            item.kondisi = request.form.get("kondisi", "Baik").strip() or "Baik"
            db.session.commit()
            flash("Data barang berhasil diperbarui.", "success")
            return redirect(url_for("barang_index"))
        except (ValueError, KeyError) as error:
            db.session.rollback()
            flash(str(error), "danger")
    return render_template("barang/form.html", mode="edit", item=item, kategori=kategori, lokasi=lokasi)


@app.route("/barang/<int:item_id>/hapus", methods=["POST"])
@login_required
@admin_required
def barang_hapus(item_id):
    item = db.get_or_404(Barang, item_id)
    if item.transaksi:
        flash("Barang tidak bisa dihapus karena sudah memiliki riwayat transaksi. Hapus/arsipkan transaksi terkait terlebih dahulu.", "danger")
    else:
        db.session.delete(item)
        db.session.commit()
        flash("Barang berhasil dihapus.", "success")
    return redirect(url_for("barang_index"))


# ---------------------------------------------------------------------------
# KATEGORI
# ---------------------------------------------------------------------------
@app.route("/kategori")
@login_required
def kategori_index():
    kategori = Kategori.query.order_by(Kategori.nama_kategori).all()
    return render_template("kategori/index.html", kategori=kategori)


@app.route("/kategori/tambah", methods=["GET", "POST"])
@login_required
@admin_required
def kategori_tambah():
    if request.method == "POST":
        nama = request.form.get("nama_kategori", "").strip()
        if not nama:
            flash("Nama kategori wajib diisi.", "danger")
        elif Kategori.query.filter(func.lower(Kategori.nama_kategori) == nama.lower()).first():
            flash("Nama kategori sudah ada.", "danger")
        else:
            db.session.add(Kategori(nama_kategori=nama))
            db.session.commit()
            flash("Kategori berhasil ditambahkan.", "success")
            return redirect(url_for("kategori_index"))
    return render_template("kategori/form.html", mode="tambah", item=None)


@app.route("/kategori/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def kategori_edit(item_id):
    item = db.get_or_404(Kategori, item_id)
    if request.method == "POST":
        nama = request.form.get("nama_kategori", "").strip()
        duplicate = Kategori.query.filter(func.lower(Kategori.nama_kategori) == nama.lower(), Kategori.id_kategori != item_id).first()
        if not nama:
            flash("Nama kategori wajib diisi.", "danger")
        elif duplicate:
            flash("Nama kategori sudah digunakan.", "danger")
        else:
            item.nama_kategori = nama
            db.session.commit()
            flash("Kategori berhasil diperbarui.", "success")
            return redirect(url_for("kategori_index"))
    return render_template("kategori/form.html", mode="edit", item=item)


@app.route("/kategori/<int:item_id>/hapus", methods=["POST"])
@login_required
@admin_required
def kategori_hapus(item_id):
    item = db.get_or_404(Kategori, item_id)
    if item.barang:
        flash("Kategori masih digunakan oleh barang dan tidak dapat dihapus.", "danger")
    else:
        db.session.delete(item)
        db.session.commit()
        flash("Kategori berhasil dihapus.", "success")
    return redirect(url_for("kategori_index"))


# ---------------------------------------------------------------------------
# LOKASI
# ---------------------------------------------------------------------------
@app.route("/lokasi")
@login_required
def lokasi_index():
    lokasi = Lokasi.query.order_by(Lokasi.nama_lokasi).all()
    return render_template("lokasi/index.html", lokasi=lokasi)


@app.route("/lokasi/tambah", methods=["GET", "POST"])
@login_required
@admin_required
def lokasi_tambah():
    if request.method == "POST":
        nama = request.form.get("nama_lokasi", "").strip()
        keterangan = request.form.get("keterangan", "").strip()
        if not nama:
            flash("Nama lokasi wajib diisi.", "danger")
        elif Lokasi.query.filter(func.lower(Lokasi.nama_lokasi) == nama.lower()).first():
            flash("Nama lokasi sudah ada.", "danger")
        else:
            db.session.add(Lokasi(nama_lokasi=nama, keterangan=keterangan))
            db.session.commit()
            flash("Lokasi berhasil ditambahkan.", "success")
            return redirect(url_for("lokasi_index"))
    return render_template("lokasi/form.html", mode="tambah", item=None)


@app.route("/lokasi/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def lokasi_edit(item_id):
    item = db.get_or_404(Lokasi, item_id)
    if request.method == "POST":
        nama = request.form.get("nama_lokasi", "").strip()
        duplicate = Lokasi.query.filter(func.lower(Lokasi.nama_lokasi) == nama.lower(), Lokasi.id_lokasi != item_id).first()
        if not nama:
            flash("Nama lokasi wajib diisi.", "danger")
        elif duplicate:
            flash("Nama lokasi sudah digunakan.", "danger")
        else:
            item.nama_lokasi = nama
            item.keterangan = request.form.get("keterangan", "").strip()
            db.session.commit()
            flash("Lokasi berhasil diperbarui.", "success")
            return redirect(url_for("lokasi_index"))
    return render_template("lokasi/form.html", mode="edit", item=item)


@app.route("/lokasi/<int:item_id>/hapus", methods=["POST"])
@login_required
@admin_required
def lokasi_hapus(item_id):
    item = db.get_or_404(Lokasi, item_id)
    if item.barang:
        flash("Lokasi masih digunakan oleh barang dan tidak dapat dihapus.", "danger")
    else:
        db.session.delete(item)
        db.session.commit()
        flash("Lokasi berhasil dihapus.", "success")
    return redirect(url_for("lokasi_index"))


# ---------------------------------------------------------------------------
# TRANSAKSI - stok otomatis berubah ketika transaksi dibuat/diedit/dihapus.
# ---------------------------------------------------------------------------
@app.route("/transaksi")
@login_required
def transaksi_index():
    q = request.args.get("q", "").strip()
    jenis = request.args.get("jenis", "").strip()
    query = Transaksi.query.join(Barang)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Barang.nama_barang.ilike(like), Barang.kode_barang.ilike(like)))
    if jenis in ("Masuk", "Keluar"):
        query = query.filter(Transaksi.jenis_transaksi == jenis)
    transaksi = query.order_by(Transaksi.tanggal.desc(), Transaksi.id_transaksi.desc()).all()
    return render_template("transaksi/index.html", transaksi=transaksi, q=q, jenis=jenis)


@app.route("/transaksi/tambah", methods=["GET", "POST"])
@login_required
@admin_required
def transaksi_tambah():
    barang = Barang.query.order_by(Barang.nama_barang).all()
    if request.method == "POST":
        try:
            item = db.get_or_404(Barang, int(request.form.get("id_barang", "0")))
            jenis = request.form.get("jenis_transaksi", "")
            jumlah = positive_int(request.form.get("jumlah", "0"), "Jumlah")
            tanggal = parse_date(request.form.get("tanggal", ""))
            if jumlah <= 0:
                raise ValueError("Jumlah transaksi harus lebih dari nol.")
            apply_transaction(item, jenis, jumlah)
            transaksi = Transaksi(
                barang=item, jenis_transaksi=jenis, jumlah=jumlah,
                tanggal=tanggal, keterangan=request.form.get("keterangan", "").strip()
            )
            db.session.add(transaksi)
            db.session.commit()
            flash("Transaksi berhasil disimpan dan stok sudah diperbarui.", "success")
            return redirect(url_for("transaksi_index"))
        except (ValueError, TypeError) as error:
            db.session.rollback()
            flash(str(error), "danger")
    return render_template("transaksi/form.html", mode="tambah", item=None, barang=barang)


@app.route("/transaksi/<int:transaksi_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def transaksi_edit(transaksi_id):
    item = db.get_or_404(Transaksi, transaksi_id)
    barang = Barang.query.order_by(Barang.nama_barang).all()
    if request.method == "POST":
        try:
            # Kembalikan efek transaksi lama, lalu terapkan transaksi yang baru.
            barang_lama = db.session.get(Barang, item.id_barang)
            reverse_transaction(barang_lama, item.jenis_transaksi, item.jumlah)
            barang_baru = db.get_or_404(Barang, int(request.form.get("id_barang", "0")))
            jenis_baru = request.form.get("jenis_transaksi", "")
            jumlah_baru = positive_int(request.form.get("jumlah", "0"), "Jumlah")
            tanggal_baru = parse_date(request.form.get("tanggal", ""))
            if jumlah_baru <= 0:
                raise ValueError("Jumlah transaksi harus lebih dari nol.")
            apply_transaction(barang_baru, jenis_baru, jumlah_baru)
            item.barang = barang_baru
            item.jenis_transaksi = jenis_baru
            item.jumlah = jumlah_baru
            item.tanggal = tanggal_baru
            item.keterangan = request.form.get("keterangan", "").strip()
            db.session.commit()
            flash("Transaksi diperbarui dan stok disesuaikan.", "success")
            return redirect(url_for("transaksi_index"))
        except (ValueError, TypeError) as error:
            db.session.rollback()
            flash(str(error), "danger")
    return render_template("transaksi/form.html", mode="edit", item=item, barang=barang)


@app.route("/transaksi/<int:transaksi_id>/hapus", methods=["POST"])
@login_required
@admin_required
def transaksi_hapus(transaksi_id):
    item = db.get_or_404(Transaksi, transaksi_id)
    try:
        reverse_transaction(item.barang, item.jenis_transaksi, item.jumlah)
        db.session.delete(item)
        db.session.commit()
        flash("Transaksi dihapus dan stok dikembalikan.", "success")
    except ValueError as error:
        db.session.rollback()
        flash(str(error), "danger")
    return redirect(url_for("transaksi_index"))


# ---------------------------------------------------------------------------
# MANAJEMEN USER (ADMIN) DAN PROFIL
# ---------------------------------------------------------------------------
@app.route("/pengguna")
@login_required
@admin_required
def pengguna_index():
    pengguna = User.query.order_by(User.role, User.nama).all()
    return render_template("pengguna/index.html", pengguna=pengguna)


@app.route("/pengguna/tambah", methods=["GET", "POST"])
@login_required
@admin_required
def pengguna_tambah():
    if request.method == "POST":
        nama = request.form.get("nama", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "user")
        if not nama or not username or not password:
            flash("Nama, username, dan password wajib diisi.", "danger")
        elif len(password) < 8:
            flash("Password minimal 8 karakter.", "danger")
        elif role not in ("admin", "user"):
            flash("Role tidak valid.", "danger")
        elif User.query.filter_by(username=username).first():
            flash("Username sudah digunakan.", "danger")
        else:
            db.session.add(User(nama=nama, username=username, password=generate_password_hash(password), role=role))
            db.session.commit()
            flash("Pengguna berhasil dibuat.", "success")
            return redirect(url_for("pengguna_index"))
    return render_template("pengguna/form.html", mode="tambah", item=None)


@app.route("/pengguna/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def pengguna_edit(user_id):
    item = db.get_or_404(User, user_id)
    if request.method == "POST":
        nama = request.form.get("nama", "").strip()
        username = request.form.get("username", "").strip()
        role = request.form.get("role", "user")
        password = request.form.get("password", "")
        duplicate = User.query.filter(User.username == username, User.id_user != user_id).first()
        if not nama or not username:
            flash("Nama dan username wajib diisi.", "danger")
        elif duplicate:
            flash("Username sudah digunakan.", "danger")
        elif role not in ("admin", "user"):
            flash("Role tidak valid.", "danger")
        elif password and len(password) < 8:
            flash("Password baru minimal 8 karakter.", "danger")
        else:
            item.nama, item.username, item.role = nama, username, role
            if password:
                item.password = generate_password_hash(password)
            db.session.commit()
            flash("Pengguna berhasil diperbarui.", "success")
            return redirect(url_for("pengguna_index"))
    return render_template("pengguna/form.html", mode="edit", item=item)


@app.route("/pengguna/<int:user_id>/hapus", methods=["POST"])
@login_required
@admin_required
def pengguna_hapus(user_id):
    item = db.get_or_404(User, user_id)
    if item.id_user == current_user.id_user:
        flash("Akun yang sedang digunakan tidak dapat dihapus.", "danger")
    elif item.role == "admin" and User.query.filter_by(role="admin").count() <= 1:
        flash("Minimal harus ada satu akun Admin.", "danger")
    else:
        db.session.delete(item)
        db.session.commit()
        flash("Pengguna berhasil dihapus.", "success")
    return redirect(url_for("pengguna_index"))


@app.route("/profil", methods=["GET", "POST"])
@login_required
def profil():
    if request.method == "POST":
        password_lama = request.form.get("password_lama", "")
        password_baru = request.form.get("password_baru", "")
        konfirmasi = request.form.get("konfirmasi", "")
        if not check_password_hash(current_user.password, password_lama):
            flash("Password saat ini salah.", "danger")
        elif len(password_baru) < 8:
            flash("Password baru minimal 8 karakter.", "danger")
        elif password_baru != konfirmasi:
            flash("Konfirmasi password tidak sama.", "danger")
        else:
            current_user.password = generate_password_hash(password_baru)
            db.session.commit()
            flash("Password berhasil diganti.", "success")
            return redirect(url_for("profil"))
    return render_template("profil.html")


# ---------------------------------------------------------------------------
# LAPORAN: 3 jenis laporan, dapat dicetak atau diekspor CSV.
# ---------------------------------------------------------------------------
def get_report_data(jenis):
    if jenis == "transaksi":
        rows = Transaksi.query.order_by(Transaksi.tanggal.desc(), Transaksi.id_transaksi.desc()).all()
        return rows
    if jenis == "stok":
        return Barang.query.order_by(Barang.stok.asc(), Barang.nama_barang).all()
    return Barang.query.order_by(Barang.nama_barang).all()


@app.route("/laporan")
@login_required
def laporan_index():
    jenis = request.args.get("jenis", "inventaris")
    if jenis not in ("inventaris", "stok", "transaksi"):
        jenis = "inventaris"
    rows = get_report_data(jenis)
    return render_template("laporan/index.html", jenis=jenis, rows=rows)


@app.route("/laporan/cetak")
@login_required
def laporan_cetak():
    jenis = request.args.get("jenis", "inventaris")
    if jenis not in ("inventaris", "stok", "transaksi"):
        jenis = "inventaris"
    return render_template("laporan/cetak.html", jenis=jenis, rows=get_report_data(jenis))


@app.route("/laporan/export")
@login_required
def laporan_export():
    jenis = request.args.get("jenis", "inventaris")
    if jenis not in ("inventaris", "stok", "transaksi"):
        jenis = "inventaris"
    rows = get_report_data(jenis)
    output = io.StringIO()
    writer = csv.writer(output)
    if jenis == "transaksi":
        writer.writerow(["ID Transaksi", "Tanggal", "Kode Barang", "Nama Barang", "Jenis", "Jumlah", "Keterangan"])
        for row in rows:
            writer.writerow([row.id_transaksi, row.tanggal, row.barang.kode_barang if row.barang else "", row.barang.nama_barang if row.barang else "", row.jenis_transaksi, row.jumlah, row.keterangan or ""])
    else:
        writer.writerow(["ID Barang", "Kode Barang", "Nama Barang", "Kategori", "Lokasi", "Stok", "Kondisi"])
        for row in rows:
            writer.writerow([row.id_barang, row.kode_barang, row.nama_barang, row.kategori.nama_kategori if row.kategori else "-", row.lokasi.nama_lokasi if row.lokasi else "-", row.stok, row.kondisi or "-"])
    response = make_response("\ufeff" + output.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = f"attachment; filename=laporan_{jenis}_{date.today().isoformat()}.csv"
    return response


@app.errorhandler(404)
def not_found(_error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(_error):
    db.session.rollback()
    return render_template("errors/500.html"), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG", "true").lower() == "true")
