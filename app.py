from flask import Flask, request, render_template, redirect, url_for, session, flash
from database import enregistrer_absence, enregistrer_notes_completes, get_affectations_professeur, get_eleves_par_classe, get_infos_professeur, get_infos_selection, get_notes_existantes, sauvegarder_note_individuelle, supprimer_notes_eleve, supprimer_notes_eleve, supprimer_notes_eleve, get_user_by_id, update_profil_prof
from python.database import *
import os
from dotenv import load_dotenv
from flask import jsonify
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()
app = Flask(__name__)
app.secret_key = os.urandom(24)
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Si la personne n'est pas connectée OU si elle n'est pas 'admin'
        if 'user_id' not in session or session.get('role') != 'admin':
            # On la renvoie vers TA page de login principale
            return redirect(url_for('main_function'))
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'eleve':
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
    password = request.form.get("mot_de_passe")
    
    eleve_id = check_etudiant(email, password)
    if eleve_id:
        # Si c'est bon, on sauvegarde l'ID et le rôle dans la session
        session['user_id'] = eleve_id
        session['role'] = 'eleve'
        return redirect(url_for("eleve_dash"))
    else:
        # Si c'est faux, on recharge la page login avec un message d'erreur
        return render_template("login.html", error="Identifiants Élève incorrects")

@app.route("/login/professeur", methods=["POST"])
def login_professeur():
    email = request.form.get("email")
    mot_de_passe = request.form.get("mot_de_passe")
    
    prof = check_professeur(email, mot_de_passe)
    
    if prof:
        session['user_id'] = prof['id']
        # ICI : On enregistre le prénom récupéré en base (ex: 'Ahmed' ou 'Fatima')
        session['prenom'] = prof['prenom'] 
        session['role'] = 'professeur'
        return redirect(url_for("prof_dash"))
    
    return render_template("login.html", error="Identifiants incorrects")

@app.route("/prof/dashboard")
def prof_dash():
    if session.get('role') != 'professeur':
        return redirect(url_for("index"))
    
    # On récupère le nom stocké dans la session
    nom_utilisateur = session.get('nom') 
    
    # On l'envoie au fichier HTML
    return render_template("dashboard_prof.html", nom=nom_utilisateur)


@app.route("/prof/saisir_notes")
def saisir_notes():
    user_id = session.get('user_id')
    
    # On récupère les vraies classes depuis la base
    liste_affectations = get_affectations_professeur(user_id)
    
    # On récupère l'ID choisi ou le premier de la liste
    cm_id = request.args.get('classe_matiere_id')
    if not cm_id and liste_affectations:
        cm_id = liste_affectations[0]['id']

    if cm_id:
        # On va chercher les vrais élèves pour cette classe
        donnees = get_infos_selection(cm_id)
        eleves = get_eleves_par_classe(donnees['classe_id'])
        notes_anciennes = get_notes_existantes(cm_id)
        
        return render_template("saisie_notes.html", 
                               eleves=eleves, 
                               nom_classe=donnees['nom_classe'], 
                               nom_matiere=donnees['nom_matiere'],
                               notes_existantes=notes_anciennes,
                               liste_affectations=liste_affectations,
                               cm_id=cm_id)
    
    return "Aucune classe trouvée. Vérifiez la table classe_matiere."

@app.route("/prof/valider-notes", methods=["POST"])
def valider_notes():
    user_id = session.get('user_id') # On récupère l'ID du prof connecté
    cm_id = request.form.get('cm_id')
    
    # 1. RÉCUPÉRATION DES DONNÉES DE BASE
    donnees = get_infos_selection(cm_id)
    eleves = get_eleves_par_classe(donnees['classe_id'])
    
    # AJOUT ICI : On récupère la liste pour que le menu de changement de classe revienne
    liste_affectations = get_affectations_professeur(user_id)

    # 2. TRAITEMENT ET SAUVEGARDE DES NOTES
    ids_eleves = set(key.split("_")[1] for key in request.form.keys() if "_" in key)
    for e_id in ids_eleves:
        for i in range(1, 5):
            valeur = request.form.get(f"cc{i}_{e_id}")
            if valeur and valeur.strip() != "":
                sauvegarder_note_individuelle(
                    eleve_id=e_id,
                    classe_matiere_id=cm_id,
                    valeur=float(valeur),
                    type_eval=f'cc{i}' # On utilise cc1, cc2, etc. pour correspondre à ton dictionnaire
                )

    # 3. RÉCUPÉRATION DES NOTES MISES À JOUR
    notes_existantes =get_notes_existantes(cm_id)

    # 4. AFFICHAGE (On ajoute liste_affectations dans le retour)
    return render_template("saisie_notes.html", 
                           eleves=eleves, 
                           notes_existantes=notes_existantes,
                           nom_classe=donnees['nom_classe'], 
                           nom_matiere=donnees['nom_matiere'],
                           liste_affectations=liste_affectations, # <--- C'est cette ligne qui fait réapparaître le menu !
                           cm_id=cm_id,
                           success="Notes enregistrées avec succès !")

@app.route("/prof/profil")
def mon_profil():
    if 'user_id' not in session:
        return redirect(url_for("index"))
    
    # On récupère les infos actuelles pour les afficher dans le formulaire
    user = get_user_by_id(session['user_id']) 
    return render_template("profil.html", user=user)

