import os
from sqlalchemy import create_engine, text 
from dotenv import load_dotenv

load_dotenv()

DATABASE_KEY = os.getenv("DATABASE")

if not DATABASE_KEY:
    raise ValueError("L'URL de la base de données n'est pas définie dans le fichier .env")

if DATABASE_KEY.startswith("mysql://"):
    DATABASE_KEY = DATABASE_KEY.replace("mysql://", "mysql+mysqlconnector://", 1)

engine = create_engine(DATABASE_KEY, pool_pre_ping=True, pool_recycle=300)

# --- VÉRIFICATION DES CONNEXIONS (CORRIGÉ) ---

def check_etudiant(email, password): 
    with engine.connect() as conn:
        # On cherche dans 'utilisateur' avec le rôle 'eleve'
        query = text("SELECT * FROM utilisateur WHERE email = :email AND mot_de_passe = :password AND role = 'eleve'")
        result = conn.execute(query, {"email": email, "password": password}).fetchone()
        return result is not None 

def check_professeur(email, password):
    try:
        with engine.connect() as conn:
            # On sélectionne les colonnes nécessaires selon la table de Zakaria
            query = text("SELECT id, nom, prenom FROM utilisateur WHERE email = :email AND mot_de_passe = :pw AND role = 'professeur'")
            result = conn.execute(query, {"email": email, "pw": password}).mappings().fetchone()
            return result # Retourne les données ou None
    except Exception as e:
        print(f"Erreur base de données : {e}")
        return None

def check_admin(email, mot_de_passe): 
    with engine.connect() as conn:
        query = text("SELECT * FROM utilisateur WHERE email = :email AND mot_de_passe = :mot_de_passe AND role = 'admin'")
        result = conn.execute(query, {"email": email, "mot_de_passe": mot_de_passe}).fetchone()
        return result is not None 

# --- STATISTIQUES ---

def compter_eleves():
    try:
        with engine.connect() as conn:
            query = text("SELECT COUNT(*) FROM utilisateur WHERE role = 'eleve'")
            return conn.execute(query).scalar() 
    except Exception as e:
        print(f"Erreur : {e}")
        return 0

def compter_profs():
    try:
        with engine.connect() as conn:
            query = text("SELECT COUNT(*) FROM utilisateur WHERE role = 'professeur'")
            return conn.execute(query).scalar()
    except Exception as e:
        print(f"Erreur : {e}")
        return 0

# --- GESTION DES ÉLÈVES (ADAPTÉ À TA STRUCTURE) ---

def ajouter_eleve(nom, prenom, sexe, email, adresse, mot_de_passe, classe_id, numero_eleve, date_naissance, nom_tuteur, tel_tuteur):
    try:
        with engine.begin() as conn:
            query_user = text("""
                INSERT INTO utilisateur (nom, prenom, sexe, email, adresse, mot_de_passe, role)
                VALUES (:nom, :prenom, :sexe, :email, :adresse, :mot_de_passe, 'eleve')
            """)
            result = conn.execute(query_user, {
                "nom": nom, "prenom": prenom, "sexe": sexe, 
                "email": email, "adresse": adresse, "mot_de_passe": mot_de_passe
            })
            
            eleve_id = result.lastrowid 

            query_eleve_classe = text("""
                INSERT INTO eleve_classe (eleve_id, classe_id, numero_eleve, date_naissance, nom_tuteur, tel_tuteur)
                VALUES (:eleve_id, :classe_id, :numero_eleve, :date_naissance, :nom_tuteur, :tel_tuteur)
            """)
            conn.execute(query_eleve_classe, {
                "eleve_id": eleve_id, "classe_id": classe_id, "numero_eleve": numero_eleve,
                "date_naissance": date_naissance, "nom_tuteur": nom_tuteur, "tel_tuteur": tel_tuteur
            })
            return True
    except Exception as e:
        print(f"Erreur : {e}")
        return False

