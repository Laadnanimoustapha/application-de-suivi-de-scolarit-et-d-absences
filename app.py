from flask import Flask, request, render_template, redirect, url_for, session, flash
from python.database import (check_etudiant, check_professeur, check_admin, ajouter_eleve, get_eleves_sans_classe,affecter_eleve_db,get_tous_les_eleves,
                             generer_numero_eleve,supprimer_ele,get_eleve_by_id, modifier_eleve_db, ajouter_prof,
                               get_tous_les_profs, supprimer_pr,supprimer_pr, get_prof_by_id,get_notes_by_eleve,
                               get_note_by_id,modifier_note_db, modifier_prof_db,compter_eleves, get_nombre_eleves_classe,
                               ajouter_classe_db,supprimer_classe_db,compter_profs,get_toutes_les_matieres,get_eleves_by_classe,
                                 get_classe_by_id,get_absences_non_justifiees,justifier_absence_db, update_configuration,get_configuration_actuelle,get_toutes_les_classes,ajouter_assignation_db,get_toutes_les_assignations,get_profs_par_classe,get_dernier_coefficient)
import os
from dotenv import load_dotenv
from flask import jsonify
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Si la personne n'est pas connectée OU si elle n'est pas 'admin'
        if 'user_id' not in session or session.get('role') != 'admin':
            # On la renvoie vers TA page de login principale
            return redirect(url_for('main_function'))
        return f(*args, **kwargs)
    return decorated_function
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
            # 🌟 ICI : ON DONNE LE BADGE (SESSION) À L'ADMIN 🌟
            session['user_id'] = email  # On garde l'email en mémoire
            session['role'] = 'admin'   # TRÈS IMPORTANT : c'est ça qui ouvre la douane !
            
            return redirect(url_for("admin_dash"))
        else:
            return render_template("login.html", error="Identifiants Administrateur incorrects")

    except Exception as e:
        # S'il y a une erreur avec la base de données...
        return f"<h1>ERREUR TROUVÉE :</h1> <p>{str(e)}</p>"
@app.route("/logout")
def logout():
    # On vide la mémoire (on détruit le badge de la session)
    session.clear()
    
    # On redirige l'utilisateur vers TA page principale
    return redirect(url_for("main_function"))
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
@admin_required
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
@admin_required
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
        date_naissance = request.form.get("date_naissance")
        nom_tuteur = request.form.get("nom_tuteur")
        tel_tuteur = request.form.get("tel_tuteur")
        numero_eleve = generer_numero_eleve()
        ajouter_eleve(nom, prenom, sexe, email, adresse, mot_de_passe, numero_eleve, date_naissance, nom_tuteur, tel_tuteur)
        return redirect(url_for("gestion_eleves"))
        
    return render_template("admin/gestion_eleves.html", eleves=get_tous_les_eleves())
@app.route("/admin/eleves/supprimer/<int:id>")
@admin_required
def supprimer_eleve(id):
    # On appelle la fonction de la base de données avec l'ID
    supprimer_ele(id)
    # On redirige vers la page de gestion des élèves
    return redirect(url_for("gestion_eleves"))
@app.route("/admin/eleves/modifier/<int:id>", methods=["GET", "POST"])
@admin_required
def route_modifier_eleve(id):
    if request.method == "POST":
        nom = request.form.get("nom")
        prenom = request.form.get("prenom")
        date_naissance = request.form.get("date_naissance")
        sexe = request.form.get("sexe")
        adresse = request.form.get("adresse")
        email = request.form.get("email")
        nom_tuteur = request.form.get("nom_tuteur")
        tel_tuteur = request.form.get("tel_tuteur")
        
        # 1. On récupère le mot de passe tapé
        nouveau_mdp = request.form.get("mot_de_passe")
        
        # 2. On vérifie s'il est vide
        if nouveau_mdp and nouveau_mdp.strip() != "":
            # Si l'admin a tapé un truc, on le hache (sécurité)
            mdp_hash = generate_password_hash(nouveau_mdp)
        else:
            # S'il est vide, on le met à None pour dire "Ne pas modifier"
            mdp_hash = None
            
        # 3. On appelle la fonction de mise à jour
        modifier_eleve_db(id, nom, prenom, date_naissance, sexe, adresse, email, nom_tuteur, tel_tuteur, mdp_hash)
        
        flash("✅ Les informations de l'élève ont été mises à jour.", "success")
        return redirect(url_for("gestion_eleves")) # Ou la page où tu veux rediriger
    # Si c'est un GET, on va chercher les infos pour remplir les cases
    eleve = get_eleve_by_id(id)
    return render_template("admin/modifier_eleve.html", eleve=eleve)
