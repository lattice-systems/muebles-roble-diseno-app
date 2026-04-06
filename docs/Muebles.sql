-- MySQL dump 10.13  Distrib 8.0.45, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: furniture_store_db
-- ------------------------------------------------------
-- Server version	9.6.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
SET @MYSQLDUMP_TEMP_LOG_BIN = @@SESSION.SQL_LOG_BIN;
SET @@SESSION.SQL_LOG_BIN= 0;

--
-- GTID state at the beginning of the backup 
--

SET @@GLOBAL.GTID_PURGED=/*!80000 '+'*/ '15fe161e-fa5e-11f0-b151-08bfb86e099c:1-1581';

--
-- Table structure for table `furniture_types`
--

DROP TABLE IF EXISTS `furniture_types`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `furniture_types` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(100) NOT NULL,
  `status` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `subtitle` varchar(255) DEFAULT NULL,
  `image_url` varchar(500) DEFAULT NULL,
  `slug` varchar(120) DEFAULT NULL,
  `deactivated_at` datetime DEFAULT NULL,
  `created_by` int DEFAULT NULL,
  `updated_by` int DEFAULT NULL,
  `deactivated_by` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`title`),
  UNIQUE KEY `ix_furniture_types_slug` (`slug`),
  KEY `created_by` (`created_by`),
  KEY `updated_by` (`updated_by`),
  KEY `deactivated_by` (`deactivated_by`),
  CONSTRAINT `furniture_types_ibfk_1` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`),
  CONSTRAINT `furniture_types_ibfk_2` FOREIGN KEY (`updated_by`) REFERENCES `users` (`id`),
  CONSTRAINT `furniture_types_ibfk_3` FOREIGN KEY (`deactivated_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `furniture_types`
--

LOCK TABLES `furniture_types` WRITE;
/*!40000 ALTER TABLE `furniture_types` DISABLE KEYS */;
INSERT INTO `furniture_types` VALUES (1,'Salas',1,'2026-04-05 23:51:57','2026-04-06 00:06:53','Sofas, loveseats, sillones y ottomanes','https://res.cloudinary.com/dv26xoo6n/image/upload/v1775455612/furniture_types/fnvecygfqpm0rpyqn6rx.jpg','salas',NULL,NULL,1,NULL),(2,'Comedores',1,'2026-04-05 23:51:57','2026-04-06 00:46:52','Mesas de comedor, sillas, bancos y vitrinas','https://res.cloudinary.com/dv26xoo6n/image/upload/v1775458010/furniture_types/ouqralxg3gka1vgoxfq2.jpg','comedores',NULL,NULL,1,NULL),(3,'Recamaras',1,'2026-04-05 23:51:57','2026-04-06 11:23:46','Camas, buros, comodas y cabeceras','https://res.cloudinary.com/dv26xoo6n/image/upload/v1775496224/furniture_types/rsnhg0laxdefmgqcetfc.jpg','recamaras',NULL,NULL,1,NULL),(4,'Closets y almacenamiento',1,'2026-04-05 23:51:57','2026-04-06 11:46:19','Closets, roperos y organizadores','https://res.cloudinary.com/dv26xoo6n/image/upload/v1775497577/furniture_types/tnuyy180ihuilnokvekd.jpg','closets-y-almacenamiento',NULL,NULL,1,NULL),(5,'Escritorios y oficina',1,'2026-04-05 23:51:57','2026-04-06 11:52:17','Escritorios, credenzas y muebles para home office','https://res.cloudinary.com/dv26xoo6n/image/upload/v1775497934/furniture_types/aw7rypycaeo6fmtp290i.jpg','escritorios-y-oficina',NULL,NULL,1,NULL),(6,'Muebles para TV',1,'2026-04-05 23:51:57','2026-04-06 11:53:15','Centros de entretenimiento y consolas multimedia','https://res.cloudinary.com/dv26xoo6n/image/upload/v1775497993/furniture_types/cr82qzc2ujersa886ter.jpg','muebles-para-tv',NULL,NULL,1,NULL),(7,'Mesas',1,'2026-04-05 23:51:57','2026-04-06 11:59:25','Mesas de centro, laterales, auxiliares y recibidor','https://res.cloudinary.com/dv26xoo6n/image/upload/v1775498363/furniture_types/wpwoi4c898exi0iovggo.jpg','mesas',NULL,NULL,1,NULL),(8,'Estanterias y libreros',1,'2026-04-05 23:51:57','2026-04-06 12:13:09','Libreros, estantes, repisas y modulares','https://res.cloudinary.com/dv26xoo6n/image/upload/v1775499187/furniture_types/rzn5lp82hzv0iqhg77s0.jpg','estanterias-y-libreros',NULL,NULL,1,NULL),(9,'Cocina',1,'2026-04-05 23:51:57','2026-04-06 12:13:55','Alacenas, islas y gabinetes','https://res.cloudinary.com/dv26xoo6n/image/upload/v1775499233/furniture_types/rdflrqcsbcydjt7kanzc.jpg','cocina',NULL,NULL,1,NULL),(10,'Muebles infantiles',1,'2026-04-05 23:51:57','2026-04-06 12:23:06','Camas, escritorios y organizadores para ninos','https://res.cloudinary.com/dv26xoo6n/image/upload/v1775499784/furniture_types/er3lzioxzajmuz229d9x.jpg','muebles-infantiles',NULL,NULL,1,NULL),(11,'Muebles decorativos',1,'2026-04-05 23:51:57','2026-04-06 12:29:20','Consolas, biombos y bancos decorativos','https://res.cloudinary.com/dv26xoo6n/image/upload/v1775500157/furniture_types/kuswchaxjcb9qybe67kc.jpg','muebles-decorativos',NULL,NULL,1,NULL),(12,'Muebles personalizados',1,'2026-04-05 23:51:57','2026-04-06 12:35:01','Diseno a medida y proyectos especiales bajo pedido','https://res.cloudinary.com/dv26xoo6n/image/upload/v1775500499/furniture_types/yst2uo1nbpipfrvioijs.jpg','muebles-personalizados',NULL,NULL,1,NULL),(13,'Muebles de jardin',1,'2026-04-05 23:51:57','2026-04-06 12:35:57','Salas, comedores y descanso para exterior','https://res.cloudinary.com/dv26xoo6n/image/upload/v1775500555/furniture_types/s067dw7s6gr5xuyrubpg.jpg','muebles-de-jardin',NULL,NULL,1,NULL);
/*!40000 ALTER TABLE `furniture_types` ENABLE KEYS */;
UNLOCK TABLES;
SET @@SESSION.SQL_LOG_BIN = @MYSQLDUMP_TEMP_LOG_BIN;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-04-06 12:37:42
