-- phpMyAdmin SQL Dump
-- version 5.1.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1:3306
-- Generation Time: Aug 07, 2024 at 04:01 AM
-- Server version: 5.7.36
-- PHP Version: 7.4.26

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `mini_project_11`
--

-- --------------------------------------------------------

--
-- Table structure for table `mini_table_11`
--

DROP TABLE IF EXISTS `mini_table_11`;
CREATE TABLE IF NOT EXISTS `mini_table_11` (
  `date` varchar(11) NOT NULL,
  `red` int(4) NOT NULL,
  `blue` int(4) NOT NULL,
  `green` int(4) NOT NULL,
  `orange` int(4) NOT NULL,
  `yellow` int(4) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Dumping data for table `mini_table_11`
--

INSERT INTO `mini_table_11` (`date`, `red`, `blue`, `green`, `orange`, `yellow`) VALUES
('', 5, 5, 4, 5, 6),
('2024-07-31', 3, 5, 7, 8, 2),
('2024-08-07', 9, 8, 7, 6, 3);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
