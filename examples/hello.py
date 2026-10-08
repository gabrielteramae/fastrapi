from fastrapi import FastrAPI

app = FastrAPI()


@app.get("/")
def root(request):
    return {"framework": "fastrapi", "ok": True}


@app.get("/items/{item_id}")
def read_item(request):
    return {"item_id": request.path_params["item_id"], "q": request.query.get("q")}


@app.post("/echo")
async def echo(request):
    data = await request.json()
    return {"echo": data}
