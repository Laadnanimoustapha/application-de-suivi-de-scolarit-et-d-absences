import os
from sqlalchemy import create_engine, text 
from dotenv import load_dotenv

load_dotenv()

DATABASE_KEY = os.getenv("DATABASE")

if not DATABASE_KEY:
    raise ValueError("The 'DATABASE' environment variable is not set. Please set it in your environment or in a .env file.")

if DATABASE_KEY.startswith("mysql://"):
    DATABASE_KEY = DATABASE_KEY.replace("mysql://", "mysql+mysqlconnector://", 1)

engine = create_engine(DATABASE_KEY, pool_pre_ping=True, pool_recycle=300)

def check_etudiant(email,password): # check if the student has an account 
    with engine.connect() as conn:
        query = text("SELECT * FROM etudiant WHERE email = :email AND password = :password")
        result = conn.execute(query,{"email" : email,"password" : password}).fetchone()

        return result is not None 


def check_professeur(email,password): # check if the profesor has an account 
    with engine.connect() as conn:
        query = text("SELECT * FROM professeur WHERE email = :email AND password = :password")
        result = conn.execute(query,{"email" : email,"password" : password}).fetchone()

        return result is not None 
#---------------------------------------------------------------------------------
# ------------ LES METHODES DE L'ESPACE ADMIN ------------ هنايا متقيسوهش ❗️
# ---------------------------------------------------------------------------------
def check_admin(username,password): # check if the admin has an account 
    with engine.connect() as conn:
        query = text("SELECT * FROM admin WHERE username = :username AND password = :password")
        result = conn.execute(query,{"username" : username,"password" : password}).fetchone()
        return result is not None 
#------------------------les fonctions de gestion des élèves------------------------
# fonction pour ajouter un élève à la base de données, elle sera utilisée dans le dashboard admin pour créer des comptes élèves
def ajouter_eleve(nom, prenom, date_naissance, sexe, adresse, classe, email, password, nom_tuteur, tel_tuteur):
    try:
        # On utilise "engine" exactement comme tu as fait pour check_admin
        with engine.connect() as conn:
            query = text("""
                INSERT INTO eleves 
                (nom, prenom, date_naissance, sexe, adresse, classe, email, mot_de_passe, nom_tuteur, tel_tuteur)
                VALUES (:nom, :prenom, :date_naissance, :sexe, :adresse, :classe, :email, :password, :nom_tuteur, :tel_tuteur)
            """)
            
            # On passe les variables sous forme de dictionnaire
            conn.execute(query, {
                "nom": nom,
                "prenom": prenom,
                "date_naissance": date_naissance,
                "sexe": sexe,
                "adresse": adresse,
                "classe": classe,
                "email": email,
                "password": password,
                "nom_tuteur": nom_tuteur,
                "tel_tuteur": tel_tuteur
            })
            
            conn.commit() # Très important pour sauvegarder les changements dans Aiven
            return True
            
    except Exception as e:
        print(f"Erreur lors de l'ajout de l'élève : {e}")
        return False
# fonction pour récupérer tous les élèves de la base de données, elle sera utilisée dans le dashboard admin pour afficher la liste des élèves
def get_tous_les_eleves():
    try:
        with engine.connect() as conn:
            # On sélectionne tout, ordonné par ID décroissant (les plus récents en premier)
            query = text("SELECT * FROM eleves ORDER BY id DESC")
            # fetchall() récupère toutes les lignes d'un coup
            resultats = conn.execute(query).mappings().fetchall() 
            return resultats
    except Exception as e:
        print(f"Erreur lors de la récupération des élèves : {e}")
        return [] # En cas d'erreur, on retourne une liste vide
# fonction pour supprimer un élève de la base de données, elle sera utilisée dans le dashboard admin pour supprimer un élève
def supprimer_ele(id_eleve):
    try:
        with engine.connect() as conn:
            # On cherche l'élève par son ID et on le supprime
            query = text("DELETE FROM eleves WHERE id = :id")
            conn.execute(query, {"id": id_eleve})
            conn.commit() # On valide la suppression dans Aiven
            return True
    except Exception as e:
        print(f"Erreur lors de la suppression de l'élève : {e}")
        return False
# fonction pour récupérer les informations d'un élève par son ID, elle sera utilisée dans le dashboard admin pour pré-remplir le formulaire de modification d'un élève 
def get_eleve_by_id(id_eleve):
    try:
        with engine.connect() as conn:
            query = text("SELECT * FROM eleves WHERE id = :id")
            resultat = conn.execute(query, {"id": id_eleve}).mappings().fetchone()
            return resultat
    except Exception as e:
        print(f"Erreur lors de la récupération de l'élève : {e}")
        return None
