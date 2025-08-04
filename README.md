# Instalação
- Instale o [UV](https://docs.astral.sh/uv/getting-started/installation/): `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Instale as dependências com `uv sync`

# Rodando
## BD
- Instale o Docker
- `docker build -t postgres .`
- `docker run --name postgres -d -p 5432:5432 postgres:latest`
## API
- Modo dev com `uv run fastapi dev`
- Modo produção com `uv run fastapi run`
- Testes com `uv run -m unittest`