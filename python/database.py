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
def ajouter_eleve(nom, prenom, sexe, email, adresse, mot_de_passe, numero_eleve, date_naissance, nom_tuteur, tel_tuteur):
    try:
        with engine.begin() as conn:
            # 1. Insertion dans "utilisateur" avec sexe et adresse
            query_user = text("""
                INSERT INTO utilisateur (nom, prenom, sexe, email, adresse, mot_de_passe, role, numero_eleve, date_naissance, nom_tuteur, tel_tuteur)
                VALUES (:nom, :prenom, :sexe, :email, :adresse, :mot_de_passe, 'eleve', :numero_eleve, :date_naissance, :nom_tuteur, :tel_tuteur)
            """)
            result = conn.execute(query_user, {
                "nom": nom, "prenom": prenom, "sexe": sexe, 
                "email": email, "adresse": adresse, "mot_de_passe": mot_de_passe, "numero_eleve": numero_eleve, "date_naissance": date_naissance, "nom_tuteur": nom_tuteur, "tel_tuteur": tel_tuteur
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
                FROM utilisateur 
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
                SELECT id, nom, prenom, sexe, email, adresse,
                       numero_eleve, date_naissance, nom_tuteur, tel_tuteur
                FROM utilisateur 
                WHERE role = 'eleve'
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
                SELECT id, nom, prenom, sexe, email, adresse,
                       numero_eleve, date_naissance, nom_tuteur, tel_tuteur
                FROM utilisateur 
                WHERE id = :id AND role = 'eleve'
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
def modifier_eleve_db(id_eleve, nom, prenom, sexe, adresse, email, mot_de_passe, date_naissance, nom_tuteur, tel_tuteur):
    try:
        # On utilise engine.begin() car on modifie DEUX tables (Transaction)
        with engine.begin() as conn:
            
            # 1. Mise à jour des informations générales dans "utilisateur"
            query_user = text("""
                UPDATE utilisateur 
                SET nom=:nom, prenom=:prenom, sexe=:sexe, adresse=:adresse, email=:email, mot_de_passe=:mot_de_passe, date_naissance=:date_naissance, nom_tuteur=:nom_tuteur, tel_tuteur=:tel_tuteur
                WHERE id = :id
            """)
            conn.execute(query_user, {
                "nom": nom, "prenom": prenom, "sexe": sexe, "adresse": adresse, 
                "email": email, "mot_de_passe": mot_de_passe, "date_naissance": date_naissance, "nom_tuteur": nom_tuteur, "tel_tuteur": tel_tuteur, "id": id_eleve
            })
            return True
            
    except Exception as e:
        print(f"Erreur modification élève : {e}")
        return False
#------------------------les fonctions de gestion des profs------------------------
def get_toutes_les_matieres():
    try:
        with engine.connect() as conn:
            # On récupère l'ID et le nom de chaque matière
            query = text("SELECT id, nom FROM matiere ORDER BY nom ASC")
            resultats = conn.execute(query).mappings().fetchall()
            return resultats
    except Exception as e:
        print(f"Erreur lors de la récupération des matières : {e}")
        return []
def get_toutes_les_classes():
    try:
        with engine.connect() as conn:
            # On ajoute niveau et annee_academique dans le SELECT
            query = text("SELECT id, nom, niveau, filiere, annee_academique FROM classe ORDER BY annee_academique DESC, nom ASC")
            return conn.execute(query).mappings().fetchall()
    except Exception as e:
        print(f"Erreur SQL : {e}")
        return []
def get_eleves_by_classe(classe_id):
    try:
        with engine.connect() as conn:
            # On fait la jointure entre utilisateur et la table pivot eleve_classe
            query = text("""
                SELECT u.id, u.nom, u.prenom, u.sexe, u.email 
                FROM utilisateur u
                JOIN eleve_classe ec ON u.id = ec.eleve_id
                WHERE ec.classe_id = :classe_id AND u.role = 'eleve'
                ORDER BY u.nom ASC, u.prenom ASC
            """)
            return conn.execute(query, {"classe_id": classe_id}).mappings().fetchall()
    except Exception as e:
        print(f"Erreur lors de la récupération des élèves de la classe : {e}")
        return []
def get_classe_by_id(classe_id):
    """Fonction bonus pour récupérer le nom de la classe et l'afficher en titre"""
    try:
        with engine.connect() as conn:
            query = text("SELECT id, nom, niveau, filiere, annee_academique FROM classe WHERE id = :id")
            return conn.execute(query, {"id": classe_id}).mappings().fetchone()
    except Exception as e:
        print(f"Erreur SQL : {e}")
        return None
def ajouter_classe_db(nom, niveau, filiere, annee_academique):
    try:
        with engine.begin() as conn:
            # On ajoute les nouvelles colonnes dans l'INSERT
            query = text("""
                INSERT INTO classe (nom, niveau, filiere, annee_academique) 
                VALUES (:nom, :niveau, :filiere, :annee)
            """)
            conn.execute(query, {
                "nom": nom, 
                "niveau": niveau, 
                "filiere": filiere, 
                "annee": annee_academique
            })
            return True
    except Exception as e:
        print(f"Erreur ajout classe : {e}")
        return False
def supprimer_classe_db(classe_id):
    try:
        with engine.begin() as conn:
            query = text("DELETE FROM classe WHERE id = :id")
            conn.execute(query, {"id": classe_id})
            return True
    except Exception as e:
        print(f"Erreur lors de la suppression de la classe : {e}")
        return False
def get_nombre_eleves_classe(classe_id):
    """Compte le nombre d'élèves actuellement dans une classe"""
    try:
        with engine.connect() as conn:
            query = text("SELECT COUNT(*) FROM eleve_classe WHERE classe_id = :id")
            # scalar() permet de récupérer juste le chiffre (ex: 8) au lieu d'un dictionnaire
            count = conn.execute(query, {"id": classe_id}).scalar()
            return count
    except Exception as e:
        print(f"Erreur lors du comptage : {e}")
        return 0
def get_eleves_sans_classe():
    """Récupère uniquement les élèves qui ne sont pas encore affectés à une classe"""
    try:
        with engine.connect() as conn:
            # Le LEFT JOIN et le IS NULL permettent de trouver ceux qui n'ont pas de correspondance dans eleve_classe
            query = text("""
                SELECT u.id, u.nom, u.prenom, u.numero_eleve 
                FROM utilisateur u
                LEFT JOIN eleve_classe ec ON u.id = ec.eleve_id
                WHERE u.role = 'eleve' AND ec.classe_id IS NULL
                ORDER BY u.nom ASC
            """)
            return conn.execute(query).mappings().fetchall()
    except Exception as e:
        print(f"Erreur SQL élèves sans classe : {e}")
        return []
def affecter_eleve_db(eleve_id, classe_id):
    """Insère l'élève dans la classe sélectionnée"""
    try:
        with engine.begin() as conn:
            query = text("""
                INSERT INTO eleve_classe (eleve_id, classe_id)
                VALUES (:e_id, :c_id)
            """)
            conn.execute(query, {
                "e_id": eleve_id, 
                "c_id": classe_id
            })
            return True
    except Exception as e:
        print(f"Erreur lors de l'affectation : {e}")
        return False
def get_nombre_eleves_classe(classe_id):
    """Compte le nombre d'élèves actuellement dans une classe"""
    try:
        with engine.connect() as conn:
            query = text("SELECT COUNT(*) FROM eleve_classe WHERE classe_id = :id")
            return conn.execute(query, {"id": classe_id}).scalar()
    except Exception as e:
        return 0
# fonction pour ajouter un professeur à la base de données, elle sera utilisée dans le dashboard admin pour créer des comptes professeurs
def ajouter_prof(nom, prenom, sexe, email, adresse, mot_de_passe):
    try:
        with engine.begin() as conn:
            # 1. On crée d'abord le professeur dans la table utilisateur
            query_user = text("""
                INSERT INTO utilisateur (nom, prenom, sexe, email, adresse, mot_de_passe, role)
                VALUES (:nom, :prenom, :sexe, :email, :adresse, :mot_de_passe, 'professeur')
            """)
            result = conn.execute(query_user, {
                "nom": nom, "prenom": prenom, "sexe": sexe, 
                "email": email, "adresse": adresse, "mot_de_passe": mot_de_passe
            })
            return True
    except Exception as e:
        print(f"Erreur lors de l'ajout du professeur : {e}")
        return False
def get_tous_les_profs():
    try:
        with engine.connect() as conn:
            # On utilise GROUP_CONCAT pour fusionner les matières
            # et GROUP BY pour regrouper par professeur
            query = text("""
                SELECT 
                    u.id, 
                    u.nom, 
                    u.prenom, 
                    u.sexe, 
                    u.email, 
                    u.adresse, 
                    GROUP_CONCAT(DISTINCT m.nom SEPARATOR ', ') AS nom_matiere
                FROM utilisateur u
                LEFT JOIN classe_matiere cm ON u.id = cm.professeur_id
                LEFT JOIN matiere m ON cm.matiere_id = m.id
                WHERE u.role = 'professeur'
                GROUP BY u.id, u.nom, u.prenom, u.sexe, u.email, u.adresse
                ORDER BY u.nom ASC
            """)
            resultats = conn.execute(query).mappings().fetchall()
            return resultats
    except Exception as e:
        print(f"Erreur lors de la récupération des professeurs : {e}")
        return []
def get_toutes_les_assignations():
    """Récupère le tableau de toutes les assignations pour l'affichage"""
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT cm.id, c.nom AS classe_nom, c.filiere, m.nom AS matiere_nom,
                       u.nom AS prof_nom, u.prenom AS prof_prenom, cm.coefficient
                FROM classe_matiere cm
                JOIN classe c ON cm.classe_id = c.id
                JOIN matiere m ON cm.matiere_id = m.id
                JOIN utilisateur u ON cm.professeur_id = u.id
                ORDER BY c.nom ASC, m.nom ASC
            """)
            return conn.execute(query).mappings().fetchall()
    except Exception as e:
        print(f"Erreur SQL assignations : {e}")
        return []

def ajouter_assignation_db(classe_id, matiere_id, prof_id, coefficient):
    """Enregistre l'assignation dans la base de données"""
    try:
        with engine.begin() as conn:
            query = text("""
                INSERT INTO classe_matiere (classe_id, matiere_id, professeur_id, coefficient)
                VALUES (:c_id, :m_id, :p_id, :coef)
            """)
            conn.execute(query, {
                "c_id": classe_id, 
                "m_id": matiere_id, 
                "p_id": prof_id, 
                "coef": coefficient
            })
            return True
    except Exception as e:
        print(f"Erreur lors de l'assignation : {e}")
        return False

def get_dernier_coefficient(filiere, matiere_id):
    """Cherche le dernier coefficient utilisé pour la magie du JavaScript"""
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT cm.coefficient 
                FROM classe_matiere cm
                JOIN classe c ON cm.classe_id = c.id
                WHERE c.filiere = :filiere AND cm.matiere_id = :matiere_id
                ORDER BY cm.id DESC LIMIT 1
            """)
            result = conn.execute(query, {"filiere": filiere, "matiere_id": matiere_id}).scalar()
            return result if result is not None else 1
    except Exception as e:
        return 1
def supprimer_pr(id_prof):
    try:
        with engine.connect() as conn:
            # On cherche le professeur par son ID et on le supprime
            query = text("DELETE FROM utilisateur WHERE id = :id AND role = 'professeur'")
            conn.execute(query, {"id": id_prof})
            conn.commit() # On valide la suppression dans Aiven
            return True
    except Exception as e:
        print(f"Erreur lors de la suppression du professeur : {e}")
        return False
def get_prof_by_id(prof_id):
    """Récupère les infos du prof + sa matière et sa classe actuelles"""
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT id, nom, prenom, sexe, email, adresse
                FROM utilisateur 
                WHERE id = :id AND role = 'professeur'
            """)
            resultat = conn.execute(query, {"id": prof_id}).mappings().fetchone()
            return resultat
    except Exception as e:
        print(f"Erreur lors de la récupération du prof : {e}")
        return None

def modifier_prof_db(prof_id, nom, prenom, sexe, email, adresse, mot_de_passe=None, matiere_id=None, classe_id=None):
    """Sauvegarde les modifications (Infos + Matière/Classe)"""
    try:
        with engine.begin() as conn:
            # 1. On modifie les infos dans la table 'utilisateur'
            if mot_de_passe and mot_de_passe.strip() != "":
                query_user = text("""
                    UPDATE utilisateur 
                    SET nom=:nom, prenom=:prenom, sexe=:sexe, email=:email, adresse=:adresse, mot_de_passe=:mdp
                    WHERE id=:id AND role='professeur'
                """)
                conn.execute(query_user, {"nom":nom, "prenom":prenom, "sexe":sexe, "email":email, "adresse":adresse, "mdp":mot_de_passe, "id":prof_id})
            else:
                query_user = text("""
                    UPDATE utilisateur 
                    SET nom=:nom, prenom=:prenom, sexe=:sexe, email=:email, adresse=:adresse
                    WHERE id=:id AND role='professeur'
                """)
                conn.execute(query_user, {"nom":nom, "prenom":prenom, "sexe":sexe, "email":email, "adresse":adresse, "id":prof_id})

            # 2. On modifie l'affectation dans la table 'classe_matiere'
            if matiere_id and classe_id:
                # On vérifie si le prof a déjà une affectation
                check_query = text("SELECT id FROM classe_matiere WHERE professeur_id = :prof_id")
                existing = conn.execute(check_query, {"prof_id": prof_id}).fetchone()

                if existing:
                    # S'il a déjà une affectation, on la met à jour
                    update_cm = text("""
                        UPDATE classe_matiere
                        SET matiere_id = :matiere_id, classe_id = :classe_id
                        WHERE professeur_id = :prof_id
                    """)
                    conn.execute(update_cm, {"matiere_id": matiere_id, "classe_id": classe_id, "prof_id": prof_id})
                else:
                    # S'il n'avait aucune affectation avant, on la crée
                    insert_cm = text("""
                        INSERT INTO classe_matiere (classe_id, matiere_id, professeur_id)
                        VALUES (:classe_id, :matiere_id, :prof_id)
                    """)
                    conn.execute(insert_cm, {"matiere_id": matiere_id, "classe_id": classe_id, "prof_id": prof_id})
            return True
    except Exception as e:
        print(f"Erreur lors de la modification : {e}")
        return False