def get_tous_les_eleves():
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT u.id, u.nom, u.prenom, u.sexe, u.email, u.adresse,
                       ec.numero_eleve, ec.date_naissance, ec.nom_tuteur, ec.tel_tuteur, 
                       c.nom as nom_classe
                FROM utilisateur u
                JOIN eleve_classe ec ON u.id = ec.eleve_id
                JOIN classe c ON ec.classe_id = c.id
                WHERE u.role = 'eleve'
            """)
            return conn.execute(query).mappings().fetchall()
    except Exception as e:
        print(f"Erreur : {e}")
        return []

# --- GESTION DES PROFS (ADAPTÉ À TA STRUCTURE) ---

def get_tous_les_profs():
    try:
        with engine.connect() as conn:
            # On cherche dans utilisateur là où le rôle est professeur
            query = text("SELECT * FROM utilisateur WHERE role = 'professeur' ORDER BY id DESC")
            return conn.execute(query).mappings().fetchall()
    except Exception as e:
        print(f"Erreur : {e}")
        return []

def supprimer_pr(id_prof):
    try:
        with engine.begin() as conn:
            query = text("DELETE FROM utilisateur WHERE id = :id AND role = 'professeur'")
            conn.execute(query, {"id": id_prof})
            return True
    except Exception as e:
        print(f"Erreur : {e}")
        return False


def get_eleves_par_classe(classe_id):
    try:
        with engine.connect() as conn:
            # On cherche les élèves liés à une classe spécifique
            query = text("""
                SELECT u.id, u.nom, u.prenom 
                FROM utilisateur u
                JOIN eleve_classe ec ON u.id = ec.eleve_id
                WHERE ec.classe_id = :classe_id AND u.role = 'eleve'
            """)
            return conn.execute(query, {"classe_id": classe_id}).mappings().fetchall()
    except Exception as e:
        print(f"Erreur lors de la récupération des élèves : {e}")
        return []

def enregistrer_note(eleve_id, matiere, note, date_saisie):
    try:
        with engine.connect() as conn:
            query = text("""
                INSERT INTO notes (eleve_id, matiere, valeur, date_saisie)
                VALUES (:id, :mat, :val, :dt)
            """)
            conn.execute(query, {"id": eleve_id, "mat": matiere, "val": note, "dt": date_saisie})
            conn.commit() # Très important pour valider l'insertion dans MySQL
            return True
    except Exception as e:
        print(f"Erreur lors de l'enregistrement de la note : {e}")
        return False

def enregistrer_notes_completes(eleve_id, matiere, cc1, cc2, exam, moyenne): # On a bien 6 arguments ici
    try:
        with engine.connect() as conn:
            query = text("""
                INSERT INTO notes (eleve_id, matiere, note_cc1, note_cc2, note_examen, moyenne, date_saisie)
                VALUES (:id, :mat, :c1, :c2, :ex, :moy, NOW())
                ON DUPLICATE KEY UPDATE note_cc1=:c1, note_cc2=:c2, note_examen=:ex, moyenne=:moy
            """)
            conn.execute(query, {
                "id": eleve_id, "mat": matiere, 
                "c1": cc1, "c2": cc2, "ex": exam, "moy": moyenne
            })
            conn.commit()
            return True
    except Exception as e:
        print(f"Erreur SQL : {e}")
        return False
    except Exception as e:
        print(f"Erreur SQL : {e}")
def get_notes_existantes(matiere):
    try:
        with engine.connect() as conn:
            query = text("SELECT * FROM notes WHERE matiere = :mat")
            result = conn.execute(query, {"mat": matiere}).mappings().fetchall()
            # On crée un dictionnaire {eleve_id: données_de_la_note}
            return {r['eleve_id']: r for r in result}
    except Exception as e:
        print(f"Erreur SQL lecture : {e}")
        return {}

def update_profil_prof(user_id, nouveau_prenom, nouveau_nom, nouveau_mdp=None):
    try:
        with engine.connect() as conn:
            if nouveau_mdp:
                query = text("""
                    UPDATE utilisateur 
                    SET prenom = :p, nom = :n, mot_de_passe = :m 
                    WHERE id = :id
                """)
                conn.execute(query, {"p": nouveau_prenom, "n": nouveau_nom, "m": nouveau_mdp, "id": user_id})
            else:
                query = text("""
                    UPDATE utilisateur SET prenom = :p, nom = :n WHERE id = :id
                """)
                conn.execute(query, {"p": nouveau_prenom, "n": nouveau_nom, "id": user_id})
            conn.commit()
            return True
    except Exception as e:
        print(f"Erreur profil : {e}")
        return False

def get_user_by_id(user_id):
    try:
        with engine.connect() as conn:
            query = text("SELECT id, nom, prenom, email, role FROM utilisateur WHERE id = :id")
            # .mappings().first() permet de récupérer le résultat sous forme de dictionnaire
            return conn.execute(query, {"id": user_id}).mappings().first()
    except Exception as e:
        print(f"Erreur lors de la récupération de l'utilisateur : {e}")
        return None

def enregistrer_absence(eleve_id, date_absence, seance, statut, justification="Non justifiée"):
    try:
        with engine.connect() as conn:
            query = text("""
                INSERT INTO absence (eleve_id, date_absence, seance, statut, justification)
                VALUES (:id, :date, :seance, :statut, :just)
                ON DUPLICATE KEY UPDATE statut=:statut, justification=:just
            """)
            conn.execute(query, {
                "id": eleve_id, "date": date_absence, 
                "seance": seance, "statut": statut, "just": justification
            })
            conn.commit()
            return True
    except Exception as e:
        print(f"Erreur SQL Absence : {e}")
        return False