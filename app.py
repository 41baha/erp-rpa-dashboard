from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import pandas as pd

app = Flask(__name__)
app.secret_key = "supersecretkey123"  # session için gerekli

def get_db():
    return sqlite3.connect("data.db")

# Veritabanı ve tabloları oluştur
conn = get_db()
conn.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    quantity INTEGER,
    price INTEGER
)
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

# admin kullanıcı ekle (ilk çalıştırmada)
try:
    conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("admin", "admin123"))
except:
    pass
conn.commit()
conn.close()

# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password)).fetchone()
        conn.close()

        if user:
            session["user"] = username
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="Kullanıcı adı veya şifre yanlış")

    return render_template("login.html", error=None)

# Logout route
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

# Ana sayfa (index)
@app.route("/")
def index():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    return render_template("index.html", products=products)

# Ürün ekleme
@app.route("/add", methods=["GET", "POST"])
def add():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form["name"]
        quantity = request.form["quantity"]
        price = request.form["price"]

        conn = get_db()
        conn.execute("INSERT INTO products (name, quantity, price) VALUES (?, ?, ?)",
                     (name, quantity, price))
        conn.commit()
        conn.close()

        return redirect("/")
    return render_template("add.html")

# Ürün silme
@app.route("/delete/<int:product_id>")
def delete(product_id):
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    conn.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit()
    conn.close()

    return redirect("/")

# Ürün düzenleme
@app.route("/edit/<int:product_id>", methods=["GET", "POST"])
def edit(product_id):
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    product = conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()

    if request.method == "POST":
        name = request.form["name"]
        quantity = request.form["quantity"]
        price = request.form["price"]
        conn.execute("UPDATE products SET name=?, quantity=?, price=? WHERE id=?",
                     (name, quantity, price, product_id))
        conn.commit()
        conn.close()
        return redirect("/")

    conn.close()
    return render_template("edit.html", product=product)

# Excel import
@app.route("/import", methods=["POST"])
def import_excel():
    if "user" not in session:
        return redirect(url_for("login"))

    file = request.files["file"]
    df = pd.read_excel(file)

    conn = get_db()
    for _, row in df.iterrows():
        conn.execute("INSERT INTO products (name, quantity, price) VALUES (?, ?, ?)",
                     (row["name"], row["quantity"], row["price"]))
    conn.commit()
    conn.close()

    return redirect("/")

# Excel export
@app.route("/export")
def export_excel():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    df = pd.read_sql_query("SELECT * FROM products", conn)
    conn.close()

    df.to_excel("export.xlsx", index=False)
    return "Excel indirildi!"

if __name__ == "__main__":
    app.run(debug=True)