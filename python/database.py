import os
from sqlalchemy import create_engine, text 
from dotenv import load_dotenv
from datetime import datetime
import random
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

DATABASE_KEY = os.getenv("DATABASE")

if not DATABASE_KEY:
    raise ValueError("The 'DATABASE' environment variable is not set. Please set it in your environment or in a .env file.")

if DATABASE_KEY.startswith("mysql://"):
    DATABASE_KEY = DATABASE_KEY.replace("mysql://", "mysql+mysqlconnector://", 1)

engine = create_engine(DATABASE_KEY, pool_pre_ping=True, pool_recycle=300)

def check_etudiant(email,password): # check if the student has an account 
    # N'oublie pas d'importer la fonction tout en haut de ton fichier
    try:
        with engine.connect() as conn:
            # 1. On cherche SEULEMENT l'élève par son email et on récupère son mot de passe haché
            query = text("""
                SELECT id, mot_de_passe 
                FROM utilisateur 
                WHERE email = :email AND role = 'eleve'
            """)
            
            resultat = conn.execute(query, {"email": email}).fetchone()

            # Si on a trouvé un élève avec cet email
            if resultat:
                eleve_id = resultat[0]
                mot_de_passe_hache_db = resultat[1] # Ressemble à "scrypt:32768:8:1$..."
                
                # 2. LA MAGIE EST ICI : On compare le hachage de la DB avec le mot de passe tapé
                if check_password_hash(mot_de_passe_hache_db, password):
                    # Si c'est True, le mot de passe est bon ! On retourne l'ID pour la session
                    return eleve_id
                else:
                    # Le mot de passe est faux
                    return None
            else:
                # L'email n'existe pas
                return None
                
    except Exception as e:
        print(f"Erreur lors du login : {e}")
        return None


def check_professeur(email, password):
    try:
        with engine.connect() as conn:
            # 1. On cherche SEULEMENT par l'email (on enlève le mot de passe du WHERE)
            # On ajoute "mot_de_passe" dans le SELECT pour pouvoir le récupérer et le comparer
            query = text("""
                SELECT id, nom, prenom, mot_de_passe 
                FROM utilisateur 
                WHERE email = :email AND role = 'professeur'
            """)
            
            # mappings() permet d'accéder aux données comme un dictionnaire
            result = conn.execute(query, {"email": email}).mappings().fetchone()
            
            # 2. Si on a trouvé un professeur avec cet email
            if result:
                # 3. On compare le hachage de la base avec le mot de passe tapé
                if check_password_hash(result['mot_de_passe'], password):
                    # Si c'est correct, on retourne un dictionnaire propre avec juste les infos utiles
                    return {
                        "id": result['id'],
                        "nom": result['nom'],
                        "prenom": result['prenom']
                    }
                    
            # Si l'email n'existe pas, ou si le mot de passe est faux
            return None
            
    except Exception as e:
        print(f"Erreur base de données : {e}")
        # Optionnel : Tu pourrais utiliser logging.exception(e) ici !
        return None
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
    -- 1. On coupe le texte au dernier tiret '-'
    -- 2. On transforme le résultat en nombre (UNSIGNED)
    -- 3. On trie du plus grand au plus petit
    ORDER BY CAST(SUBSTRING_INDEX(numero_eleve, '-', -1) AS UNSIGNED) DESC 
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
            query = text("""
                SELECT 
                    n.id,
                    m.nom AS matiere, 
                    n.valeur AS note, 
                    n.type_evaluation, 
                    n.date_saisie, 
                    n.semestre,               -- AJOUT DU SEMESTRE
                    c.annee_academique        -- AJOUT DE L'ANNÉE
                FROM note n
                JOIN classe_matiere cm ON n.classe_matiere_id = cm.id
                JOIN classe c ON cm.classe_id = c.id
                JOIN matiere m ON cm.matiere_id = m.id
                WHERE n.eleve_id = :eleve_id
                ORDER BY c.annee_academique DESC, n.semestre ASC, n.date_saisie DESC
            """)
            return conn.execute(query, {"eleve_id": id_eleve}).mappings().fetchall()
    except Exception as e:
        print(f"Erreur : {e}")
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
def modifier_eleve_db(id, nom, prenom, date_naissance, sexe, adresse, email, nom_tuteur, tel_tuteur, mdp_hash):
    """Met à jour l'élève. Ne modifie le mot de passe que si mdp_hash n'est pas None."""
    try:
        with engine.begin() as conn:
            
            # CAS 1 : L'admin A TAPÉ un nouveau mot de passe
            if mdp_hash is not None:
                query = text("""
                    UPDATE utilisateur 
                    SET nom = :nom, prenom = :prenom, date_naissance = :dn, 
                        sexe = :sexe, adresse = :adresse, email = :email, 
                        nom_tuteur = :nt, tel_tuteur = :tt, 
                        mot_de_passe = :mdp  -- ON MET À JOUR LE MOT DE PASSE ICI
                    WHERE id = :id
                """)
                conn.execute(query, {
                    "nom": nom, "prenom": prenom, "dn": date_naissance, "sexe": sexe, 
                    "adresse": adresse, "email": email, "nt": nom_tuteur, 
                    "tt": tel_tuteur, "mdp": mdp_hash, "id": id
                })
                
            # CAS 2 : L'admin N'A RIEN TAPÉ (mdp_hash est None)
            else:
                query = text("""
                    UPDATE utilisateur 
                    SET nom = :nom, prenom = :prenom, date_naissance = :dn, 
                        sexe = :sexe, adresse = :adresse, email = :email, 
                        nom_tuteur = :nt, tel_tuteur = :tt
                    WHERE id = :id
                    -- ON NE TOUCHE PAS À LA COLONNE mot_de_passe !
                """)
                conn.execute(query, {
                    "nom": nom, "prenom": prenom, "dn": date_naissance, "sexe": sexe, 
                    "adresse": adresse, "email": email, "nt": nom_tuteur, 
                    "tt": tel_tuteur, "id": id
                })
                
        return True
    except Exception as e:
        print(f"Erreur lors de la mise à jour : {e}")
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
def get_profs_par_classe(classe_id):
    """Récupère la liste des professeurs assignés à une classe avec leurs matières"""
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT u.nom, u.prenom, m.nom AS matiere_nom, cm.coefficient
                FROM classe_matiere cm
                JOIN utilisateur u ON cm.professeur_id = u.id
                JOIN matiere m ON cm.matiere_id = m.id
                WHERE cm.classe_id = :id
                ORDER BY m.nom ASC
            """)
            return conn.execute(query, {"id": classe_id}).mappings().fetchall()
    except Exception as e:
        print(f"Erreur SQL profs par classe : {e}")
        return []
def modifier_prof_db(prof_id, nom, prenom, sexe, email, adresse, mot_de_passe, matiere_id=None, classe_id=None):
    """Sauvegarde les modifications (Infos + Matière/Classe)"""
    try:
        with engine.begin() as conn:
            # 1. On modifie les infos dans la table 'utilisateur'
            if mot_de_passe and mot_de_passe.strip() != "":
                mdp_hash=generate_password_hash(mot_de_passe)
                query_user = text("""
                    UPDATE utilisateur 
                    SET nom=:nom, prenom=:prenom, sexe=:sexe, email=:email, adresse=:adresse, mot_de_passe=:mdp
                    WHERE id=:id AND role='professeur'
                """)
                conn.execute(query_user, {"nom":nom, "prenom":prenom, "sexe":sexe, "email":email, "adresse":adresse, "mdp":mdp_hash, "id":prof_id})
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
#------------------------les fonctions de gestion de la configuration globale de l'école------------------------
def get_configuration_actuelle():
    """Récupère l'année et le semestre en cours"""
    try:
        with engine.connect() as conn:
            query = text("SELECT annee_academique, semestre FROM configuration_ecole WHERE id = 1")
            return conn.execute(query).mappings().fetchone()
    except Exception as e:
        print(f"Erreur SQL configuration : {e}")
        return None