@app.route("/admin/eleves/<int:id>/notes")
@admin_required
def consulter_notes_eleve(id):
    # 1. On récupère les infos de l'élève
    eleve = get_eleve_by_id(id)
    
    # 2. On récupère ses notes
    liste_notes = get_notes_by_eleve(id)
    
    # 3. On affiche la page
    return render_template("admin/consulter_notes.html", eleve=eleve, notes=liste_notes)
@app.route("/admin/notes/modifier/<int:id>", methods=["GET", "POST"])
@admin_required
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
@admin_required
def gestion_profs():
    if request.method == "POST":
        # Infos générales
        nom = request.form.get("nom")
        prenom = request.form.get("prenom")
        sexe = request.form.get("sexe")
        email = request.form.get("email")
        adresse = request.form.get("adresse")
        mot_de_passe = request.form.get("mot_de_passe")
        
        # Nouvelles infos : Matière et Classe        
        # Appel de la fonction mise à jour
        ajouter_prof(nom, prenom, sexe, email, adresse, mot_de_passe)
        
        return redirect(url_for("gestion_profs"))

    # Pour l'affichage de la page (GET)
    liste_profs = get_tous_les_profs()
    liste_matieres = get_toutes_les_matieres() # Récupère la liste des matières
    liste_classes = get_toutes_les_classes()   # Récupère la liste des classes
    
    return render_template(
        "admin/gestion_profs.html", 
        profs=liste_profs, 
        matieres=liste_matieres, 
        classes=liste_classes
    )
@app.route("/admin/profs/supprimer/<int:id>")
@admin_required
def supprimer_prof(id):
    # On appelle la fonction de la base de données avec l'ID
    supprimer_pr(id)
    # On redirige vers la page de gestion des professeurs
    return redirect(url_for("gestion_profs"))
@app.route("/admin/profs/modifier/<int:id>", methods=["GET", "POST"])
@admin_required
def modifier_prof(id):
    # Si l'utilisateur clique sur "Enregistrer les modifications"

    if request.method == "POST":
        # Infos générales
        nom = request.form.get("nom")
        prenom = request.form.get("prenom")
        sexe = request.form.get("sexe")
        email = request.form.get("email")
        adresse = request.form.get("adresse")
        mot_de_passe = request.form.get("mot_de_passe")
        
        #         # On sauvegarde tout
        modifier_prof_db(id, nom, prenom, sexe, email, adresse, mot_de_passe)
        return redirect(url_for("gestion_profs"))

    # Pour l'affichage de la page de modification
    prof = get_prof_by_id(id)
    if not prof:
        return redirect(url_for("gestion_profs"))
        
    matieres = get_toutes_les_matieres()
    classes = get_toutes_les_classes()
        
    return render_template("admin/modifier_prof.html", prof=prof, matieres=matieres, classes=classes)
@app.route("/admin/classes", methods=["GET", "POST"])
@admin_required
def gestion_classes():
    if request.method == "POST":
        nom = request.form.get("nom")
        niveau = request.form.get("niveau")
        filiere = request.form.get("filiere")
        annee_academique = request.form.get("annee_academique")
        
        # On vérifie que toutes les données sont bien là
        if nom and niveau and filiere and annee_academique:
            ajouter_classe_db(nom, niveau, filiere, annee_academique)
            
        return redirect(url_for("gestion_classes"))

    classes = get_toutes_les_classes()
    return render_template("admin/gestion_classes.html", classes=classes)
@app.route("/admin/classes/<int:id>/details") # On peut renommer la route en /details
@admin_required
def details_classe(id):
    classe = get_classe_by_id(id)
    if not classe:
        return redirect(url_for('gestion_classes'))
    
    # On récupère les deux listes
    eleves = get_eleves_by_classe(id)
    professeurs = get_profs_par_classe(id)
    
    return render_template("admin/eleves_classe.html", 
                           classe=classe, 
                           eleves=eleves, 
                           profs=professeurs)
