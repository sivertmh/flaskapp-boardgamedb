from flask import Flask, redirect, render_template, request, url_for, flash, session
from dotenv import load_dotenv
import bcrypt
import os
from waitress import serve
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Kobling til pi-db og laptop-db (laptop brukes når pi ikke er tilgjengelig)
from python.conn import db_connect
from python.laptop_conn import ltdb_connect

load_dotenv()

# Bestemmer om rpi- eller laptop-db-kobling skal brukes
rpi_db = True

app = Flask(__name__)
app.secret_key = os.environ.get("APP_SECRET_KEY")
# Se "Flask-Limiter" kilder.
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

def create_db_structure():
    # ltdb/db
    conn = db_connect() if rpi_db else ltdb_connect()
    cursor = conn.cursor()
    
    # Rolletabell
    # Må lages før brukertabell pga foreign key.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS role (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(20) UNIQUE NOT NULL
        )
    """)
    # Innhold til rolletabell
    cursor.execute("""
        INSERT IGNORE INTO role (name) VALUES ("admin"), ("editor"), ("user")
    """)
    
    # Brukertabell
    # Bruker backticks på tabellnavnet "user" p.g.a. eksisterende Mysql-fenomen.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `user` (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) NOT NULL UNIQUE,
            email VARCHAR(255) NOT NULL UNIQUE,
            password CHAR(60) NOT NULL,
            role_id INT, FOREIGN KEY (role_id) REFERENCES role(id),
            active TINYINT(1) DEFAULT 1
        )
    """)

    # Brettspilltabell
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS boardgame (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            year_published INT,
            creator VARCHAR(255),
            publisher VARCHAR(255),
            img_filename VARCHAR(255),
            description TEXT CHARACTER SET utf8mb4
        )
    """)
    
    # Spørsmålstabell
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS question (
            id INT AUTO_INCREMENT PRIMARY KEY,
            question TEXT NOT NULL,
            created_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES `user`(id)
        )
    """)

    conn.commit()
    conn.close()

# Prøver å lage tabeller
try:
    create_db_structure()
    print("Databasestruktur ble laget!")
except Exception as e:
    print(f"Error: Databasestruktur ble ikke laget. {e}")

# Hjemside
@app.route("/")
def index():
    
    conn = db_connect() if rpi_db else ltdb_connect()
    cursor = conn.cursor()

    # Henter brettspillinfo som en liste/tuple.
    cursor.execute("SELECT name, year_published, publisher, img_filename, id FROM boardgame")
    bg_info = cursor.fetchall()
    
    return render_template("index.html", bg_info=bg_info)

# Registrering
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
            # Enten kobling til db på laptop eller rpi
            conn = db_connect() if rpi_db else ltdb_connect()
            cursor = conn.cursor()
            username = request.form['username']
            email = request.form['email']
            # Kode fra geeksforgeeks.org for hashing med bcrypt
            password = (request.form['password'])
            password_bytes = password.encode('utf-8')
            salt = bcrypt.gensalt()
            password_hash_bytes = bcrypt.hashpw(password_bytes, salt)
            # Siden jeg bruker CHAR(60) i DB må jeg gjøre om til tekststreng
            password_hash_str = password_hash_bytes.decode()
            # Setter info inn i databasen (3 er rolle-id for vanlig bruker)
            cursor.execute("INSERT INTO user (username, email, password, role_id) VALUES (%s, %s, %s, %s)", (username, email, password_hash_str, 3))
            conn.commit()
            cursor.close()
            conn.close()
            
            flash("User registered!", "success")
            return redirect(url_for("login"))
    return render_template("register.html")

