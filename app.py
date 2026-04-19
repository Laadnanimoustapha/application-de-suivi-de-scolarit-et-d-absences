from fastapi import FastAPI,HTTPException
from python.database import *
import python.models
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (JS, CSS)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def main_function():
    return {"statu":"server is runing"}

@app.post("/login/etudiant")
def login_etudiant(etudiant: dict):
    if check_etudiant(etudiant["email"],etudiant["password"]):
        return {"statu":"login successfully"}
    else:
        return {"statu":"login failed"}

@app.post("/login/professeur")
def login_professeur(professeur: dict):
    if check_professeur(professeur["email"],professeur["password"]):
        return {"statu":"login successfully"}
    else:
        return {"statu":"login failed"}

@app.post("/login/admin")
def login_admin(admin: dict):
    if check_users(admin["username"],admin["password"]):
        return {"statu":"login successfully"}
    else:
        return {"statu":"login failed"}
