from fastapi import FastAPI
from test import hello

app = FastAPI()

def test_func(test):
	return test * test

@app.get("/api/test")
def read_root():
    return {"Hello": test_func(19)}

@app.get("/api/hello")
def read_root():
    return {"Hello": hello()}