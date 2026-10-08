# fastrapi — ASGI no estilo FastAPI, sem dependências

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![ASGI](https://img.shields.io/badge/ASGI-stdlib-3776AB?logo=python&logoColor=white)

Framework ASGI em Python, com a cara do FastAPI: decorators, parâmetro na rota e JSON de volta. O núcleo cabe numa leitura só e **não instala nada** — o servidor HTTP/1.1 sai da biblioteca padrão.

## Por que esta versão?

| Escolha | Motivo |
|---|---|
| Python, não Rust | A ideia original falava em Rust e um “6×”. Esta versão é Python de propósito: dá para ler, testar e mudar sem compilador. |
| Sem número de performance | Não publicamos benchmark contra o FastAPI. O ponto é o miolo, não um número. |
| Sem OpenAPI, middleware empilhado ou WebSocket | Se a rota precisa disso, o FastAPI continua sendo a ferramenta certa. |

## Stack

- **Python 3.11+**, zero dependências (`pyproject.toml`)
- **ASGI** — `FastrAPI` também sobe em qualquer servidor ASGI
- **`unittest`** da biblioteca padrão, com `TestClient` que não abre porta
- Servidor HTTP/1.1 em `fastrapi/serve.py`

## Estrutura

```
fastrapi/
├── __init__.py       # FastrAPI, JSONResponse, Request
├── __main__.py       # python -m fastrapi modulo:app
├── app.py            # rotas, path params, query string, corpo JSON
├── serve.py          # servidor HTTP/1.1 na biblioteca padrão
└── testing.py        # TestClient sem servidor
examples/
└── hello.py          # app de exemplo
tests/
└── test_app.py
```

## Como rodar

Não precisa de `pip install`. Na raiz do repositório:

```bash
git clone https://github.com/gabrielteramae/fastrapi.git
cd fastrapi
python -m unittest discover -s tests -t .
python -m fastrapi examples.hello:app
```

O segundo comando sobe `http://127.0.0.1:8000`. O alvo padrão é `examples.hello:app`; outro módulo entra como `python -m fastrapi pacote.modulo:app`.

```python
from fastrapi import FastrAPI

app = FastrAPI()

@app.get("/items/{item_id}")
def read_item(request):
    return {"item_id": request.path_params["item_id"], "q": request.query.get("q")}

@app.post("/echo")
async def echo(request):
    return {"echo": await request.json()}
```

## O que tem

| Peça | Onde | Descrição |
|---|---|---|
| `GET` `POST` `PUT` `DELETE` | `app.py` | Decorators no estilo FastAPI |
| `/{param}` e query string | `Request` | Path decodificado e `request.query` |
| Corpo JSON | `await request.json()` | Handler sync ou async |
| `TestClient` | `testing.py` | Chama a app sem subir servidor |
| Servidor incluso | `serve.py` | HTTP/1.1 na biblioteca padrão |

## O que não tem

Injeção de tipos, geração de OpenAPI, pilha de middleware e WebSocket.

## Testes realizados

`tests/test_app.py` cobre `GET /`, path com espaço (`abc%20d`) mais query, `POST` com JSON, rota inexistente → 404, exceção na rota → 500 com `detail` em JSON, e uma requisição HTTP de verdade contra o servidor da biblioteca padrão em porta efêmera.

---

© 2026 Gabriel Teramae Chan
