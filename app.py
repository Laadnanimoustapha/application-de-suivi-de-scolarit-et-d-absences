from flask import Flask, request, render_template, redirect, url_for
from python.database import check_etudiant, check_professeur, check_admin, ajouter_eleve,get_tous_les_eleves,generer_numero_eleve,supprimer_ele,get_eleve_by_id, modifier_eleve_db, ajouter_prof, get_tous_les_profs, supprimer_pr
from python.database import supprimer_pr, get_prof_by_id,get_notes_by_eleve,get_note_by_id,modifier_note_db, modifier_prof_db
from python.database import compter_eleves, compter_profs
import random
from datetime import datetime
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
        email = request.form.get("email")
        mot_de_passe = request.form.get("mot_de_passe")
        
        if check_admin(email, mot_de_passe):
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
        # Récupération des nouveaux champs
        sexe = request.form.get("sexe")
        adresse = request.form.get("adresse")
        
        # Les autres champs habituels
        nom = request.form.get("nom")
        prenom = request.form.get("prenom")
        email = request.form.get("email")
        mot_de_passe = request.form.get("mot_de_passe")
        classe_id = request.form.get("classe_id")
        date_naissance = request.form.get("date_naissance")
        nom_tuteur = request.form.get("nom_tuteur")
        tel_tuteur = request.form.get("tel_tuteur")
        numero_eleve = generer_numero_eleve()
        ajouter_eleve(nom, prenom, sexe, email, adresse, mot_de_passe, classe_id, numero_eleve, date_naissance, nom_tuteur, tel_tuteur)
        return redirect(url_for("gestion_eleves"))
    
    return render_template("admin/gestion_eleves.html", eleves=get_tous_les_eleves())
@app.route("/admin/eleves/supprimer/<int:id>")
def supprimer_eleve(id):
    # On appelle la fonction de la base de données avec l'ID
    supprimer_ele(id)
    # On redirige vers la page de gestion des élèves
    return redirect(url_for("gestion_eleves"))
@app.route("/admin/eleves/modifier/<int:id>", methods=["GET", "POST"])
def route_modifier_eleve(id):
    if request.method == "POST":
        # On récupère tous les champs du formulaire de modification
        nom = request.form.get("nom")
        prenom = request.form.get("prenom")
        sexe = request.form.get("sexe")
        adresse = request.form.get("adresse")
        email = request.form.get("email")
        mot_de_passe = request.form.get("mot_de_passe")
        
        classe_id = request.form.get("classe_id")
        date_naissance = request.form.get("date_naissance")
        nom_tuteur = request.form.get("nom_tuteur")
        tel_tuteur = request.form.get("tel_tuteur")
        
        # On appelle notre nouvelle fonction à deux têtes !
        modifier_eleve_db(id, nom, prenom, sexe, adresse, email, mot_de_passe, classe_id, date_naissance, nom_tuteur, tel_tuteur)
        
        return redirect(url_for("gestion_eleves"))
    
    # Si c'est un GET, on va chercher les infos pour remplir les cases
    eleve = get_eleve_by_id(id)
    return render_template("admin/modifier_eleve.html", eleve=eleve)
@app.route("/admin/eleves/<int:id>/notes")
def consulter_notes_eleve(id):
    # 1. On récupère les infos de l'élève
    eleve = get_eleve_by_id(id)
    
    # 2. On récupère ses notes
    liste_notes = get_notes_by_eleve(id)
    
    # 3. On affiche la page
    return render_template("admin/consulter_notes.html", eleve=eleve, notes=liste_notes)
@app.route("/admin/notes/modifier/<int:id>", methods=["GET", "POST"])
def route_modifier_note(id):
    # 1. On récupère la note actuelle pour savoir de quel élève il s'agit
    note_actuelle = get_note_by_id(id)
    
    if request.method == "POST":
        valeur = request.form.get("valeur")
        type_eval = request.form.get("type_evaluation")
        semestre = request.form.get("semestre")
        
        if modifier_note_db(id, valeur, type_eval, semestre):
            # On redirige vers la page des notes de l'élève
            return redirect(url_for('consulter_notes_eleve', id=note_actuelle['eleve_id']))
    
    return render_template("admin/modifier_note.html", note=note_actuelle)
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
