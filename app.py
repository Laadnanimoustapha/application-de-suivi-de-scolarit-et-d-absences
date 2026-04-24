from flask import Flask, request, render_template, redirect, url_for
from python.database import check_etudiant, check_professeur, check_admin

app = Flask(__name__)

@app.route("/")
def main_function():
    # On peut passer une variable "error" vide au départ
    return render_template("login.html", error=None)

@app.route("/login/etudiant", methods=["POST"])
def login_etudiant():
    # En Flask classique, on récupère les données des balises <input> comme ça :
    email = request.form.get("email")
    password = request.form.get("password")
    
    if check_etudiant(email, password):
        # Si c'est bon, on le redirige vers sa page
        return redirect(url_for("eleve_dash"))
    else:
        # Si c'est faux, on recharge la page login avec un message d'erreur
        return render_template("login.html", error="Identifiants Élève incorrects")

@app.route("/login/professeur", methods=["POST"])
def login_professeur():
    email = request.form.get("email")
    password = request.form.get("password")
    
    if check_professeur(email, password):
        return redirect(url_for("prof_dash"))
    else:
        return render_template("login.html", error="Identifiants Professeur incorrects")

@app.route("/login/admin", methods=["POST"])
def login_admin():
    username = request.form.get("username")
    password = request.form.get("password")
    
    if check_admin(username, password):
        return redirect(url_for("admin_dash"))
    else:
        return render_template("login.html", error="Identifiants Administrateur incorrects")

# --- LES ROUTES DES DASHBOARDS ---

@app.route("/admin/dashboard")
def admin_dash():
    return render_template("dashboard_admin.html")

@app.route("/prof/dashboard")
def prof_dash():
    return render_template("dashboard_prof.html")

@app.route("/eleve/dashboard")
def eleve_dash():
    return render_template("dashboard_eleve.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)