from fastapi import FastAPI

from src.dtos.ISayHelloDto import ISayHelloDto
from src.outline import *

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.post("/hello")
async def hello_message(dto: ISayHelloDto):
    return {"message": f"Hello {dto.message}"}


@app.get("/amz/{keyword}")
async def getLastMonthsales(keyword: str):
    result = run(keyword)
    return {"keyword": keyword, "json": result}
