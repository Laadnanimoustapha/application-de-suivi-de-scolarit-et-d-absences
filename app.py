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
    
    # On récupère le nom stocké dans la session
    nom_utilisateur = session.get('nom') 
    
    # On l'envoie au fichier HTML
    return render_template("dashboard_prof.html", nom=nom_utilisateur)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/prof/saisir-notes")
def saisie_notes_page():
    if session.get('role') != 'professeur':
        return redirect(url_for("index"))
    
    # On récupère la matière (SVT par défaut pour le test)
    matiere = session.get('matiere', 'SVT')
    
    # 1. On récupère la liste des élèves (Classe ID 1)
    eleves = db.get_eleves_par_classe(1) 
    
    # 2. On récupère les notes déjà enregistrées dans MySQL
    # On utilise la fonction de lecture (il faut la créer dans database.py)
    notes_existantes = db.get_notes_existantes(matiere)
    
    # 3. On envoie les deux listes au template HTML
    return render_template("saisie_notes.html", eleves=eleves, notes_db=notes_existantes)

@app.route("/prof/valider-notes", methods=["POST"])
def valider_notes():
    matiere = session.get('matiere', 'SVT')
    ids_eleves = set(key.split("_")[1] for key in request.form.keys() if "_" in key)

    for e_id in ids_eleves:
        c1 = request.form.get(f"cc1_{e_id}")
        c2 = request.form.get(f"cc2_{e_id}")
        ex = request.form.get(f"exam_{e_id}")
        
        if c1 or c2 or ex:
            val_c1 = float(c1 or 0)
            val_c2 = float(c2 or 0)
            val_ex = float(ex or 0)
            moy = (val_c1 * 0.25) + (val_c2 * 0.25) + (val_ex * 0.50)
            db.enregistrer_notes_completes(e_id, matiere, val_c1, val_c2, val_ex, moy)

    # Cette ligne doit être alignée parfaitement sous le "for"
    flash("Les notes ont été enregistrées avec succès !", "success")
    return redirect(url_for("prof_dash"))

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

@app.route("/prof/absences") 
def faire_appel():
    if session.get('role') != 'professeur':
        return redirect(url_for("index"))
    
    # On récupère les élèves de la classe 1
    eleves = db.get_eleves_par_classe(1) 
    return render_template("appel.html", eleves=eleves)

@app.route("/prof/valider-appel", methods=["POST"])
def valider_appel():
    date_jour = request.form.get("date_appel")
    seance = request.form.get("seance")
    
    eleves = db.get_eleves_par_classe(1)
    for eleve in eleves:
        # On récupère le statut et la justification
        statut = request.form.get(f"statut_{eleve.id}")
        justification = request.form.get(f"justification_{eleve.id}", "Non justifiée")
        
        # Enregistrement dans la table "absence"
        db.enregistrer_absence(eleve.id, date_jour, seance, statut, justification)
    
    flash("L'appel a été enregistré avec succès !", "success")
    return redirect(url_for("prof_dash"))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)