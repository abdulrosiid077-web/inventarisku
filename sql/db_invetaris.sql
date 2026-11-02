-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Nov 02, 2026 at 04:43 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.0.30

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `db_invetaris`
--

-- --------------------------------------------------------

--
-- Table structure for table `barang`
--

CREATE TABLE `barang` (
  `id_barang` int(11) NOT NULL,
  `kode_barang` varchar(20) NOT NULL,
  `nama_barang` varchar(100) NOT NULL,
  `id_kategori` int(11) DEFAULT NULL,
  `id_lokasi` int(11) DEFAULT NULL,
  `stok` int(11) DEFAULT 0,
  `kondisi` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `barang`
--

INSERT INTO `barang` (`id_barang`, `kode_barang`, `nama_barang`, `id_kategori`, `id_lokasi`, `stok`, `kondisi`) VALUES
(1, 'BRG001', 'Laptop Asus', 2, 2, 10, 'Baik'),
(2, 'BRG002', 'Komputer Lenovo', 2, 2, 8, 'Baik'),
(3, 'BRG003', 'Printer Epson', 1, 1, 5, 'Baik'),
(4, 'BRG004', 'Meja Kantor', 4, 1, 12, 'Baik'),
(5, 'BRG005', 'Kursi Kantor', 4, 1, 20, 'Baik'),
(6, 'BRG006', 'Router TP-Link', 5, 10, 7, 'Baik'),
(7, 'BRG007', 'Keyboard Logitech', 2, 2, 15, 'Baik'),
(8, 'BRG008', 'Mouse Wireless', 2, 2, 18, 'Baik'),
(9, 'BRG009', 'Proyektor Epson', 9, 4, 4, 'Baik'),
(10, 'BRG010', 'Kabel HDMI', 5, 3, 25, 'Baik');

-- --------------------------------------------------------

--
-- Table structure for table `kategori`
--

CREATE TABLE `kategori` (
  `id_kategori` int(11) NOT NULL,
  `nama_kategori` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `kategori`
--

INSERT INTO `kategori` (`id_kategori`, `nama_kategori`) VALUES
(1, 'Elektronik'),
(2, 'Komputer'),
(3, 'Peralatan Kantor'),
(4, 'Furniture'),
(5, 'Peralatan Jaringan'),
(6, 'Alat Tulis'),
(7, 'Peralatan Kebersihan'),
(8, 'Peralatan Laboratorium'),
(9, 'Peralatan Presentasi'),
(10, 'Peralatan Listrik');

-- --------------------------------------------------------

--
-- Table structure for table `lokasi`
--

CREATE TABLE `lokasi` (
  `id_lokasi` int(11) NOT NULL,
  `nama_lokasi` varchar(100) NOT NULL,
  `keterangan` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `lokasi`
--

INSERT INTO `lokasi` (`id_lokasi`, `nama_lokasi`, `keterangan`) VALUES
(1, 'Ruang Admin', 'Tempat penyimpanan barang administrasi'),
(2, 'Ruang IT', 'Tempat penyimpanan komputer dan laptop'),
(3, 'Gudang Utama', 'Gudang penyimpanan barang utama'),
(4, 'Ruang Kelas 1', 'Tempat peralatan belajar'),
(5, 'Ruang Kelas 2', 'Tempat peralatan belajar'),
(6, 'Laboratorium', 'Tempat peralatan praktikum'),
(7, 'Ruang Dosen', 'Tempat perlengkapan dosen'),
(8, 'Ruang Rapat', 'Tempat peralatan rapat'),
(9, 'Perpustakaan', 'Tempat perlengkapan perpustakaan'),
(10, 'Ruang Server', 'Tempat perangkat jaringan dan server');

-- --------------------------------------------------------

--
-- Table structure for table `transaksi`
--

CREATE TABLE `transaksi` (
  `id_transaksi` int(11) NOT NULL,
  `id_barang` int(11) DEFAULT NULL,
  `jenis_transaksi` varchar(20) DEFAULT NULL,
  `jumlah` int(11) NOT NULL,
  `tanggal` date DEFAULT NULL,
  `keterangan` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `transaksi`
--

INSERT INTO `transaksi` (`id_transaksi`, `id_barang`, `jenis_transaksi`, `jumlah`, `tanggal`, `keterangan`) VALUES
(1, 1, 'Masuk', 5, '2026-10-01', 'Pembelian laptop baru'),
(2, 2, 'Masuk', 3, '2026-10-02', 'Penambahan komputer'),
(3, 3, 'Keluar', 1, '2026-10-03', 'Digunakan ruang admin'),
(4, 4, 'Masuk', 5, '2026-10-04', 'Pembelian meja kantor'),
(5, 5, 'Keluar', 2, '2026-10-05', 'Dipindahkan ke ruang dosen'),
(6, 6, 'Masuk', 4, '2026-10-06', 'Pembelian router'),
(7, 7, 'Keluar', 3, '2026-10-07', 'Digunakan laboratorium'),
(8, 8, 'Masuk', 6, '2026-10-08', 'Penambahan mouse'),
(9, 9, 'Keluar', 1, '2026-10-09', 'Digunakan ruang kelas'),
(10, 10, 'Masuk', 10, '2026-10-10', 'Pembelian kabel HDMI');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `barang`
--
ALTER TABLE `barang`
  ADD PRIMARY KEY (`id_barang`),
  ADD UNIQUE KEY `kode_barang` (`kode_barang`),
  ADD KEY `id_kategori` (`id_kategori`),
  ADD KEY `id_lokasi` (`id_lokasi`);

--
-- Indexes for table `kategori`
--
ALTER TABLE `kategori`
  ADD PRIMARY KEY (`id_kategori`);

--
-- Indexes for table `lokasi`
--
ALTER TABLE `lokasi`
  ADD PRIMARY KEY (`id_lokasi`);

--
-- Indexes for table `transaksi`
--
ALTER TABLE `transaksi`
  ADD PRIMARY KEY (`id_transaksi`),
  ADD KEY `id_barang` (`id_barang`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `barang`
--
ALTER TABLE `barang`
  MODIFY `id_barang` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `kategori`
--
ALTER TABLE `kategori`
  MODIFY `id_kategori` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `lokasi`
--
ALTER TABLE `lokasi`
  MODIFY `id_lokasi` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `transaksi`
--
ALTER TABLE `transaksi`
  MODIFY `id_transaksi` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `barang`
--
ALTER TABLE `barang`
  ADD CONSTRAINT `barang_ibfk_1` FOREIGN KEY (`id_kategori`) REFERENCES `kategori` (`id_kategori`),
  ADD CONSTRAINT `barang_ibfk_2` FOREIGN KEY (`id_lokasi`) REFERENCES `lokasi` (`id_lokasi`);

--
-- Constraints for table `transaksi`
--
ALTER TABLE `transaksi`
  ADD CONSTRAINT `transaksi_ibfk_1` FOREIGN KEY (`id_barang`) REFERENCES `barang` (`id_barang`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