# fonction pour modifier les informations d'un élève dans la base de données, elle sera utilisée dans le dashboard admin pour modifier les informations d'un élève
def modifier_eleve_db(id_eleve, nom, prenom, date_naissance, sexe, adresse, classe, email, password, nom_tuteur, tel_tuteur):
    try:
        with engine.connect() as conn:
            query = text("""
                UPDATE eleves SET 
                nom=:nom, prenom=:prenom, date_naissance=:date_naissance, sexe=:sexe, 
                adresse=:adresse, classe=:classe, email=:email, mot_de_passe=:password, 
                nom_tuteur=:nom_tuteur, tel_tuteur=:tel_tuteur
                WHERE id = :id
            """)
            conn.execute(query, {
                "id": id_eleve, "nom": nom, "prenom": prenom, "date_naissance": date_naissance,
                "sexe": sexe, "adresse": adresse, "classe": classe, "email": email,
                "password": password, "nom_tuteur": nom_tuteur, "tel_tuteur": tel_tuteur
            })
            conn.commit()
            return True
    except Exception as e:
        print(f"Erreur lors de la modification : {e}")
        return False
#------------------------les fonctions de gestion des profs------------------------
# fonction pour ajouter un professeur à la base de données, elle sera utilisée dans le dashboard admin pour créer des comptes professeurs
def ajouter_prof(nom, prenom, date_naissance, sexe, adresse, matiere, email, telephone, mot_de_passe):
    try:
        # On utilise "engine" exactement comme tu as fait pour check_admin
        with engine.connect() as conn:
            query = text("""
                INSERT INTO professeurs 
                (nom, prenom, date_naissance, sexe, adresse, matiere, email, telephone, mot_de_passe)
                VALUES (:nom, :prenom, :date_naissance, :sexe, :adresse, :matiere, :email, :telephone, :mot_de_passe)
            """)
            
            # On passe les variables sous forme de dictionnaire
            conn.execute(query, {
                "nom": nom,
                "prenom": prenom,
                "date_naissance": date_naissance,
                "sexe": sexe,
                "adresse": adresse,
                "matiere": matiere,
                "email": email,
                "telephone": telephone,
                "mot_de_passe": mot_de_passe
            })
            
            conn.commit() # Très important pour sauvegarder les changements dans Aiven
            return True
            
    except Exception as e:
        print(f"Erreur lors de l'ajout du professeur : {e}")
        return False
def get_tous_les_profs():
    try:
        with engine.connect() as conn:
            # On sélectionne tout, ordonné par ID décroissant (les plus récents en premier)
            query = text("SELECT * FROM professeurs ORDER BY id DESC")
            # fetchall() récupère toutes les lignes d'un coup
            resultats = conn.execute(query).mappings().fetchall() 
            return resultats
    except Exception as e:
        print(f"Erreur lors de la récupération des professeurs : {e}")
        return [] # En cas d'erreur, on retourne une liste vide
def supprimer_pr(id_prof):
    try:
        with engine.connect() as conn:
            # On cherche le professeur par son ID et on le supprime
            query = text("DELETE FROM professeurs WHERE id = :id")
            conn.execute(query, {"id": id_prof})
            conn.commit() # On valide la suppression dans Aiven
            return True
    except Exception as e:
        print(f"Erreur lors de la suppression du professeur : {e}")
        return False
def get_prof_by_id(id_prof):
    try:
        with engine.connect() as conn:
            query = text("SELECT * FROM professeurs WHERE id = :id")
            resultat = conn.execute(query, {"id": id_prof}).mappings().fetchone()
            return resultat
    except Exception as e:
        print(f"Erreur lors de la récupération du professeur : {e}")
        return None
def modifier_prof_db(id_prof, nom, prenom, date_naissance, sexe, adresse, matiere, email, telephone, mot_de_passe):
    try:
        with engine.connect() as conn:
            query = text("""
                UPDATE professeurs SET 
                nom=:nom, prenom=:prenom, date_naissance=:date_naissance, sexe=:sexe, 
                adresse=:adresse, matiere=:matiere, email=:email, mot_de_passe=:mot_de_passe, 
                telephone=:telephone
                WHERE id = :id
            """)
            conn.execute(query, {
                "id": id_prof, "nom": nom, "prenom": prenom, "date_naissance": date_naissance,
                "sexe": sexe, "adresse": adresse, "matiere": matiere, "email": email,
                "mot_de_passe": mot_de_passe, "telephone": telephone
            })
            conn.commit()
            return True
    except Exception as e:
        print(f"Erreur lors de la modification : {e}")
        return False


