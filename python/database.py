import os
from sqlalchemy import create_engine, text 
from dotenv import load_dotenv
from datetime import datetime
import random

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
def check_admin(email,mot_de_passe): # check if the admin has an account 
    with engine.connect() as conn:
        query = text("SELECT * FROM utilisateur WHERE email = :email AND mot_de_passe = :mot_de_passe AND role = 'admin'")
        result = conn.execute(query,{"email" : email,"mot_de_passe" : mot_de_passe}).fetchone()
        return result is not None 

def compter_eleves():
    try:
        with engine.connect() as conn:
            query = text("SELECT COUNT(*) FROM utilisateur WHERE role = 'eleve'")
            # scalar() renvoie juste le nombre (ex: 12) au lieu d'un dictionnaire
            return conn.execute(query).scalar() 
    except Exception as e:
        print(f"Erreur comptage élèves : {e}")
        return 0

def compter_profs():
    try:
        with engine.connect() as conn:
            query = text("SELECT COUNT(*) FROM utilisateur WHERE role = 'professeur'")
            return conn.execute(query).scalar()
    except Exception as e:
        print(f"Erreur comptage profs : {e}")
        return 0
#------------------------les fonctions de gestion des élèves------------------------
# fonction pour ajouter un élève à la base de données, elle sera utilisée dans le dashboard admin pour créer des comptes élèves
def ajouter_eleve(nom, prenom, sexe, email, adresse, mot_de_passe,classe_id, numero_eleve, date_naissance, nom_tuteur, tel_tuteur):
    try:
        with engine.begin() as conn:
            # 1. Insertion dans "utilisateur" avec sexe et adresse
            query_user = text("""
                INSERT INTO utilisateur (nom, prenom, sexe, email, adresse, mot_de_passe, role)
                VALUES (:nom, :prenom, :sexe, :email, :adresse, :mot_de_passe, 'eleve')
            """)
            result = conn.execute(query_user, {
                "nom": nom, "prenom": prenom, "sexe": sexe, 
                "email": email, "adresse": adresse, "mot_de_passe": mot_de_passe
            })
            
            eleve_id = result.lastrowid 

            # 2. Insertion dans "eleve_classe" (inchangé mais lié à l'ID ci-dessus)
            query_eleve_classe = text("""
                INSERT INTO eleve_classe (eleve_id, classe_id, numero_eleve, date_naissance, nom_tuteur, tel_tuteur)
                VALUES (:eleve_id, :classe_id, :numero_eleve, :date_naissance, :nom_tuteur, :tel_tuteur)
            """)
            conn.execute(query_eleve_classe, {
                "eleve_id": eleve_id,
                "classe_id": classe_id,
                "numero_eleve": numero_eleve,
                "date_naissance": date_naissance,
                "nom_tuteur": nom_tuteur,
                "tel_tuteur": tel_tuteur
            })
            return True
    except Exception as e:
        print(f"Erreur ajout élève : {e}")
        return False

def generer_numero_eleve():
    # On récupère l'année actuelle (ex: 2024 ou 2026)
    annee_actuelle = datetime.now().year
    prefixe = f"EL-{annee_actuelle}-"

    try:
        with engine.connect() as conn:
            # On cherche le plus grand numéro qui commence par "EL-Annee-"
            query = text("""
                SELECT numero_eleve 
                FROM eleve_classe 
                WHERE numero_eleve LIKE :prefixe 
                ORDER BY numero_eleve DESC 
                LIMIT 1
            """)
            # fetchone() car on veut juste le premier résultat de la liste
            resultat = conn.execute(query, {"prefixe": f"{prefixe}%"}).fetchone()

            if resultat:
                # Si on trouve "EL-2024-003", on le coupe par les tirets et on prend "003"
                dernier_numero = resultat[0] # On récupère la chaîne de caractères
                valeur_chiffre = int(dernier_numero.split("-")[2]) # On extrait le chiffre et on le convertit en entier
                nouveau_numero = valeur_chiffre + 1
            else:
                # Si c'est le tout premier élève de l'année, on commence à 1
                nouveau_numero = 1

            # On formate le texte pour forcer les 3 zéros (ex: 001, 012, 105)
            return f"{prefixe}{nouveau_numero:03d}"
            
    except Exception as e:
        print(f"Erreur génération matricule : {e}")
        # Sécurité : en cas d'erreur serveur, on renvoie quand même un code provisoire pour ne pas bloquer l'ajout
        return f"{prefixe}ERR-{random.randint(100,999)}"