def update_configuration(annee, semestre):
    """Met à jour la configuration globale de l'école"""
    try:
        with engine.begin() as conn:
            query = text("""
                UPDATE configuration_ecole 
                SET annee_academique = :annee, semestre = :semestre 
                WHERE id = 1
            """)
            conn.execute(query, {"annee": annee, "semestre": semestre})
            return True
    except Exception as e:
        print(f"Erreur mise à jour configuration : {e}")
        return False
def get_absences_non_justifiees():
    """Récupère toutes les absences qui attendent une justification"""
    try:
        with engine.connect() as conn:
            # On fait des jointures pour avoir le nom de l'élève, de la classe et de la matière
            query = text("""
                SELECT a.id, u.nom, u.prenom, c.nom AS classe_nom, m.nom AS matiere_nom, a.date_absence, a.motif_justification, a.fichier_justificatif 
                FROM absence a
                JOIN utilisateur u ON a.eleve_id = u.id
                JOIN classe_matiere cm ON a.classe_matiere_id = cm.id
                JOIN classe c ON cm.classe_id = c.id
                JOIN matiere m ON cm.matiere_id = m.id
                WHERE a.justifiee = FALSE
                ORDER BY a.date_absence DESC
            """)
            return conn.execute(query).mappings().fetchall()
    except Exception as e:
        print(f"Erreur SQL lecture absences : {e}")
        return []
def justifier_absence_db(absence_id, motif, est_acceptee):
    """Met à jour l'absence pour la marquer comme justifiée avec son motif"""
    try:
        with engine.begin() as conn:
            query = text("""
                UPDATE absence
                -- On met à jour "justifiee" avec True (1) ou False (0) selon le bouton cliqué
                SET justifiee = :est_acceptee, motif_justification = :motif
                WHERE id = :id
            """)
            conn.execute(query, {
                "id": absence_id, 
                "motif": motif, 
                "est_acceptee": est_acceptee
            })
        return True
    except Exception as e:
        print(f"Erreur SQL justification absence : {e}")
        return False

