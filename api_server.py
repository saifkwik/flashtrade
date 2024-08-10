from fastapi import FastAPI
from fastapi.responses import JSONResponse

from stock_update import get_data

app = FastAPI()


@app.get("/")
def root():
    return {"message": "Flash Trade API"}


@app.post("/crawl")
def crawl_start():
    result = get_data(force_send=False)
    return JSONResponse(content={"messages": result})


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app)