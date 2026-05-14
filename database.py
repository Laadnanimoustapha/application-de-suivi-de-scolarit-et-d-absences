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

# def check_etudiant(email, password): 
#     with engine.connect() as conn:
#         # On cherche dans 'utilisateur' avec le rôle 'eleve'
#         query = text("SELECT * FROM utilisateur WHERE email = :email AND mot_de_passe = :password AND role = 'eleve'")
#         result = conn.execute(query, {"email": email, "password": password}).fetchone()
#         return result is not None 

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
def get_notes_existantes(classe_matiere_id):
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT eleve_id, valeur, type_evaluation 
                FROM note 
                WHERE classe_matiere_id = :cm_id
            """)
            result = conn.execute(query, {"cm_id": classe_matiere_id}).mappings().fetchall()
            
            notes_dict = {}
            for r in result:
                e_id = r['eleve_id']
                if e_id not in notes_dict:
                    # Initialisation par défaut pour chaque élève
                    notes_dict[e_id] = {'cc1': '', 'cc2': '', 'cc3': '', 'cc4': ''}
                
                # On mappe le type_evaluation (ex: 'cc1') à la clé du dictionnaire
                t_eval = r['type_evaluation']
                if t_eval in ['cc1', 'cc2', 'cc3', 'cc4']:
                    notes_dict[e_id][t_eval] = r['valeur']
                elif t_eval == 'controle': # Fallback pour ton test précédent
                    notes_dict[e_id]['cc1'] = r['valeur']
            
            return notes_dict
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

def enregistrer_absence(eleve_id, date_abs, statut, justification):
    # On n'utilise que les colonnes qui existent vraiment dans ta table 'absence'
    # Si 'statut' n'existe pas, retire-le aussi d'ici
    query = text("""
        INSERT INTO absence (eleve_id, date_absence, justification) 
        VALUES (:e_id, :d_abs, :j)
        ON DUPLICATE KEY UPDATE justification = :j
    """)
    with engine.connect() as conn:
        conn.execute(query, {
            "e_id": eleve_id, 
            "d_abs": date_abs, 
            "j": justification
        })
        conn.commit()

def get_infos_professeur(prof_id):
    try:
        # Utilise 'with engine.connect()' comme dans tes autres fonctions
        with engine.connect() as conn:
            query = text("""
                SELECT cm.classe_id, cm.matiere_id, c.nom AS nom_classe, m.nom AS nom_matiere
                FROM classe_matiere cm
                JOIN classe c ON cm.classe_id = c.id
                JOIN matiere m ON cm.matiere_id = m.id
                WHERE cm.professeur_id = :id
                LIMIT 1
            """)
            # On utilise 'conn.execute' et '.mappings().first()' pour plus de facilité
            return conn.execute(query, {"id": prof_id}).mappings().first()
    except Exception as e:
        print(f"Erreur lors de la récupération des infos prof : {e}")
        return None
    
def get_notes_existantes(classe_matiere_id):
    try:
        with engine.connect() as conn:
            # On récupère toutes les lignes de notes pour cette classe/matière
            query = text("SELECT eleve_id, valeur, type_evaluation FROM note WHERE classe_matiere_id = :cm_id")
            result = conn.execute(query, {"cm_id": classe_matiere_id}).mappings().fetchall()
            
            notes_dict = {}
            for r in result:
                e_id = r['eleve_id']
                if e_id not in notes_dict:
                    notes_dict[e_id] = {'note_cc1': None, 'note_cc2': None, 'note_cc3': None, 'note_cc4': None}
                
                # IMPORTANT : On associe le type_evaluation au bon champ CC
                # Vérifie bien les noms 'cc1', 'cc2' etc. dans ta colonne type_evaluation
                t_eval = r['type_evaluation']
                if t_eval in ['cc1', 'cc2', 'cc3', 'cc4']:
                    notes_dict[e_id][f'note_{t_eval}'] = r['valeur']
                elif t_eval == 'controle': # Si tu as utilisé 'controle' pour le premier test
                    notes_dict[e_id]['note_cc1'] = r['valeur']
            
            return notes_dict
    except Exception as e:
        print(f"Erreur SQL lecture : {e}")
        return {}

def supprimer_notes_eleve(eleve_id, matiere_nom):
    try:
        with engine.begin() as conn:
            query = text("DELETE FROM note WHERE eleve_id = :id AND matiere = :mat")
            conn.execute(query, {"id": eleve_id, "mat": matiere_nom})
            return True
    except Exception as e:
        print(f"Erreur suppression : {e}")
        return False

def sauvegarder_note_individuelle(eleve_id, classe_matiere_id, valeur, type_eval):
    try:
        # 'begin()' gère automatiquement le COMMIT à la fin du bloc
        with engine.begin() as conn:
            query = text("""
                INSERT INTO note (eleve_id, classe_matiere_id, valeur, type_evaluation, semestre, date_saisie)
                VALUES (:e_id, :cm_id, :val, :type, 'S1', CURRENT_DATE)
                ON DUPLICATE KEY UPDATE 
                    valeur = VALUES(valeur),
                    date_saisie = CURRENT_DATE
            """)
            conn.execute(query, {
                "e_id": eleve_id, 
                "cm_id": classe_matiere_id, 
                "val": valeur, 
                "type": type_eval
            })
            print(f"DEBUG: Note {valeur} enregistrée pour l'élève {eleve_id}")
    except Exception as e:
        print(f"ERREUR SQL CRITIQUE : {e}")

def get_affectations_professeur(user_id):
    with engine.connect() as conn:
        # Utilisation des noms de colonnes 'nom' confirmés par ton SQL
        query = text("""
            SELECT cm.id, c.nom AS nom_classe, m.nom AS nom_matiere 
            FROM classe_matiere cm
            JOIN classe c ON cm.classe_id = c.id
            JOIN matiere m ON cm.matiere_id = m.id
            JOIN utilisateur u ON cm.professeur_id = u.id
            WHERE u.id = :u_id AND u.role = 'professeur'
        """)
        return conn.execute(query, {"u_id": user_id}).mappings().fetchall()

def get_infos_selection(cm_id):
    with engine.connect() as conn:
        query = text("""
            SELECT 
                c.id AS classe_id, 
                c.nom AS nom_classe, 
                m.id AS matiere_id, 
                m.nom AS nom_matiere
            FROM classe_matiere cm
            JOIN classe c ON cm.classe_id = c.id
            JOIN matiere m ON cm.matiere_id = m.id
            WHERE cm.id = :cm_id
        """)
        return conn.execute(query, {"cm_id": cm_id}).mappings().fetchone()

def get_classes_du_prof(prof_id):
    try:
        with engine.connect() as conn:
            # Cette requête récupère les classes associées au professeur
            query = text("""
                SELECT DISTINCT c.id, c.nom 
                FROM classe c
                JOIN assignation_matiere am ON c.id = am.classe_id
                WHERE am.prof_id = :p_id
            """)
            return conn.execute(query, {"p_id": prof_id}).mappings().fetchall()
    except Exception as e:
        print(f"Erreur get_classes_du_prof : {e}")
        return []
