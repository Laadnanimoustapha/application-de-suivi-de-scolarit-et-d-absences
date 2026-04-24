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

def check_admin(username,password): # check if the admin has an account 
    with engine.connect() as conn:
        query = text("SELECT * FROM admin WHERE username = :username AND password = :password")
        result = conn.execute(query,{"username" : username,"password" : password}).fetchone()

        return result is not None 