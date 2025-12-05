from fastapi import FastAPI
from mongo import db
app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello World"}