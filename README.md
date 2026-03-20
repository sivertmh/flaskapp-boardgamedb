# Prosjektbeskrivelse – IT-utviklingsprosjekt (2IMI)

## Prosjekttittel

**Internet Boardgame Database (IBDb)**

---

## Deltakere

Sivert M. Hansen (Individuelt prosjekt)

---

## 1. Prosjektidé og problemstilling

### Beskrivelse

- Hva er prosjektet?

Prosjektet en Flask-applikasjon som jeg utvikler for å lære meg python-rammeverket, altså Flask. Det er en skoleoppgave og vi har krav om blant annet å et inloggings-system på plass. Ellers vil jeg utforske funksjoner som søking, visning av database-innhold og brukerdashbord. 

- Hvilket problem løser det?

Nettsiden skal la deg som sagt søke opp brettspill og finne info om de. Dette kan man bruke som et verktøy for å researche spillet eller si noe om hvilke målgruppper spillet passer. Da slipper du å komme til spillekvelden med et spill ingen liker!

- Hvorfor er løsningen nyttig?

Nettsiden funker som et oppslagsverk for brettspill. Det betyr at du kan søke opp spill du allerede har for kanskje å hvordan det spilles om du f.eks. mistet reglene. Dersom du ikke har et spill kan du bruke nettsiden til å lese deg opp på nett isteden for å måtte dra til byen eller kjøpesenteret.

### Målgruppe

Hvem er løsningen laget for?

Løsningen er laget for de som spiller og liker brettspill, og de som vil finne ut mer om de. Det kan f.eks. være før de velger å kjøpe det, eller ikke, p.g.a. det de leste om det. Det kan også f.eks. være de som har mistet regler og glemte hva målet i spillet var som bruker siden for å minne seg selv på dette.

### Refleksjon

#### Mulige Forbedringer

Det er noen funksjoner og aspekter til prosjektet som kunne trengt forbedring. Enten om det er en revisjon av noe eller en helt ny funksjon. Her er noen konkrete ideer basert på min brukertesting:

**Egen side for hvert spill**

Dette kan nesten klassifiseres som en manglende funksjon. Hver av spillene på forsiden, eller hvis du søker de opp, burde ha sin egen side hvor du får flere detaljer og beskrivelse av spillet. Selv om dette ikke sto i målene jeg satt, er ikke nettsiden helt komplett uten. Hvis jeg velger å fortsette på prosjektet, er dette en viktig del.

**Brukeradministrering**

Admin har oversikt over brukere og kan angi roller. Man slipper da å manuelt gå inn i database med SSH. Dette gir også en reell grunn til å ha en editor-rolle, da admin har samme tillatelser som editor, og nå faktisk fler.

**Rolleindikator**

Muligheten til å se hva slags rolle din bruker har. Det kan gjøres ved å ha tekst i navbar eller i navbar men i dropdown når man er logget inn.

**Innloggingsstatus**

Dette ligner en del på rolleindikator-ideen, men enklere. Brukeren kan se at de er logget inn. Kan gjøres ved å vise brukernavn i navbar.

---

## 2. Funksjonelle krav

Systemet skal minst ha følgende funksjoner:

1. Registrering

2. Innlogging

3. Søke etter brettspill

4. Registrere brettspill (om admin/editor)

5. Ulikt innhold/tillatelser basert på rolle (registrering av brettspill)

---

## 3. Teknologivalg

### Programmeringsspråk

- Python

### Rammeverk / Plattform / Spillmotor

- Flask

### Database

- MariaDB

### Verktøy

- GitHub
- GitHub Projects (Kanban)

---

## 4. Datamodell

### Programstruktur

Under ser du en oversikt av de funksjonelle delene som trengs i programmet:

boardgame-site/
├── app.py
├── templates/
| ├── index.html
| ├── register.html
| ├── login.html
| ├── register_boardgame.html
| └── results.html
├── static/
| ├── media/
| ├── stylesheets/
| └── style.css
└── .env

### Oversikt over tabeller

**Tabell 1:**

- Navn: user
- Beskrivelse: Innholder brukerinfo om email, brukernavn og et hashet og saltet passord.

**Tabell 2:**

- Navn: boardgame
- Beskrivelse: Inneholder brettspillets navn, hvilket år det kom ut, de som lagde det, de som publiserte det og en beskrivelse.