@app.route("/admin/classes/supprimer/<int:id>", methods=["POST"])
@admin_required
def supprimer_classe(id):
    supprimer_classe_db(id)
    return redirect(url_for("gestion_classes"))
# --- ROUTE PRINCIPALE ---
@app.route("/admin/assignations", methods=["GET", "POST"])
@admin_required
def gestion_assignations():
    if request.method == "POST":
        classe_id = request.form.get("classe_id")
        matiere_id = request.form.get("matiere_id")
        prof_id = request.form.get("professeur_id")
        coefficient = request.form.get("coefficient")

        if classe_id and matiere_id and prof_id and coefficient:
            ajouter_assignation_db(classe_id, matiere_id, prof_id, coefficient)
        
        return redirect(url_for("gestion_assignations"))

    # Pour le mode GET : on récupère tout ce qu'il faut pour remplir les listes
    classes = get_toutes_les_classes()
    matieres = get_toutes_les_matieres() # Assure-toi d'avoir cette fonction
    profs = get_tous_les_profs()
    assignations = get_toutes_les_assignations()

    return render_template("admin/assignations.html", 
                           classes=classes, matieres=matieres, 
                           profs=profs, assignations=assignations)
@app.route("/admin/affectation_eleves", methods=["GET", "POST"])
@admin_required
def affectation_eleves():
    if request.method == "POST":
        eleve_id = request.form.get("eleve_id")
        classe_id = request.form.get("classe_id")

        if eleve_id and classe_id:
            # 1. On vérifie le nombre d'élèves actuels
            nombre_actuel = get_nombre_eleves_classe(classe_id)
            
            # 2. Règle stricte des 10 élèves
            if nombre_actuel >= 10:
                flash("❌ Impossible : Cette classe est déjà complète (10/10).", "danger")
            else:
                # 3. On affecte l'élève
                success = affecter_eleve_db(eleve_id, classe_id)
                if success:
                    flash("✅ L'élève a été affecté avec succès !", "success")
                else:
                    flash("❌ Une erreur s'est produite lors de l'affectation.", "danger")
                    
        return redirect(url_for("affectation_eleves"))

    # Mode GET : on prépare les listes pour le formulaire
    classes = get_toutes_les_classes()
    eleves_dispos = get_eleves_sans_classe()
    
    return render_template("admin/affectation_eleves.html", classes=classes, eleves=eleves_dispos)

# --- ROUTE API (Pour le Smart Defaulting) ---
@app.route("/api/coefficient/<filiere>/<int:matiere_id>")
@admin_required
def api_get_coefficient(filiere, matiere_id):
    coef = get_dernier_coefficient(filiere, matiere_id)
    return jsonify({"coefficient": coef})
@app.route("/admin/absences", methods=["GET"])
@admin_required
def gestion_absences():
    # On récupère la liste des absences non justifiées
    absences = get_absences_non_justifiees()
    return render_template("admin/gestion_absences.html", absences=absences)

@app.route("/admin/absences/justifier", methods=["POST"])
@admin_required
def justifier_absence():
    absence_id = request.form.get("absence_id")
    motif = request.form.get("motif")
    
    if absence_id and motif:
        success = justifier_absence_db(absence_id, motif)
        if success:
            flash("✅ L'absence a été justifiée avec succès.", "success")
        else:
            flash("❌ Erreur lors de la mise à jour de l'absence.", "danger")
            
    return redirect(url_for("gestion_absences"))

@app.route("/admin/configuration", methods=["GET", "POST"])
@admin_required
def gestion_configuration():
    if request.method == "POST":
        nouvelle_annee = request.form.get("annee_academique")
        nouveau_semestre = request.form.get("semestre")
        
        if nouvelle_annee and nouveau_semestre:
            success = update_configuration(nouvelle_annee, nouveau_semestre)
            if success:
                flash("✅ Configuration mise à jour ! Le système est synchronisé.", "success")
            else:
                flash("❌ Erreur lors de la mise à jour.", "danger")
                
        return redirect(url_for("gestion_configuration"))

    config = get_configuration_actuelle()
    return render_template("admin/configuration.html", config=config)
# -----------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