# Innlogging
# Bcrypt istedenfor Werkzeug.
# Bcrypt er teoretisk sett litt sterkere, men i praksis gjorde jeg det for å prøve ut en annen løsning.
@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password'].encode('utf-8')
        
        conn = db_connect() if rpi_db else ltdb_connect()
        cursor = conn.cursor(dictionary=True)
        
        # Henter brukernavn fra db ved hjelp av form-data
        cursor.execute("SELECT * FROM user WHERE username=%s", (username,))
        user = cursor.fetchone()
        
        if user:
            # Henter passord og gjør om til bytes.
            db_password = user['password'].encode('utf-8')
        else:
            # Hvis den ikke finner bruker, gis den tom verdi
            db_password = None

        if db_password:
            # Sjekker passordene mot hverandre
            if bcrypt.checkpw(password, db_password) and user['active'] == 1:
                conn = db_connect() if rpi_db else ltdb_connect()
                cursor = conn.cursor(dictionary=True)
                
                # Henter rollenavn basert på rolle-id
                cursor.execute("SELECT name FROM role WHERE id=%s", (user['role_id'],))
                role = cursor.fetchone()
                
                # Session-cookies
                session['username'] = user['username']
                session['role_id'] = user['role_id']
                session['role_name'] = role['name']
                
                flash("Successfully logged in!", "success")
                return redirect(url_for("index"))
        else:
            # Feilmelding til bruker          
            flash("Invalid username or password.", "error")
            return redirect(url_for("login"))
        
        cursor.close()
        conn.close()
    return render_template("login.html" )

# Utlogging
@app.route("/logout")
def logout():
    session.clear()
    flash("Successfully logged out!", "success")
    return redirect(url_for("index"))

# Registrering av brettspill
@app.route("/register_boardgame", methods=["GET", "POST"])
def register_boardgame():
    
    # Fra "How to use Flask-Session in Python Flask". Se kilder.
    # Sjekker om bruker er logget inn og redirecter til index hvis ikke.
    if not session.get("username") or not session.get("role_id"):
        flash("You are not authorized to view this page.", "error")
        return redirect(url_for("index"))
    
    # Kodesnutt er fikset/minimalisert ved hjelp av KI (Microsoft Copilot).
    # Sjekker om bruker har riktig rolle, hvis ikke blir du omdirigert til hjemside.
    # Roller: admin (1), editor (2), user (3).
    if session["role_id"] not in (1, 2):
        flash("You are not authorized to view this page.", "error")
        return redirect(url_for("index"))
    
    conn = db_connect() if rpi_db else ltdb_connect()
    cursor = conn.cursor()
    
    # Kjøres ved POST-ing av brettspill-form.
    if request.method == "POST":
        bg_name = request.form['name'].strip()
        year = request.form['year'].strip()
        creator = request.form['creator'].strip()
        publisher = request.form['publisher'].strip()
        img_filepath = "./static/media/" + request.form['img-filename'].strip()
        desc = request.form['description'].strip()

        if not bg_name:
            flash("Name is required.", "error")
            return redirect(url_for("register_boardgame"))
        
        cursor.execute("""INSERT INTO boardgame ( 
                            name, 
                            year_published, 
                            creator, 
                            publisher,
                            img_filename,
                            description
                            ) VALUES (%s, %s, %s, %s, %s, %s)""", (bg_name, year, creator, publisher, img_filepath, desc))
        conn.commit()
        
        
        
        flash("Boardgame registered!", "success")
        return redirect(url_for("register_boardgame"))
    
    cursor.close()
    conn.close()
    
    return render_template("register_boardgame.html")

# Funksjon som brukes i search-routen.
# Creds til Ochoaprojects. Se kilder. Modifisert.
def perform_search(query):
    conn = db_connect() if rpi_db else ltdb_connect()
    cursor = conn.cursor()

    # Kjører søk i database med query fra bruker.
    cursor.execute("SELECT * FROM boardgame WHERE name LIKE %s", (query,))
    results = cursor.fetchall()

    conn.close()

    return results

