import importlib
import sys

from fastrapi.serve import serve_blocking


def main() -> None:
    target = sys.argv[1] if len(sys.argv) > 1 else "examples.hello:app"
    module_name, _, attr = target.partition(":")
    app = getattr(importlib.import_module(module_name), attr or "app")
    host = "127.0.0.1"
    port = 8000
    print(f"servindo {module_name}:{attr or 'app'} em http://{host}:{port}")
    serve_blocking(app, host, port)


if __name__ == "__main__":
    main()
