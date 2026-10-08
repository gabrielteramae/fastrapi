# fastrapi

Framework ASGI em Python, com a cara do FastAPI: decorators, parâmetros na rota e JSON de volta. O núcleo cabe numa leitura só. Não tem dependências.

A ideia original falava em Rust e um número de “6× mais rápido”. Esta versão é Python de propósito — dá para ler, testar e mudar sem compilador. Não publicamos benchmark contra o FastAPI.

## Rodar

```bash
python -m unittest discover -s tests -t .
python -m fastrapi examples.hello:app
```

O segundo comando sobe `http://127.0.0.1:8000`. `app` também é ASGI puro: qualquer servidor ASGI serve.

```python
from fastrapi import FastrAPI

app = FastrAPI()

@app.get("/items/{item_id}")
def read_item(request):
    return {"item_id": request.path_params["item_id"]}

@app.post("/echo")
async def echo(request):
    return {"echo": await request.json()}
```

## O que tem

- `GET` `POST` `PUT` `DELETE`
- caminho `/{param}` e query string
- corpo JSON
- `TestClient` sem servidor
- servidor HTTP/1.1 na biblioteca padrão

## O que não tem

Injeção de tipos, OpenAPI, middleware empilhado, WebSocket. Se a rota precisa disso, o FastAPI continua sendo a ferramenta certa.
