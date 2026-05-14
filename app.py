from flask import Flask, render_template, request, redirect, url_for, session , flash
import database as db

app = Flask(__name__)
app.secret_key = 'votre_cle_secrete_pfe_2026'

@app.route("/")
def index():
    return render_template("login.html")

@app.route("/login/professeur", methods=["POST"])
def login_professeur():
    email = request.form.get("email")
    mot_de_passe = request.form.get("mot_de_passe")
    
    prof = db.check_professeur(email, mot_de_passe)
    
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
    
    # On récupère 'prenom' car c'est ce qu'on a mis en session au login
    nom_utilisateur = session.get('prenom') 
    
    return render_template("dashboard_prof.html", nom=nom_utilisateur)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/prof/saisir_notes")
def saisir_notes():
    user_id = session.get('user_id')
    
    # On récupère les vraies classes depuis la base
    liste_affectations = db.get_affectations_professeur(user_id)
    
    # On récupère l'ID choisi ou le premier de la liste
    cm_id = request.args.get('classe_matiere_id')
    if not cm_id and liste_affectations:
        cm_id = liste_affectations[0]['id']

    if cm_id:
        # On va chercher les vrais élèves pour cette classe
        donnees = db.get_infos_selection(cm_id)
        eleves = db.get_eleves_par_classe(donnees['classe_id'])
        notes_anciennes = db.get_notes_existantes(cm_id)
        
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
    donnees = db.get_infos_selection(cm_id)
    eleves = db.get_eleves_par_classe(donnees['classe_id'])
    
    # AJOUT ICI : On récupère la liste pour que le menu de changement de classe revienne
    liste_affectations = db.get_affectations_professeur(user_id)

    # 2. TRAITEMENT ET SAUVEGARDE DES NOTES
    ids_eleves = set(key.split("_")[1] for key in request.form.keys() if "_" in key)
    for e_id in ids_eleves:
        for i in range(1, 5):
            valeur = request.form.get(f"cc{i}_{e_id}")
            if valeur and valeur.strip() != "":
                db.sauvegarder_note_individuelle(
                    eleve_id=e_id,
                    classe_matiere_id=cm_id,
                    valeur=float(valeur),
                    type_eval=f'cc{i}' # On utilise cc1, cc2, etc. pour correspondre à ton dictionnaire
                )

    # 3. RÉCUPÉRATION DES NOTES MISES À JOUR
    notes_existantes = db.get_notes_existantes(cm_id)

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
    user = db.get_user_by_id(session['user_id']) 
    return render_template("profil.html", user=user)

@app.route("/prof/update-profil", methods=["POST"])
def update_profil():
    prenom = request.form.get("prenom")
    nom = request.form.get("nom")
    mdp = request.form.get("mot_de_passe")
    
    if db.update_profil_prof(session['user_id'], prenom, nom, mdp if mdp else None):
        session['prenom'] = prenom # On met à jour le prénom dans la session
        flash("Profil mis à jour avec succès !", "success")
    else:
        flash("Erreur lors de la mise à jour.", "danger")
        
    return redirect(url_for("mon_profil"))

@app.route('/prof/absences')
def faire_appel():
    user_id = session.get('user_id')
    
    # 1. RÉCUPÉRATION : Est-ce que cette variable contient des données ?
    mes_classes = db.get_affectations_professeur(user_id) 
    
    classe_id = request.args.get('classe_id', type=int)
    eleves = []
    if classe_id:
        eleves = db.get_eleves_par_classe(classe_id)
    
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
    eleves = db.get_eleves_par_classe(int(classe_id))
    
    for eleve in eleves:
        # On récupère le statut (Présent/Absent) envoyé par les boutons radio
        statut = request.form.get(f"statut_{eleve.id}")
        # On récupère la justification si elle existe
        justification = request.form.get(f"justification_{eleve.id}", "Non justifiée")
        
    if statut == 'Absent':
        db.enregistrer_absence(
            eleve_id=eleve_id,
            date_abs=date_jour,
            statut=statut,
            justification=justification
        )
    
    flash("L'appel a été enregistré avec succès !", "success")
    return redirect(url_for("prof_dash"))

@app.route("/prof/supprimer_note/<int:eleve_id>")
def supprimer_note(eleve_id):
    prof_id = session.get('user_id')
    infos = db.get_infos_professeur(prof_id)
    if db.supprimer_notes_eleve(eleve_id, infos['nom_matiere']):
        flash("Note supprimée", "success")
    return redirect(url_for("saisir_notes"))
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)