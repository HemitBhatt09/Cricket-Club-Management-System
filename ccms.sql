-- MySQL dump 10.13  Distrib 8.0.45, for Win64 (x86_64)
--
-- Host: localhost    Database: new_backup
-- ------------------------------------------------------
-- Server version	8.0.45

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

--
-- Table structure for table `ball_by_ball`
--

DROP TABLE IF EXISTS `ball_by_ball`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ball_by_ball` (
  `ball_id` int NOT NULL AUTO_INCREMENT,
  `match_id` int DEFAULT NULL,
  `innings` int DEFAULT NULL,
  `over_number` int DEFAULT NULL,
  `ball_number` int DEFAULT NULL,
  `batting_team_id` int DEFAULT NULL,
  `bowling_team_id` int DEFAULT NULL,
  `striker_id` int DEFAULT NULL,
  `non_striker_id` int DEFAULT NULL,
  `bowler_id` int DEFAULT NULL,
  `runs_scored` int DEFAULT '0',
  `extra_type` enum('WIDE','NO_BALL','BYE','LEG_BYE') DEFAULT NULL,
  `extra_runs` int DEFAULT '0',
  `is_wicket` tinyint(1) DEFAULT '0',
  `wicket_type` enum('BOWLED','CAUGHT','RUNOUT','STUMPED','OTHER') DEFAULT NULL,
  `fielder_id` int DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`ball_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ball_by_ball`
--

LOCK TABLES `ball_by_ball` WRITE;
/*!40000 ALTER TABLE `ball_by_ball` DISABLE KEYS */;
/*!40000 ALTER TABLE `ball_by_ball` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `current_match_state`
--

DROP TABLE IF EXISTS `current_match_state`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `current_match_state` (
  `match_id` int NOT NULL,
  `innings` int DEFAULT NULL,
  `striker_id` int DEFAULT NULL,
  `non_striker_id` int DEFAULT NULL,
  `bowler_id` int DEFAULT NULL,
  `last_bowler_id` int DEFAULT NULL,
  `total_runs` int DEFAULT '0',
  `total_wickets` int DEFAULT '0',
  `current_over` int DEFAULT '0',
  `current_ball` int DEFAULT '0',
  PRIMARY KEY (`match_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `current_match_state`
--