# Route for søk
# Creds til Ochoaprojects. Se kilder. Modifisert.
@app.route('/search', methods=['POST'])
def search():
    user_query = request.form['query']
    query = '%' + request.form['query'] + '%'
    results = perform_search(query)
    return render_template('results.html', user_query=user_query, results=results)

# Route for dashbord
@app.route('/dashboard', methods=["GET", "POST"])
def dashboard():
    # DB-kobling
    conn = db_connect() if rpi_db else ltdb_connect()
    cursor = conn.cursor()
    
    # Henter spørsmål fra DB
    cursor.execute("SELECT q.question, q.created_on, u.username AS user FROM question q INNER JOIN user u ON u.id = q.user_id;")
    question_info = cursor.fetchall()
    
    cursor.execute("SELECT username, email FROM user WHERE username=%s", (session["username"],))
    user_info = cursor.fetchone()
    
    if request.method == "POST":
        # DB-kobling
        conn = db_connect() if rpi_db else ltdb_connect()
        cursor = conn.cursor()
        
        username = session["username"]
        
        # Brukernavn fra form
        form_username = request.form["username"]
        # Passord fra form gjøres om til bytes
        form_password = request.form["password"].encode('utf-8')
        
        # Henter passord fra db basert på brukernavn i session
        cursor.execute("SELECT password, id FROM user WHERE username=%s", (username,))
        user_info = cursor.fetchone()
        # Gjør om hentet passord til bytes
        user_password = user_info[0].encode('utf-8')
        user_id = user_info[1]
        
        cursor.close()
        conn.close()
        
        # Sletting av bruker
        # Betingelsen sjekker brukernavnene mot hverandre og passordene mot hverandre 
        if session['username'] == form_username and bcrypt.checkpw(form_password, user_password):
            conn = db_connect() if rpi_db else ltdb_connect()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE user
                SET active=0, username=CONCAT("redacted_username", %s), email=CONCAT("redacted_email", %s), password='REDACTED'
                WHERE username=%s""", (user_id, user_id, username))
            conn.commit()
            
            session.clear()
            flash("Successfully deleted account.", "success")
            return redirect(url_for('index'))
        else:
            flash("Wrong username or password.", "error")
    return render_template('dashboard.html', question_info=question_info, user_info=user_info)

@app.route('/faq', methods=["GET", "POST"])
def faq():
    if request.method == "POST":
        email = request.form["email"]
        question = request.form["question"]

        conn = db_connect() if rpi_db else ltdb_connect()
        cursor = conn.cursor()

        # Henter brukers id
        # Gir tom verdi om oppgitt email stemmer med pålogget bruker
        cursor.execute("SELECT id FROM user WHERE email=%s AND username=%s", (email, session['username']))
        row = cursor.fetchone()
        
        if row is None:
            flash("You need to be logged in to submit questions. If you are logged in, you used an email that does not belong to your account.", "error")
        else:
            userid = row[0]

            # Setter inn spørsmål i databasen (spørsmål og brukers id)
            cursor.execute("INSERT INTO question (question, user_id) VALUES (%s, %s)", (question, userid))
            conn.commit()
            flash("Question successfully submitted! We will try to answer it as soon as possible.")
    return render_template('faq.html')

@app.route('/favorites/<int:boardgame_id>', methods=["GET", "POST"])
def favorites(boardgame_id):
    if request.method == "POST":
        conn = db_connect() if rpi_db else ltdb_connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT FROM favorited_boardgame boardgame_id WHERE user_id=%s", (boardgame_id,))
        row = cursor.fetchone()
        
        if row:
            cursor.execute("DELETE FROM favorited_boardgame WHERE favorite_boardgame boardgame_id WHERE user_id=%s", (boardgame_id,))
        else:
            cursor.execute("INSERT INTO favorited_boardgame (user_id, boardgame_id) VALUES (%s, %s)", (session['username'], boardgame_id))

if __name__ == "__main__":
    #app.run(debug=True)
    serve(app, host="0.0.0.0", port=8080)