def get_donnees_bulletin(eleve_id, semestre):
    """
    Récupère les moyennes par matière pour un élève et un semestre donné.
    Calcule automatiquement la moyenne des différents contrôles.
    """
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT 
                    m.nom AS matiere,
                    cm.coefficient,
                    
                    AVG(n.valeur) AS moyenne_matiere, -- Calcule la moyenne des contrôles
                    u.nom AS prof_nom,
                    u.prenom AS prof_prenom
                FROM note n
                JOIN classe_matiere cm ON n.classe_matiere_id = cm.id
                JOIN matiere m ON cm.matiere_id = m.id
                JOIN utilisateur u ON cm.professeur_id = u.id
                WHERE n.eleve_id = :eleve_id AND n.semestre = :semestre
                GROUP BY m.id, cm.coefficient, u.nom, u.prenom
            """)
            
            resultats = conn.execute(query, {"eleve_id": eleve_id, "semestre": semestre}).mappings().fetchall()
            return resultats
    except Exception as e:
        print(f"Erreur génération bulletin : {e}")
        return []
#---------------------------------------------------------------------------------
# ------------ LES METHODES DE L'ESPACE ELEVE ------------
# ---------------------------------------------------------------------------------
def get_absences_by_eleve(eleve_id):
    """Récupère toutes les absences d'un élève spécifique"""
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT a.id, m.nom AS matiere_nom, a.date_absence, a.justifiee, a.motif_justification, a.fichier_justificatif
                FROM absence a
                JOIN classe_matiere cm ON a.classe_matiere_id = cm.id
                JOIN matiere m ON cm.matiere_id = m.id
                WHERE a.eleve_id = :eleve_id
                ORDER BY a.date_absence DESC
            """)
            return conn.execute(query, {"eleve_id": eleve_id}).mappings().fetchall()
    except Exception as e:
        print(f"Erreur SQL lecture absences élève : {e}")
        return []

def get_absence_by_id_for_eleve(absence_id, eleve_id):
    """Verifies that the absence belongs to the student before allowing justification."""
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT id, justifiee 
                FROM absence 
                WHERE id = :absence_id AND eleve_id = :eleve_id
            """)
            return conn.execute(query, {"absence_id": absence_id, "eleve_id": eleve_id}).mappings().fetchone()
    except Exception as e:
        print(f"Erreur SQL get_absence_by_id_for_eleve : {e}")
        return None

def submit_justification_eleve(absence_id, eleve_id, file_url):
    """Saves the justification file URL and marks the absence as pending review."""
    try:
        with engine.begin() as conn:
            query = text("""
                UPDATE absence 
                SET fichier_justificatif = :file_url
                WHERE id = :absence_id AND eleve_id = :eleve_id
            """)
            conn.execute(query, {
                "file_url": file_url,
                "absence_id": absence_id,
                "eleve_id": eleve_id
            })
            return True
    except Exception as e:
        print(f"Erreur SQL submit_justification : {e}")
        return False

# ---------------------------------------------------------------------------------
# ------------ FONCTIONS ESPACE PROFESSEUR (migrées depuis database.py racine) ----
# ---------------------------------------------------------------------------------

def get_eleves_par_classe(classe_id):
    try:
        with engine.connect() as conn:
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
            conn.commit()
            return True
    except Exception as e:
        print(f"Erreur lors de l'enregistrement de la note : {e}")
        return False

def enregistrer_notes_completes(eleve_id, matiere, cc1, cc2, exam, moyenne):
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
            return conn.execute(query, {"id": user_id}).mappings().first()
    except Exception as e:
        print(f"Erreur lors de la récupération de l'utilisateur : {e}")
        return None

def enregistrer_absence(eleve_id, date_abs, statut, justification):
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
        with engine.connect() as conn:
            query = text("""
                SELECT cm.classe_id, cm.matiere_id, c.nom AS nom_classe, m.nom AS nom_matiere
                FROM classe_matiere cm
                JOIN classe c ON cm.classe_id = c.id
                JOIN matiere m ON cm.matiere_id = m.id
                WHERE cm.professeur_id = :id
                LIMIT 1
            """)
            return conn.execute(query, {"id": prof_id}).mappings().first()
    except Exception as e:
        print(f"Erreur lors de la récupération des infos prof : {e}")
        return None

def get_notes_existantes(classe_matiere_id):
    try:
        with engine.connect() as conn:
            query = text("SELECT eleve_id, valeur, type_evaluation FROM note WHERE classe_matiere_id = :cm_id")
            result = conn.execute(query, {"cm_id": classe_matiere_id}).mappings().fetchall()
            
            notes_dict = {}
            for r in result:
                e_id = r['eleve_id']
                if e_id not in notes_dict:
                    notes_dict[e_id] = {'note_cc1': None, 'note_cc2': None, 'note_cc3': None, 'note_cc4': None}
                
                t_eval = r['type_evaluation']
                if t_eval in ['cc1', 'cc2', 'cc3', 'cc4']:
                    notes_dict[e_id][f'note_{t_eval}'] = r['valeur']
                elif t_eval == 'controle':
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
