from flask import Flask, redirect, render_template, request, url_for, flash, session
from dotenv import load_dotenv
from waitress import serve
import bcrypt
import os

# Kobling til db
from python.conn import db_connect

# Kobling til laptop-db (brukes når pi ikke er tilgjengelig)
from python.laptop_conn import ltdb_connect

# Bestemmer om rpi- eller laptop-db-kobling skal brukes
rpi_db = False

load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get("APP_SECRET_KEY")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
    #serve(app, host="0.0.0.0", port=5000)

def create_tables():
    # ltdb/db
    conn = db_connect() if rpi_db else ltdb_connect()
    cursor = conn.cursor()
    
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

# Rolletabell
    cursor.execute("""
CREATE TABLE role (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(20)
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

    # Henter info som en liste/tuple.
    cursor.execute("SELECT name, year_published, publisher FROM boardgame")
    bg_info = cursor.fetchall()
    
    return render_template("index.html", bg_info=bg_info)

# Registrering
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        
        conn = db_connect() if rpi_db else ltdb_connect()
        cursor = conn.cursor()
        username = request.form['username']
        epost = request.form['email']
        # Kode fra geeksforgeeks.org for hashing med bcrypt
        password = (request.form['password'])
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        password_hash_bytes = bcrypt.hashpw(password_bytes, salt)
        # Siden jeg bruker CHAR(60) i DB må jeg omgjøre til tekststreng
        password_hash_str = password_hash_bytes.decode()

        cursor.execute("INSERT INTO user (username, email, password) VALUES (%s, %s, %s)", (username, epost, password_hash_str))
        conn.commit()
        cursor.close()
        conn.close()
        
        flash("User registered!", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

# Innlogging
# Bcrypt istedenfor Werkzeug.
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
        cursor.close()
        conn.close()
        
        # Henter passord og gjør om til bytes.
        if user:
            db_password = user['password'].encode('utf-8')
        # Hvis den ikke finner bruker, gis den ikke verdi
        else:
            db_password = None

        if db_password:
            # Sjekker passord mot hverandre
            if bcrypt.checkpw(password, db_password):
                session['username'] = user['username']
                session['role_id'] = user['role_id']

                flash("You are now logged in!")
                return redirect(url_for("index"))
        # Beskjed om feil til bruker
        else:
            flash("Invalid username or password")
            return redirect(url_for("login"))
    return render_template("login.html")

# Registrering av brettspill
@app.route("/register_boardgame", methods=["GET", "POST"])
def register_boardgame():
    
    conn = db_connect() if rpi_db else ltdb_connect()
    cursor = conn.cursor()
    
    # Fra "How to use Flask-Session in Python Flask". Se kilder.
    # Sjekker om bruker er logget inn og redirecter til index hvis ikke.
    if not session.get("username") or not session.get("role_id"):
        flash("You must be admin or editor to access '/register_boardgame'.")
        return redirect(url_for("index"))
    
    # Kodesnutt er fikset/minimalisert ved hjelp av KI.
    # Sjekker om bruker har riktig rolle, hvis ikke blir du redirected til index.
    # Roller: admin (1), editor (2), user (3).
    if session["role_id"] not in (1, 2):
        flash("You must be admin or editor to access '/register_boardgame'.")
        return redirect(url_for("index"))
    
    # Kjøres ved POST-ing av login-form.
    if request.method == "POST":
        bg_name = request.form['name']
        year = request.form['year']
        creator = request.form['creator']
        publisher = request.form['publisher']
        img_filepath = "../static/media/" + request.form['img-filename']
        desc = request.form['description']

        if not bg_name:
            flash("Name is required.")
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

# Utlogging
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# Funksjon som brukes i search-route.
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
# Creds til Ochoaprojects. Se kilder.
@app.route('/search', methods=['POST'])
def search():
    user_query = request.form['query']
    query = '%' + request.form['query'] + '%'
    results = perform_search(query)
    return render_template('results.html', user_query=user_query, results=results)