**Tabell 3:**

- Navn: role
- Beskrivelse: Inneholder forskjellige roller som brukere kan ha. Her må jeg kjøre en manuell Insert, eller lage en funksjon i Python-filen.

### Tabellstruktur i Databasen

```sql
-- Tabell 1

CREATE TABLE `user` (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password CHAR(60) NOT NULL,
    role_id INT, FOREIGN KEY (role_id) REFERENCES role(id)
);

-- Tabell 2

CREATE TABLE boardgame (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    year_published INT,
    creator VARCHAR(255),
    publisher VARCHAR(255),
    img_filename VARCHAR(255),
    description TEXT CHARACTER SET utf8mb4
    );

-- Tabell 3

CREATE TABLE role (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(20)
)

-- Innhold til tabell 3

INSERT INTO role (name) VALUES ("admin"), ("editor"), ("user");

-- Rolle-tabellens innhold ser dermed slik ut:

+----+--------+
| id | name   |
+----+--------+
|  1 | admin  |
|  2 | editor |
|  3 | user   |
+----+--------+
-- Her ser man hvilke id som tilhører hvilke rolle
```

### Hvordan sette opp dette systemet

Før du starter må du ha installert disse på systemet:

- git
- python

Deretter kan du starte ved å klone prosjektet:

```bash
git clone https://github.com/sivertmh/boardgame-site.git
```

Så installere nødvendige pakker for appen (Det er lurt å gjøre dette i et **venv** i python):

```bash
pip install -r requirements.txt
```

Nå kan du kjøre prosjektet lokalt:

```bash
python -m flask run
```

Utenom server/database, er dette alt du trenger for å bruke/teste Flask-appen.

---

**Kilder:**

- dotenv: [https://www.geeksforgeeks.org/python/how-to-create-and-use-env-files-in-python/](https://www.geeksforgeeks.org/python/how-to-create-and-use-env-files-in-python/)

- bcrypt hashing: [https://www.geeksforgeeks.org/python/hashing-passwords-in-python-with-bcrypt/](https://www.geeksforgeeks.org/python/hashing-passwords-in-python-with-bcrypt/)

- bytte brukernavn Mysql: [https://dev.mysql.com/doc/refman/8.4/en/rename-user.html](https://dev.mysql.com/doc/refman/8.4/en/rename-user.html)

- få liste av alle brukere i Mysql: [https://phoenixnap.com/kb/mysql-show-users](https://phoenixnap.com/kb/mysql-show-users)

- Bytte passord i Mysql: [https://dev.mysql.com/doc/refman/8.4/en/alter-user.html](https://dev.mysql.com/doc/refman/8.4/en/alter-user.html)

- Bcrypt CHAR(60): [https://stackoverflow.com/questions/5881169/what-column-type-length-should-i-use-for-storing-a-bcrypt-hashed-password-in-a-d](https://stackoverflow.com/questions/5881169/what-column-type-length-should-i-use-for-storing-a-bcrypt-hashed-password-in-a-d)

- _SQL Data Types_: [https://www.geeksforgeeks.org/sql/sql-data-types/](https://www.geeksforgeeks.org/sql/sql-data-types/)

- Innholdstekst tatt fra Boardgamegeeks nettsider: [https://boardgamegeek.com](https://boardgamegeek.com)

- Flash med flask: [https://flask.palletsprojects.com/en/stable/patterns/flashing/](https://flask.palletsprojects.com/en/stable/patterns/flashing/)

- Lage roller i mysql (system, ikke i oppgave): [https://www.geeksforgeeks.org/sql/sql-creating-roles/](https://www.geeksforgeeks.org/sql/sql-creating-roles/)

- _How to use Flask-Session in Python Flask_: [https://www.geeksforgeeks.org/python/how-to-use-flask-session-in-python-flask/](https://www.geeksforgeeks.org/python/how-to-use-flask-session-in-python-flask/)

- _Building a Search Feature in a Python Flask App_: [https://ochoaprojects.com/posts/FlaskAppWithSimpleSearch/](https://ochoaprojects.com/posts/FlaskAppWithSimpleSearch/)

- _MySQL LIKE Operator_:[https://www.w3schools.com/mysql/mysql_like.asp](https://www.w3schools.com/mysql/mysql_like.asp)