LOCK TABLES `current_match_state` WRITE;
/*!40000 ALTER TABLE `current_match_state` DISABLE KEYS */;
/*!40000 ALTER TABLE `current_match_state` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `dismissed_players`
--

DROP TABLE IF EXISTS `dismissed_players`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dismissed_players` (
  `id` int NOT NULL AUTO_INCREMENT,
  `match_id` int DEFAULT NULL,
  `player_id` int DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=102 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dismissed_players`
--

LOCK TABLES `dismissed_players` WRITE;
/*!40000 ALTER TABLE `dismissed_players` DISABLE KEYS */;
INSERT INTO `dismissed_players` VALUES (69,97,209),(70,97,198),(71,98,228),(72,98,227),(73,98,10),(74,99,9),(75,99,201),(76,101,208),(77,101,10),(78,101,197),(79,103,200),(80,105,208),(81,106,13),(82,106,197),(83,106,200),(84,106,198),(85,122,227),(86,108,13),(87,108,13),(88,108,213),(89,109,213),(90,109,216),(91,125,200),(92,126,9),(93,126,4),(94,127,222),(95,127,219),(96,127,4),(97,127,7),(98,127,9),(99,127,10),(100,127,11),(101,128,206);
/*!40000 ALTER TABLE `dismissed_players` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `match_players`
--

DROP TABLE IF EXISTS `match_players`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `match_players` (
  `id` int NOT NULL AUTO_INCREMENT,
  `match_id` int DEFAULT NULL,
  `team_id` int DEFAULT NULL,
  `user_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `match_id` (`match_id`),
  KEY `team_id` (`team_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `match_players_ibfk_1` FOREIGN KEY (`match_id`) REFERENCES `matches` (`match_id`),
  CONSTRAINT `match_players_ibfk_2` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`),
  CONSTRAINT `match_players_ibfk_3` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `match_players`
--

LOCK TABLES `match_players` WRITE;
/*!40000 ALTER TABLE `match_players` DISABLE KEYS */;
/*!40000 ALTER TABLE `match_players` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `matches`
--

DROP TABLE IF EXISTS `matches`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `matches` (
  `match_id` int NOT NULL AUTO_INCREMENT,
  `team1_id` int DEFAULT NULL,
  `team2_id` int DEFAULT NULL,
  `match_date` datetime DEFAULT NULL,
  `created_by` int NOT NULL,
  `tournament_id` int DEFAULT NULL,
  `match_type` varchar(10) DEFAULT NULL,
  `is_finalized` tinyint(1) DEFAULT '0',
  `team1_score` int DEFAULT '0',
  `team2_score` int DEFAULT '0',
  `team1_extras` int DEFAULT '0',
  `team2_extras` int DEFAULT '0',
  `is_completed` tinyint(1) DEFAULT '0',
  `team1_wickets` int DEFAULT '0',
  `team2_wickets` int DEFAULT '0',
  `team1_overs` float DEFAULT '0',
  `team2_overs` float DEFAULT '0',
  `team1_summary_done` tinyint(1) DEFAULT '0',
  `team2_summary_done` tinyint(1) DEFAULT '0',
  `toss_winner_id` int DEFAULT NULL,
  `toss_decision` enum('BAT','BOWL') DEFAULT NULL,
  `total_overs` int DEFAULT NULL,
  `current_innings` int DEFAULT '1',
  `is_started` tinyint(1) DEFAULT '0',
  `winner` varchar(100) DEFAULT NULL,
  `stage` varchar(20) DEFAULT 'LEAGUE',
  `man_of_the_match` int DEFAULT NULL,
  PRIMARY KEY (`match_id`),
  KEY `team1_id` (`team1_id`),
  KEY `team2_id` (`team2_id`),
  KEY `created_by` (`created_by`),
  KEY `fk_tournament` (`tournament_id`),
  CONSTRAINT `fk_tournament` FOREIGN KEY (`tournament_id`) REFERENCES `tournaments` (`tournament_id`) ON DELETE SET NULL,
  CONSTRAINT `matches_ibfk_1` FOREIGN KEY (`team1_id`) REFERENCES `teams` (`team_id`),
  CONSTRAINT `matches_ibfk_2` FOREIGN KEY (`team2_id`) REFERENCES `teams` (`team_id`),
  CONSTRAINT `matches_ibfk_3` FOREIGN KEY (`created_by`) REFERENCES `users` (`user_id`),
  CONSTRAINT `matches_ibfk_4` FOREIGN KEY (`tournament_id`) REFERENCES `tournaments` (`tournament_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `matches`
--

LOCK TABLES `matches` WRITE;
/*!40000 ALTER TABLE `matches` DISABLE KEYS */;
/*!40000 ALTER TABLE `matches` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `player_performance`
--

DROP TABLE IF EXISTS `player_performance`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `player_performance` (
  `id` int NOT NULL AUTO_INCREMENT,
  `match_id` int DEFAULT NULL,
  `team_id` int DEFAULT NULL,
  `user_id` int DEFAULT NULL,
  `runs` int DEFAULT '0',
  `balls` int DEFAULT '0',
  `overs` float DEFAULT '0',
  `runs_conceded` int DEFAULT '0',
  `wickets` int DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `match_id` (`match_id`,`team_id`,`user_id`),
  UNIQUE KEY `match_id_2` (`match_id`,`team_id`,`user_id`),
  KEY `team_id` (`team_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `player_performance_ibfk_1` FOREIGN KEY (`match_id`) REFERENCES `matches` (`match_id`),
  CONSTRAINT `player_performance_ibfk_2` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`),
  CONSTRAINT `player_performance_ibfk_3` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=103 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `player_performance`
--

LOCK TABLES `player_performance` WRITE;
/*!40000 ALTER TABLE `player_performance` DISABLE KEYS */;
/*!40000 ALTER TABLE `player_performance` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `points_table`
--

DROP TABLE IF EXISTS `points_table`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `points_table` (
  `id` int NOT NULL AUTO_INCREMENT,
  `tournament_id` int DEFAULT NULL,
  `team_id` int DEFAULT NULL,
  `matches_played` int DEFAULT '0',
  `wins` int DEFAULT '0',
  `losses` int DEFAULT '0',
  `points` int DEFAULT '0',
  `runs_scored` int DEFAULT '0',
  `overs_faced` float DEFAULT '0',
  `runs_conceded` int DEFAULT '0',
  `overs_bowled` float DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `tournament_id` (`tournament_id`,`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `points_table`
--

LOCK TABLES `points_table` WRITE;
/*!40000 ALTER TABLE `points_table` DISABLE KEYS */;
/*!40000 ALTER TABLE `points_table` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `team_members`
--

DROP TABLE IF EXISTS `team_members`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `team_members` (
  `team_id` int NOT NULL,
  `user_id` int NOT NULL,
  `is_captain` tinyint(1) DEFAULT '0',
  `is_vice_captain` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`team_id`,`user_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `team_members_ibfk_1` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`),
  CONSTRAINT `team_members_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `team_members`
--

LOCK TABLES `team_members` WRITE;
/*!40000 ALTER TABLE `team_members` DISABLE KEYS */;
INSERT INTO `team_members` VALUES (3,4,1,0),(3,7,0,0),(3,8,0,0),(3,9,0,0),(3,10,0,0),(3,11,0,0),(3,12,0,0),(3,13,0,0),(3,14,0,0),(3,15,0,0),(3,16,0,0),(8,197,1,0),(8,198,0,0),(8,200,0,0),(8,201,0,0),(8,203,0,0),(8,206,0,0),(8,208,0,0),(8,209,0,0),(8,210,0,0),(8,211,0,0),(8,212,0,0),(9,213,1,0),(9,215,0,0),(9,216,0,0),(9,218,0,0),(9,219,0,0),(9,221,0,0),(9,222,0,0),(9,224,0,0),(9,225,0,0),(9,226,0,0),(9,227,0,0),(10,227,1,0),(10,228,0,0),(10,229,0,0),(10,230,0,0),(10,231,0,0),(10,232,0,0),(10,233,0,0),(10,234,0,0),(10,235,0,0),(10,236,0,0),(10,237,0,0);
/*!40000 ALTER TABLE `team_members` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `teams`
--

DROP TABLE IF EXISTS `teams`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `teams` (
  `team_id` int NOT NULL AUTO_INCREMENT,
  `team_name` varchar(100) NOT NULL,
  `created_by` int NOT NULL,
  PRIMARY KEY (`team_id`),
  KEY `created_by` (`created_by`),
  CONSTRAINT `teams_ibfk_1` FOREIGN KEY (`created_by`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `teams`
--

LOCK TABLES `teams` WRITE;
/*!40000 ALTER TABLE `teams` DISABLE KEYS */;
INSERT INTO `teams` VALUES (3,'warriors',4),(8,'chekos',197),(9,'falcons',213),(10,'blaze',227);
/*!40000 ALTER TABLE `teams` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tournament_teams`
--

DROP TABLE IF EXISTS `tournament_teams`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tournament_teams` (
  `tournament_id` int NOT NULL,
  `team_id` int NOT NULL,
  `joined_by` int DEFAULT NULL,
  `status` varchar(20) DEFAULT 'PENDING',
  PRIMARY KEY (`tournament_id`,`team_id`),
  UNIQUE KEY `tournament_id` (`tournament_id`,`team_id`),
  KEY `team_id` (`team_id`),
  CONSTRAINT `tournament_teams_ibfk_1` FOREIGN KEY (`tournament_id`) REFERENCES `tournaments` (`tournament_id`) ON DELETE CASCADE,
  CONSTRAINT `tournament_teams_ibfk_2` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tournament_teams`
--

LOCK TABLES `tournament_teams` WRITE;
/*!40000 ALTER TABLE `tournament_teams` DISABLE KEYS */;
/*!40000 ALTER TABLE `tournament_teams` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tournaments`
--

DROP TABLE IF EXISTS `tournaments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tournaments` (
  `tournament_id` int NOT NULL AUTO_INCREMENT,
  `tournament_name` varchar(100) NOT NULL,
  `hosted_by` int NOT NULL,
  `tournament_date` date DEFAULT NULL,
  `tournament_type` varchar(20) DEFAULT NULL,
  `overs` int DEFAULT NULL,
  `match_type` varchar(10) DEFAULT NULL,
  `ball_type` varchar(10) DEFAULT NULL,
  `location` varchar(100) DEFAULT NULL,
  `logo` varchar(255) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `host_name` varchar(100) DEFAULT NULL,
  `host_mobile` varchar(15) DEFAULT NULL,
  `is_started` tinyint(1) DEFAULT '0',
  `is_completed` tinyint(1) DEFAULT '0',
  `man_of_tournament_id` int DEFAULT NULL,
  PRIMARY KEY (`tournament_id`),
  KEY `hosted_by` (`hosted_by`),
  CONSTRAINT `tournaments_ibfk_1` FOREIGN KEY (`hosted_by`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tournaments`
--

LOCK TABLES `tournaments` WRITE;
/*!40000 ALTER TABLE `tournaments` DISABLE KEYS */;
/*!40000 ALTER TABLE `tournaments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `user_id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `mobile_no` varchar(15) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('batsman','bowler','all-rounder') NOT NULL,
  `profile_pic` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `mobile_no` (`mobile_no`)
) ENGINE=InnoDB AUTO_INCREMENT=253 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'Hemit','9999999999','1234','batsman','user_1_photo2.jpeg'),(4,'parth','1234567892','12345678','bowler',NULL),(6,'Hemit','9999990001','1234','batsman',NULL),(7,'Rahul','9999990002','1234','bowler',NULL),(8,'Amit','9999990003','1234','all-rounder',NULL),(9,'Ravi','9999990004','1234','batsman',NULL),(10,'Kunal','9999990005','1234','bowler',NULL),(11,'Jay','9999990006','1234','all-rounder',NULL),(12,'Dev','9999990007','1234','batsman',NULL),(13,'Yash','9999990008','1234','bowler',NULL),(14,'Nikhil','9999990009','1234','all-rounder',NULL),(15,'Arjun','9999990010','1234','batsman',NULL),(16,'Soham','9999990011','1234','bowler',NULL),(17,'Manav','9999990012','1234','all-rounder',NULL),(18,'Rohit','9999990013','1234','batsman',NULL),(19,'Virat','9999990014','1234','batsman',NULL),(20,'Hardik','9999990015','1234','all-rounder',NULL),(197,'Hemit Bhatt','9000000056','pass','all-rounder',NULL),(198,'Aarav Patel','9000000057','pass','batsman',NULL),(199,'Vivaan Shah','9000000058','pass','bowler',NULL),(200,'Aditya Mehta','9000000059','pass','all-rounder',NULL),(201,'Krish Desai','9000000060','pass','batsman',NULL),(202,'Rohan Joshi','9000000061','pass','bowler',NULL),(203,'Dhruv Trivedi','9000000062','pass','all-rounder',NULL),(204,'Yash Pandya','9000000063','pass','batsman',NULL),(205,'Harsh Vyas','9000000064','pass','bowler',NULL),(206,'Raj Patel','9000000065','pass','all-rounder',NULL),(207,'Nirav Shah','9000000066','pass','batsman',NULL),(208,'Jay Mehta','9000000012','pass','bowler',NULL),(209,'Parth Patel','9000000013','pass','all-rounder',NULL),(210,'Meet Shah','9000000014','pass','batsman',NULL),(211,'Dev Patel','9000000015','pass','bowler',NULL),(212,'Smit Desai','9000000016','pass','all-rounder',NULL),(213,'Om Trivedi','9000000017','pass','batsman',NULL),(214,'Kunal Shah','9000000018','pass','bowler',NULL),(215,'Amit Patel','9000000019','pass','all-rounder',NULL),(216,'Chirag Mehta','9000000020','pass','batsman',NULL),(217,'Vatsal Shah','9000000021','pass','bowler',NULL),(218,'Deep Patel','9000000022','pass','all-rounder',NULL),(219,'Manav Desai','9000000023','pass','batsman',NULL),(220,'Tushar Shah','9000000024','pass','bowler',NULL),(221,'Ravi Patel','9000000025','pass','all-rounder',NULL),(222,'Sagar Mehta','9000000026','pass','batsman',NULL),(223,'Nikhil Shah','9000000027','pass','bowler',NULL),(224,'Darshan Patel','9000000028','pass','all-rounder',NULL),(225,'Ankit Desai','9000000029','pass','batsman',NULL),(226,'Vivek Shah','9000000030','pass','bowler',NULL),(227,'Hiren Patel','9000000031','pass','all-rounder',NULL),(228,'Jatin Mehta','9000000032','pass','batsman',NULL),(229,'Kalpesh Shah','9000000033','pass','bowler',NULL),(230,'Mihir Patel','9000000034','pass','all-rounder',NULL),(231,'Rakesh Desai','9000000035','pass','batsman',NULL),(232,'Mahesh Shah','9000000036','pass','bowler',NULL),(233,'Dinesh Patel','9000000037','pass','all-rounder',NULL),(234,'Sunil Mehta','9000000038','pass','batsman',NULL),(235,'Paresh Shah','9000000039','pass','bowler',NULL),(236,'Kiran Patel','9000000040','pass','all-rounder',NULL),(237,'Naresh Desai','9000000041','pass','batsman',NULL),(238,'Bhavesh Shah','9000000042','pass','bowler',NULL),(239,'Mukesh Patel','9000000043','pass','all-rounder',NULL),(240,'Alpesh Mehta','9000000044','pass','batsman',NULL),(241,'Hardik Shah','9000000045','pass','bowler',NULL),(242,'Jignesh Patel','9000000046','pass','all-rounder',NULL),(243,'Prakash Desai','9000000047','pass','batsman',NULL),(244,'Bharat Shah','9000000048','pass','bowler',NULL),(245,'Kishan Patel','9000000049','pass','all-rounder',NULL),(246,'Arjun Mehta','9000000050','pass','batsman',NULL),(247,'Laksh Shah','9000000051','pass','bowler',NULL),(248,'Veer Patel','9000000052','pass','all-rounder',NULL),(249,'Rudra Desai','9000000053','pass','batsman',NULL),(250,'Kabir Shah','9000000054','pass','bowler',NULL),(251,'Ayaan Patel','9000000055','pass','all-rounder',NULL),(252,'SHLOK PATEL','4545455656','5678','all-rounder','user_252_IMG-20250922-WA0015.jpg');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-04-18 15:56:37
