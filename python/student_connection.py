import os
from sqlalchemy import create_engine, text 
from dotenv import load_dotenv
from datetime import datetime
import random

load_dotenv()

DATABASE_KEY = os.getenv("DATABASE")

if not DATABASE_KEY:
    raise ValueError("The 'DATABASE' environment variable is not set. Please set it in your environment or in a .env file.")

engine = create_engine(DATABASE_KEY, pool_pre_ping=True, pool_recycle=300)

# check if the student has an account 
def check_etudiant(email,password): 
    with engine.connect() as conn:
        query = text("SELECT * FROM etudiant WHERE email = :email AND password = :password")
        result = conn.execute(query,{"email" : email,"password" : password}).fetchone()

        return result is not None 

# check if the profesor has an account
def check_professeur(email,password):  
    with engine.connect() as conn:
        query = text("SELECT * FROM professeur WHERE email = :email AND password = :password")
        result = conn.execute(query,{"email" : email,"password" : password}).fetchone()

        return result is not None    

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

