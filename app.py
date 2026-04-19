from fastapi import FastAPI,HTTPException
import python.database
import python.models

app = FastAPI()

@app.get("/")
def main_function():
    return {"statu":"server is runing"}