from flask import Flask, request, render_template, redirect, url_for
from python.database import check_etudiant, check_professeur, check_admin, ajouter_eleve,get_tous_les_eleves,supprimer_ele,get_eleve_by_id, modifier_eleve_db, ajouter_prof, get_tous_les_profs, supprimer_pr
from python.database import supprimer_pr, get_prof_by_id, modifier_prof_db
from python.database import compter_eleves, compter_profs
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
    try:
        username = request.form.get("username")
        password = request.form.get("password")
        
        if check_admin(username, password):
            return redirect(url_for("admin_dash"))
        else:
            return render_template("login.html", error="Identifiants Administrateur incorrects")
    
    except Exception as e:
        # S'il y a une erreur avec la base de données, elle s'affichera ici !
        return f"<h1>ERREUR TROUVÉE :</h1> <p>{str(e)}</p>"

# --- LES ROUTES DES DASHBOARDS ---
@app.route("/prof/dashboard")
def prof_dash():
    return render_template("dashboard_prof.html")

@app.route("/eleve/dashboard")
def eleve_dash():
    return render_template("dashboard_eleve.html")
# ---------------------------------------------------------------------------------
# ------------ESPACE ADMIN ------------ هنايا متقيسوهش ❗️
# ---------------------------------------------------------------------------------
@app.route("/admin/dashboard") # (Vérifie le nom exact de ta route)
def admin_dash():
    # On calcule les vrais chiffres
    total_eleves = compter_eleves()
    total_profs = compter_profs()
    total_absences = 0 # Temporaire, on l'automatisera plus tard !

    # On envoie tout ça au template
    return render_template("admin/dashboard_admin.html", 
                           total_eleves=total_eleves, 
                           total_profs=total_profs, 
                           total_absences=total_absences)
# --- ROUTES GESTION ADMIN ---

@app.route("/admin/eleves", methods=["GET", "POST"])
def gestion_eleves():
    if request.method == "POST":
        # Récupération depuis le formulaire HTML (sans le matricule)
        nom = request.form.get("nom")
        prenom = request.form.get("prenom")
        date_naissance = request.form.get("date_naissance")
        sexe = request.form.get("sexe")
        adresse = request.form.get("adresse")
        classe = request.form.get("classe")
        email = request.form.get("email")
        password = request.form.get("password")
        nom_tuteur = request.form.get("nom_tuteur")
        tel_tuteur = request.form.get("tel_tuteur")
        
        # Envoi à la base de données
        ajouter_eleve(nom, prenom, date_naissance, sexe, adresse, classe, email, password, nom_tuteur, tel_tuteur)
        
        # Recharge la page pour vider le formulaire
        return redirect(url_for("gestion_eleves"))
        # On récupère la liste de tous les élèves depuis la base de données
    liste_eleves = get_tous_les_eleves()
    # On envoie cette liste à notre fichier HTML (la variable s'appellera 'eleves')
    return render_template("admin/gestion_eleves.html", eleves=liste_eleves)
@app.route("/admin/eleves/supprimer/<int:id>")
def supprimer_eleve(id):
    # On appelle la fonction de la base de données avec l'ID
    supprimer_ele(id)
    # On redirige vers la page de gestion des élèves
    return redirect(url_for("gestion_eleves"))
@app.route("/admin/eleves/modifier/<int:id>", methods=["GET", "POST"])
def modifier_eleve(id):
    # Si l'utilisateur clique sur "Enregistrer les modifications"
    if request.method == "POST":
        nom = request.form.get("nom")
        prenom = request.form.get("prenom")
        date_naissance = request.form.get("date_naissance")
        sexe = request.form.get("sexe")
        adresse = request.form.get("adresse")
        classe = request.form.get("classe")
        email = request.form.get("email")
        password = request.form.get("password")
        nom_tuteur = request.form.get("nom_tuteur")
        tel_tuteur = request.form.get("tel_tuteur")
        
        if modifier_eleve_db(id, nom, prenom, date_naissance, sexe, adresse, classe, email, password, nom_tuteur, tel_tuteur):
            return redirect(url_for("gestion_eleves"))

    # Si on arrive juste sur la page, on récupère les infos actuelles
    eleve = get_eleve_by_id(id)
    return render_template("admin/modifier_eleve.html", eleve=eleve)


@app.route("/admin/profs", methods=["GET", "POST"])
def gestion_profs():
    if request.method == "POST":
        # Récupération depuis le formulaire HTML (sans le matricule)
        nom = request.form.get("nom")
        prenom = request.form.get("prenom")
        date_naissance = request.form.get("date_naissance")
        sexe = request.form.get("sexe")
        adresse = request.form.get("adresse")
        matiere = request.form.get("matiere")
        email = request.form.get("email")
        telephone = request.form.get("telephone")
        mot_de_passe = request.form.get("mot_de_passe")
        
        # Envoi à la base de données
        ajouter_prof(nom, prenom, date_naissance, sexe, adresse, matiere, email, telephone, mot_de_passe)
        
        # Recharge la page pour vider le formulaire
        return redirect(url_for("gestion_profs"))
        # On récupère la liste de tous les élèves depuis la base de données
    liste_profs = get_tous_les_profs()
    # On envoie cette liste à notre fichier HTML (la variable s'appellera 'eleves')
    return render_template("admin/gestion_profs.html", profs=liste_profs)
@app.route("/admin/profs/supprimer/<int:id>")
def supprimer_prof(id):
    # On appelle la fonction de la base de données avec l'ID
    supprimer_pr(id)
    # On redirige vers la page de gestion des professeurs
    return redirect(url_for("gestion_profs"))
@app.route("/admin/profs/modifier/<int:id>", methods=["GET", "POST"])
def modifier_prof(id):
    # Si l'utilisateur clique sur "Enregistrer les modifications"
    if request.method == "POST":
        nom = request.form.get("nom")
        prenom = request.form.get("prenom")
        date_naissance = request.form.get("date_naissance")
        sexe = request.form.get("sexe")
        adresse = request.form.get("adresse")
        matiere = request.form.get("matiere")
        email = request.form.get("email")
        telephone = request.form.get("telephone")
        mot_de_passe = request.form.get("mot_de_passe")
        nom_tuteur = request.form.get("nom_tuteur")
        tel_tuteur = request.form.get("tel_tuteur")
        
        if modifier_prof_db(id, nom, prenom, date_naissance, sexe, adresse, matiere, email, telephone, mot_de_passe):
            return redirect(url_for("gestion_profs"))

    # Si on arrive juste sur la page, on récupère les infos actuelles
    prof = get_prof_by_id(id)
    return render_template("admin/modifier_prof.html", prof=prof)


@app.route("/admin/absences")
def gestion_absences():
    return render_template("admin/gestion_absences.html")
# -----------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
