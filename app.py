from flask import Flask, request, jsonify, render_template
# J'importe tes fonctions de base de données (comme dans ton code)
from python.database import check_etudiant, check_professeur, check_admin

app = Flask(__name__)

# --- ROUTES API (Ce que tu avais fait en FastAPI) ---

@app.route("/")
def main_function():
    # Pour l'instant on laisse ça, mais plus tard ça pourrait être : return render_template("login.html")
    return jsonify({"statu": "server is running"})

@app.route("/login/etudiant", methods=["POST"])
def login_etudiant():
    # En Flask, on récupère les données JSON envoyées par le front-end comme ça :
    data = request.get_json() 
    if check_etudiant(data["email"], data["password"]):
        return jsonify({"statu": "login successfully"})
    else:
        return jsonify({"statu": "login failed"})

@app.route("/login/professeur", methods=["POST"])
def login_professeur():
    data = request.get_json()
    if check_professeur(data["email"], data["password"]):
        return jsonify({"statu": "login successfully"})
    else:
        return jsonify({"statu": "login failed"})

@app.route("/login/admin", methods=["POST"])
def login_admin():
    data = request.get_json()
    if check_admin(data["username"], data["password"]):
        return jsonify({"statu": "login successfully"})
    else:
        return jsonify({"statu": "login failed"})

if __name__ == "__main__":
    app.run(debug=True)