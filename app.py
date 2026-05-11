from flask import Flask, redirect, render_template, request, url_for, flash, session
from dotenv import load_dotenv
import bcrypt
import os
from waitress import serve

# Kobling til db
from python.conn import db_connect
# Kobling til laptop-db (brukes når pi ikke er tilgjengelig)
from python.laptop_conn import ltdb_connect

# Bestemmer om rpi- eller laptop-db-kobling skal brukes
rpi_db = False

load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get("APP_SECRET_KEY")

def create_tables():
    # ltdb/db
    conn = db_connect() if rpi_db else ltdb_connect()
    cursor = conn.cursor()
    
# Rolletabell
    cursor.execute("""
CREATE TABLE role (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(20)
)
""")
    
# Brukertabell
# Bruker backticks på tabellnavnet "user" p.g.a. eksisterende Mysql-fenomen.
    cursor.execute("""
CREATE TABLE `user` (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password CHAR(60) NOT NULL,
    role_id INT, FOREIGN KEY (role_id) REFERENCES role(id)
)
""")

# Brettspilltabell
    cursor.execute("""
CREATE TABLE boardgame (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    year_published INT,
    creator VARCHAR(255),
    publisher VARCHAR(255),
    img_filename VARCHAR(255),
    description TEXT CHARACTER SET utf8mb4
    )
""")

    conn.commit()
    conn.close()

# Prøver å lage tabeller
try:
    create_tables()
    print("Tabeller ble laget!")
except:
    print("Tabeller ble ikke laget. (ignorer om de finnes fra før)")

# Hjemside
@app.route("/")
def index():
    
    conn = db_connect() if rpi_db else ltdb_connect()
    cursor = conn.cursor()

    # Henter brettspillinfo som en liste/tuple.
    cursor.execute("SELECT name, year_published, publisher, img_filename FROM boardgame")
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
            cursor.execute("INSERT INTO user (username, email, password, role_id) VALUES (%s, %s, %s, %s, %s)", (username, email, password_hash_str, 3))
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
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password'].encode('utf-8')
        
        conn = db_connect() if rpi_db else ltdb_connect()
        cursor = conn.cursor(dictionary=True)
        
        # Henter brukernavn.
        cursor.execute("SELECT * FROM user WHERE username=%s", (username,))
        user = cursor.fetchone()
        
        
        # Henter passord og gjør om til bytes.
        if user:
            db_password = user['password'].encode('utf-8')
        # Hvis den ikke finner bruker, gis den tom verdi
        else:
            db_password = None

        if db_password:
            # Sjekker passordene mot hverandre
            if bcrypt.checkpw(password, db_password) and user['active'] == 1:
                conn = db_connect() if rpi_db else ltdb_connect()
                cursor = conn.cursor(dictionary=True)
                
                # Henter rollenavn basert på rolle-id
                cursor.execute("SELECT name FROM role WHERE id=%s", (user['role_id'],))
                role = cursor.fetchone()
                
                # Session-cookies for brukerinfo settes
                session['username'] = user['username']
                session['role_id'] = user['role_id']
                # Session-cookie for rollenavn
                session['role_name'] = role['name'].capitalize()
                
                flash("Successfully logged in!", "success")
                return redirect(url_for("index"))
        # Feilmelding til bruker            
        else:
            flash("Invalid username or password", "error")
            return redirect(url_for("login"))
        
        cursor.close()
        conn.close()
    return render_template("login.html" )

# Utlogging
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# Registrering av brettspill
@app.route("/register_boardgame", methods=["GET", "POST"])
def register_boardgame():
    
    conn = db_connect() if rpi_db else ltdb_connect()
    cursor = conn.cursor()
    
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
    
    # Kjøres ved POST-ing av login-form.
    if request.method == "POST":
        bg_name = request.form['name']
        year = request.form['year']
        creator = request.form['creator']
        publisher = request.form['publisher']
        img_filepath = "./static/media/" + request.form['img-filename']
        desc = request.form['description']

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
    if request.method == "POST":
        conn = db_connect() if rpi_db else ltdb_connect()
        cursor = conn.cursor()
        
        username = session["username"]
        
        # Brukernavn fra form
        form_username = request.form["username"]
        # Passord fra form gjøres om til bytes
        form_password = request.form["password"].encode('utf-8')
        
        # Henter passord fra db basert på brukernavn i session
        cursor.execute("SELECT password FROM user WHERE username=%s", (username,))
        # Gjør om hentet passord til bytes
        password_from_db = cursor.fetchone()[0].encode('utf-8')
        
        cursor.close()
        conn.close()
        
        # Sletting av bruker
        # Betingelsen sjekker brukernavnene mot hverandre og passordene mot hverandre 
        if session['username'] == form_username and bcrypt.checkpw(form_password, password_from_db):
            conn = db_connect() if rpi_db else ltdb_connect()
            cursor = conn.cursor()
            
            cursor.execute("UPDATE user SET active=0 WHERE username=%s", (username,))
            conn.commit()
            session.clear()
            flash("Successfully deleted account.", "success")
            return redirect(url_for('index'))
        else:
            flash("Wrong username or password.", "error")
    return render_template('dashboard.html')

if __name__ == "__main__":
    #app.run(debug=True)
    serve(app, host="0.0.0.0", port=8080)
