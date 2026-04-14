from fastapi import FastAPI,HTTPException

app = FastAPI()

@app.get("/")
def main_function():
    return {"statu":"server is runing"}