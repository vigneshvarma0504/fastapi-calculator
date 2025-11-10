<<<<<<< HEAD
﻿from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "FastAPI is running!"}
=======
# main.py
from fastapi import FastAPI, HTTPException
import logging
import operations

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

app = FastAPI()

@app.get("/")
def home():
    logging.info("Home endpoint accessed")
    return {"message": "Welcome to FastAPI Calculator"}

@app.get("/add")
def add(a: float, b: float):
    logging.info(f"Adding {a} and {b}")
    return {"result": operations.add(a, b)}

@app.get("/subtract")
def subtract(a: float, b: float):
    logging.info(f"Subtracting {b} from {a}")
    return {"result": operations.subtract(a, b)}

@app.get("/multiply")
def multiply(a: float, b: float):
    logging.info(f"Multiplying {a} and {b}")
    return {"result": operations.multiply(a, b)}

@app.get("/divide")
def divide(a: float, b: float):
    try:
        logging.info(f"Dividing {a} by {b}")
        return {"result": operations.divide(a, b)}
    except ValueError as e:
        logging.error("Division by zero attempted")
        raise HTTPException(status_code=400, detail=str(e))
>>>>>>> b13569bf79b96dbc2493284b4ae61c3f488c7534
