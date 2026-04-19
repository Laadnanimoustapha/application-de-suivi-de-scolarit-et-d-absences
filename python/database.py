import os
from sqlalchemy import create_engine, text 

DATABASE_KEY = os.getenv("DATABASE")

engine = create_engine(DATABASE_KEY, pool_pre_ping =True , pool_recycle = 300)

def check_users (username,password):
    with engine.connect() as conn:
        query = text("SELECT * FROM users WHERE username = :username AND password = :password")
        result = conn.execute(query,{"username" : username,"password" : password}).fetchone()

        return result is not None 