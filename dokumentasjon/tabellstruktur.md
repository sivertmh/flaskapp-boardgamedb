# Tabeller -- Internet Boardgame Database (IBDb)

```sql
-- Tabellene i IBDb:

-- Brettspill
DESC boardgame;
+----------------+--------------+------+-----+---------+----------------+
| Field          | Type         | Null | Key | Default | Extra          |
+----------------+--------------+------+-----+---------+----------------+
| id             | int(11)      | NO   | PRI | NULL    | auto_increment |
| name           | varchar(255) | NO   |     | NULL    |                |
| year_published | int(11)      | YES  |     | NULL    |                |
| creator        | varchar(255) | YES  |     | NULL    |                |
| publisher      | varchar(255) | YES  |     | NULL    |                |
| description    | text         | YES  |     | NULL    |                |
| img_filename   | varchar(255) | YES  |     | NULL    |                |
+----------------+--------------+------+-----+---------+----------------+

-- Brukere
DESC user;
+----------+--------------+------+-----+---------+----------------+
| Field    | Type         | Null | Key | Default | Extra          |
+----------+--------------+------+-----+---------+----------------+
| id       | int(11)      | NO   | PRI | NULL    | auto_increment |
| username | varchar(255) | NO   | UNI | NULL    |                |
| email    | varchar(255) | NO   | UNI | NULL    |                |
| password | char(60)     | NO   |     | NULL    |                |
| role_id  | int(11)      | YES  | MUL | NULL    |                |
+----------+--------------+------+-----+---------+----------------+

-- Roller
DESC role;
+-------+-------------+------+-----+---------+----------------+
| Field | Type        | Null | Key | Default | Extra          |
+-------+-------------+------+-----+---------+----------------+
| id    | int(11)     | NO   | PRI | NULL    | auto_increment |
| name  | varchar(20) | YES  |     | NULL    |                |
+-------+-------------+------+-----+---------+----------------+

```