@app.route("/prof/update-profil", methods=["POST"])
def update_profil():
    prenom = request.form.get("prenom")
    nom = request.form.get("nom")
    mdp = request.form.get("mot_de_passe")
    
    if update_profil_prof(session['user_id'], prenom, nom, mdp if mdp else None):
        session['prenom'] = prenom # On met à jour le prénom dans la session
        flash("Profil mis à jour avec succès !", "success")
    else:
        flash("Erreur lors de la mise à jour.", "danger")
        
    return redirect(url_for("mon_profil"))

@app.route('/prof/absences')
def faire_appel():
    user_id = session.get('user_id')
    
    # 1. RÉCUPÉRATION : Est-ce que cette variable contient des données ?
    mes_classes = get_affectations_professeur(user_id) 
    
    classe_id = request.args.get('classe_id', type=int)
    eleves = []
    if classe_id:
        eleves = get_eleves_par_classe(classe_id)
    
    # 2. ENVOI : Vérifie que tu as bien écrit 'classes=mes_classes'
    return render_template('appel.html', 
                           eleves=eleves, 
                           classes=mes_classes, # <--- C'est le nom utilisé par le {% for %}
                           classe_actuelle=classe_id)

@app.route("/prof/valider-appel", methods=["POST"])
def valider_appel():
    # 1. Récupérer les infos globales du formulaire
    classe_id = request.form.get("classe_id")
    date_jour = request.form.get("date_appel")
    classe_id = request.form.get("classe_id") # On doit l'ajouter en hidden dans le HTML

    if not classe_id:
        flash("Erreur : Classe non identifiée.", "danger")
        return redirect(url_for("faire_appel"))

    # 2. Récupérer les élèves de CETTE classe uniquement
    eleves = get_eleves_par_classe(int(classe_id))
    
    for eleve in eleves:
        # On récupère le statut (Présent/Absent) envoyé par les boutons radio
        statut = request.form.get(f"statut_{eleve.id}")
        # On récupère la justification si elle existe
        justification = request.form.get(f"justification_{eleve.id}", "Non justifiée")
        
    if statut == 'Absent':
        enregistrer_absence(
            eleve_id=eleve.id,
            date_abs=date_jour,
            statut=statut,
            justification=justification
        )
    
    flash("L'appel a été enregistré avec succès !", "success")
    return redirect(url_for("prof_dash"))

@app.route("/prof/supprimer_note/<int:eleve_id>")
def supprimer_note(eleve_id):
    prof_id = session.get('user_id')
    infos = get_infos_professeur(prof_id)
    if supprimer_notes_eleve(eleve_id, infos['nom_matiere']):
        flash("Note supprimée", "success")
    return redirect(url_for("saisir_notes"))
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
        mot_de_passe=generate_password_hash(mot_de_passe)
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
    liste_notes = get_notes_by_eleve(id_eleve=id)
    
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
        mot_de_passe=generate_password_hash(mot_de_passe)
        
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
@app.route("/admin/bulletins", methods=["GET", "POST"])
@admin_required
def interface_bulletins():
    # 1. Récupérer toutes les classes pour remplir la liste déroulante
    # Assure-toi d'avoir une fonction get_toutes_les_classes() dans database.py
    classes = get_toutes_les_classes() 
    
    eleves = []
    classe_selectionnee = None
    semestre_selectionne = "S1" # Par défaut

    # 2. Si l'admin a cliqué sur "Chercher"
    if request.method == "POST":
        classe_selectionnee = request.form.get("classe_id")
        semestre_selectionne = request.form.get("semestre")
        
        if classe_selectionnee:
            # Récupérer les élèves de CETTE classe spécifique
            # Assure-toi d'avoir une fonction get_eleves_by_classe(classe_id)
            eleves = get_eleves_by_classe(classe_selectionnee)

    return render_template("admin/interface_bulletins.html", 
                           classes=classes, 
                           eleves=eleves, 
                           classe_selec=classe_selectionnee, 
                           semestre_selec=semestre_selectionne)
# -----------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------
#------------------------------------------------------------------------------------

#------------------------------------------------------------------------------------
#------------------------------------STUDENTS PART-----------------------------------
#------------------------------------------------------------------------------------

@app.route("/eleve/dashboard")
@student_required
def eleve_dash():
    eleve_id = session.get('user_id')
    eleve = get_eleve_by_id(eleve_id)
    notes = get_notes_by_eleve(eleve_id)
    absences = get_absences_by_eleve(eleve_id)
    
    recent_notes = notes[:5]
    recent_absences = absences[:5]
    total_absences = sum(1 for a in absences if not a.justifiee)
    
    total_points = sum(note['note'] for note in notes)
    moyenne = round(total_points / len(notes), 2) if notes else "N/A"

    return render_template("student/dashboard_eleve.html", eleve=eleve, notes=recent_notes, absences=recent_absences, total_absences=total_absences, moyenne=moyenne)

@app.route("/eleve/notes")
@student_required
def eleve_notes():
    eleve_id = session.get('user_id')
    notes = get_notes_by_eleve(eleve_id)
    return render_template("student/notes.html", notes=notes)

@app.route("/eleve/absences")
@student_required
def eleve_absences():
    eleve_id = session.get('user_id')
    absences = get_absences_by_eleve(eleve_id)
    return render_template("student/absences.html", absences=absences)

@app.route("/eleve/profil")
@student_required
def eleve_profil():
    eleve_id = session.get('user_id')
    eleve = get_eleve_by_id(eleve_id)
    return render_template("student/profil.html", eleve=eleve)

#------------------------------------------------------------------------------------

#------------------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
