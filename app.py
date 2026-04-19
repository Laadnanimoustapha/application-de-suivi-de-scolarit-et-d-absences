from fastapi import FastAPI,HTTPException
from python.database import *
import python.models
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def main_function():
    return {"statu":"server is runing"}

@app.post("/login/etudiant")
def login_etudiant(etudiant: dict):
    if check_etudiant(etudiant["email"],etudiant["password"]):
        return {"statu":"login successfully"}
    else:
        return {"statu":"login failed"}
