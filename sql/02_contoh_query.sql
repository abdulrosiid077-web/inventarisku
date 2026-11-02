USE db_invetaris;

-- 1. Menampilkan barang lengkap dengan kategori dan lokasi.
SELECT b.kode_barang, b.nama_barang, k.nama_kategori, l.nama_lokasi,
       b.stok, b.kondisi
FROM barang AS b
LEFT JOIN kategori AS k ON b.id_kategori = k.id_kategori
LEFT JOIN lokasi AS l ON b.id_lokasi = l.id_lokasi
ORDER BY b.nama_barang ASC;

-- 2. Mencari barang berdasarkan nama atau kode.
SELECT *
FROM barang
WHERE nama_barang LIKE '%laptop%'
   OR kode_barang LIKE '%BRG001%';

-- 3. Mengurutkan stok dari paling sedikit ke paling banyak.
SELECT kode_barang, nama_barang, stok
FROM barang
ORDER BY stok ASC, nama_barang ASC;

-- 4. Menampilkan barang pada kategori tertentu.
SELECT b.kode_barang, b.nama_barang, k.nama_kategori, b.stok
FROM barang AS b
INNER JOIN kategori AS k ON b.id_kategori = k.id_kategori
WHERE k.nama_kategori = 'Komputer'
ORDER BY b.nama_barang;

-- 5. Menampilkan riwayat transaksi beserta nama barang.
SELECT t.id_transaksi, t.tanggal, b.kode_barang, b.nama_barang,
       t.jenis_transaksi, t.jumlah, t.keterangan
FROM transaksi AS t
LEFT JOIN barang AS b ON t.id_barang = b.id_barang
ORDER BY t.tanggal DESC, t.id_transaksi DESC;

-- 6. Menghitung total stok untuk setiap kategori.
SELECT k.nama_kategori, COALESCE(SUM(b.stok), 0) AS total_stok
FROM kategori AS k
LEFT JOIN barang AS b ON k.id_kategori = b.id_kategori
GROUP BY k.id_kategori, k.nama_kategori
ORDER BY total_stok DESC;
