from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI backend!"}

@app.get("/health/{name}")
def greet_user(name: str):
    return {"greeting": f"FastAPI is running, {name}!"}