# N'oublie pas de modifier aussi get_tous_les_eleves pour afficher le sexe et l'adresse
def get_tous_les_eleves():
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT u.id, u.nom, u.prenom, u.sexe, u.email, u.adresse,
                       ec.numero_eleve, ec.date_naissance, ec.nom_tuteur, ec.tel_tuteur, 
                       c.nom as nom_classe, c.filiere
                FROM utilisateur u
                JOIN eleve_classe ec ON u.id = ec.eleve_id
                JOIN classe c ON ec.classe_id = c.id
                WHERE u.role = 'eleve'
            """)
            return conn.execute(query).mappings().fetchall()
    except Exception as e:
        print(f"Erreur : {e}")
        return []
# fonction pour supprimer un élève de la base de données, elle sera utilisée dans le dashboard admin pour supprimer un élève
def supprimer_ele(id_eleve):
    try:
        with engine.connect() as conn:
            # On cherche l'élève par son ID et on le supprime
            query = text("DELETE FROM utilisateur WHERE id = :id AND role = 'eleve'")
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
            # On récupère les infos des DEUX tables pour remplir le formulaire
            query = text("""
                SELECT u.id, u.nom, u.prenom, u.sexe, u.email, u.adresse, u.mot_de_passe,
                       ec.numero_eleve, ec.date_naissance, ec.nom_tuteur, ec.tel_tuteur, ec.classe_id
                FROM utilisateur u
                JOIN eleve_classe ec ON u.id = ec.eleve_id
                WHERE u.id = :id AND u.role = 'eleve'
            """)
            return conn.execute(query, {"id": id_eleve}).mappings().fetchone()
    except Exception as e:
        print(f"Erreur get_eleve : {e}")
        return None
# fonction pour récupérer les notes d'un élève par son ID, elle sera utilisée dans le dashboard admin pour afficher les notes d'un élève spécifique
def get_notes_by_eleve(id_eleve):
    try:
        with engine.connect() as conn:
            # On suit le chemin exact : Note -> Classe_Matiere -> Matiere
            query = text("""
                SELECT 
                    n.id, 
                    n.valeur, 
                    n.type_evaluation, 
                    n.date_saisie, 
                    m.nom AS matiere
                FROM note n
                JOIN classe_matiere cm ON n.classe_matiere_id = cm.id
                JOIN matiere m ON cm.matiere_id = m.id
                WHERE n.eleve_id = :id_eleve
                ORDER BY n.date_saisie DESC
            """)
            resultats = conn.execute(query, {"id_eleve": id_eleve}).mappings().fetchall()
            return resultats
    except Exception as e:
        print(f"Erreur lors de la récupération des notes : {e}")
        return []
def get_note_by_id(id_note):
    try:
        with engine.connect() as conn:
            # On récupère la note et le nom de la matière associée
            query = text("""
                SELECT n.*, m.nom as nom_matiere, u.nom as nom_eleve, u.prenom as prenom_eleve
                FROM note n
                JOIN utilisateur u ON n.eleve_id = u.id
                JOIN classe_matiere cm ON n.classe_matiere_id = cm.id
                JOIN matiere m ON cm.matiere_id = m.id
                WHERE n.id = :id
            """)
            return conn.execute(query, {"id": id_note}).mappings().fetchone()
    except Exception as e:
        print(f"Erreur get_note : {e}")
        return None

def modifier_note_db(id_note, nouvelle_valeur, type_eval, semestre):
    try:
        with engine.begin() as conn:
            query = text("""
                UPDATE note 
                SET valeur = :valeur, type_evaluation = :type, semestre = :semestre 
                WHERE id = :id
            """)
            conn.execute(query, {
                "valeur": nouvelle_valeur,
                "type": type_eval,
                "semestre": semestre,
                "id": id_note
            })
            return True
    except Exception as e:
        print(f"Erreur modification note : {e}")
        return False
# fonction pour modifier les informations d'un élève dans la base de données, elle sera utilisée dans le dashboard admin pour modifier les informations d'un élève
def modifier_eleve_db(id_eleve, nom, prenom, sexe, adresse, email, mot_de_passe, classe_id, date_naissance, nom_tuteur, tel_tuteur):
    try:
        # On utilise engine.begin() car on modifie DEUX tables (Transaction)
        with engine.begin() as conn:
            
            # 1. Mise à jour des informations générales dans "utilisateur"
            query_user = text("""
                UPDATE utilisateur 
                SET nom=:nom, prenom=:prenom, sexe=:sexe, adresse=:adresse, email=:email, mot_de_passe=:mot_de_passe
                WHERE id = :id
            """)
            conn.execute(query_user, {
                "nom": nom, "prenom": prenom, "sexe": sexe, "adresse": adresse, 
                "email": email, "mot_de_passe": mot_de_passe, "id": id_eleve
            })

            # 2. Mise à jour des informations scolaires dans "eleve_classe"
            query_eleve = text("""
                UPDATE eleve_classe 
                SET classe_id=:classe_id, date_naissance=:date_naissance, nom_tuteur=:nom_tuteur, tel_tuteur=:tel_tuteur
                WHERE eleve_id = :id
            """)
            conn.execute(query_eleve, {
                "classe_id": classe_id, "date_naissance": date_naissance, 
                "nom_tuteur": nom_tuteur, "tel_tuteur": tel_tuteur, "id": id_eleve
            })
            return True
            
    except Exception as e:
        print(f"Erreur modification élève : {e}")
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


