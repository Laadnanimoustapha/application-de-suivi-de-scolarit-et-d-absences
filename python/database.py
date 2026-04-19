import os
from sqlalchemy import create_engine, text 

DATABASE_KEY = os.getenv("DATABASE")

engine = create_engine(DATABASE_KEY, connect_args={"ssl":{}}, pool_pre_ping =True , pool_recycle = 300)

def check_users (username,password): # check if the user has an account 
    with engine.connect() as conn:
        query = text("SELECT * FROM users WHERE username = :username AND password = :password")
        result = conn.execute(query,{"username" : username,"password" : password}).fetchone()

        return result is not None 

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

def add_etudiant(username,email,password): # add a new student 
    with engine.connect() as conn:
        query = text("INSERT INTO etudiant (username,email,password) VALUES (:username,:email,:password)")
        conn.execute(query,{"username" : username,"email" : email,"password" : password})
        conn.commit()

        return True 

def add_professeur(username,email,password): # add a new profesor 
    with engine.connect() as conn:
        query = text("INSERT INTO professeur (username,email,password) VALUES (:username,:email,:password)")
        conn.execute(query,{"username" : username,"email" : email,"password" : password})
        conn.commit()

        return True 

def search_etudiant(username): # search for a student 
    with engine.connect() as conn:
        query = text("SELECT * FROM etudiant WHERE username = :username")
        result = conn.execute(query,{"username" : username}).fetchone()

        return result is not None 

def search_professeur(username): # search for a profesor 
    with engine.connect() as conn:
        query = text("SELECT * FROM professeur WHERE username = :username")
        result = conn.execute(query,{"username" : username}).fetchone()

        return result is not None 
    