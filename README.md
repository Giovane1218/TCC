# Análise de fraturas em radiografias do punho

Aplicação composta por uma API FastAPI e uma interface Streamlit para analisar radiografias do punho usando um modelo YOLO treinado.

## Estrutura do projeto

```text
.
├── App/
│   ├── api/                 # Rotas HTTP
│   ├── core/                # Configuração, segurança, erros e modelo YOLO
│   ├── database/            # Conexão e execução de migrações
│   ├── models/              # Modelos SQLAlchemy
│   ├── repositories/        # Acesso a dados
│   ├── schemas/             # Schemas Pydantic
│   ├── services/            # Senhas e tokens
│   ├── usecases/            # Casos de uso da aplicação
│   └── main.py              # Aplicação FastAPI
├── View/
│   ├── assets/              # Imagens e recursos da interface
│   └── app.py               # Aplicação Streamlit
├── migrations/              # Migrações Alembic
├── Testes/                  # Scripts de teste e manutenção
├── Documentação/            # Documentação complementar
├── Dockerfile.back          # Imagem da API
├── Dockerfile.front         # Imagem do frontend
├── compose.yaml             # API, frontend e MySQL
├── pyproject.toml           # Dependências e configuração do projeto
└── uv.lock                  # Versões resolvidas pelo uv
```

O arquivo de pesos do modelo deve estar em `App/core/yolo_model/pesos/best.pt`. A imagem Docker da API copia a pasta `App`, incluindo esse arquivo.

## Executar com Docker

### Pré-requisitos

- Docker Desktop (Windows/macOS) ou Docker Engine com o plugin Docker Compose (Linux).
- O arquivo de pesos `App/core/yolo_model/pesos/best.pt`.

### Configurar o ambiente

No PowerShell, a partir da raiz do repositório, crie o arquivo `.env` a partir do exemplo:

```powershell
Copy-Item .env.example .env
```

Edite `.env` e substitua os valores de exemplo. Configure:

- `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD` e `MYSQL_ROOT_PASSWORD` para o banco de dados.
- `AUTH_SECRET_KEY` com uma chave aleatória de pelo menos 32 caracteres. Para gerar uma no PowerShell com Python instalado:

  ```powershell
  python -c "import secrets; print(secrets.token_hex(32))"
  ```

- `ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `ADMIN_REGISTRO_PROFISSIONAL`, `ADMIN_CARGO` e `ADMIN_UF_REGISTRO` para a criação do primeiro administrador. A senha precisa ter pelo menos 12 caracteres.

Não compartilhe nem versione o arquivo `.env`. O Compose configura o endereço interno do banco para a API automaticamente; `MYSQL_HOST` e `MYSQL_PORT` no `.env.example` servem para execução fora do Compose, enquanto a porta publicada no host é controlada por `MYSQL_PORT` (padrão `3306`).

### Construir e iniciar

Na raiz do projeto:

```powershell
docker compose up --build
```

O Compose inicia o MySQL, aguarda o banco ficar saudável e então inicia a API e o frontend. Na primeira inicialização, a API executa as migrações e cria o administrador inicial se ainda não existir.

- Interface Streamlit: <http://localhost:8501>
- Documentação interativa da API: <http://localhost:8000/docs>

Para executar em segundo plano:

```powershell
docker compose up --build -d
```

Ver os logs:

```powershell
docker compose logs -f api frontend
```

Parar os serviços:

```powershell
docker compose down
```

O banco permanece salvo no volume Docker `mysql_data`. Para apagar também os dados persistidos do banco, use `docker compose down --volumes`; essa operação é destrutiva e remove os dados do MySQL.

## Serviços e rotas da API

- `POST /auth/login`: autentica um usuário e retorna um token Bearer.
- `POST /predict/predictAI`: recebe imagens no campo multipart `files` e retorna os resultados da análise. Requer autenticação.
- `GET /user/me`: retorna os dados do usuário autenticado.
- `GET /user/userByEmail`: consulta um usuário por e-mail; requer administrador.
- `POST /user/userRegister`: cadastra um usuário; requer administrador.
- `PUT /user/userUpdate_email`: atualiza um usuário; requer administrador.
- `DELETE /user/userDelete_email`: remove um usuário; requer administrador.

## Dependências

O projeto usa `uv` para gerenciar as dependências Python. As imagens Docker instalam os grupos definidos em `pyproject.toml` usando `uv.lock`: o grupo `api` no serviço da API e o grupo `frontend` no Streamlit. Para atualizar o ambiente local com ambos os grupos, instale o uv e execute:

```powershell
uv sync --all-groups
```

## Solução de problemas

- **A API não inicia:** verifique os logs com `docker compose logs -f api`. Confirme se as variáveis do `.env` estão preenchidas e se `AUTH_SECRET_KEY` tem pelo menos 32 caracteres.
- **Erro de conexão com MySQL:** veja `docker compose logs -f db` e aguarde o healthcheck do banco. No Compose, a API se conecta ao serviço `db` pela rede interna.
- **Falha ao carregar o modelo:** confirme que `App/core/yolo_model/pesos/best.pt` existe antes de construir a imagem.
- **Porta ocupada:** ajuste `MYSQL_PORT` para a porta publicada do banco ou libere as portas `8000`, `8501` e `3306`, conforme aplicável.
- **Build falha em `apt-get update`:** essa etapa instala bibliotecas de sistema da imagem da API; ela acontece antes do `uv sync` e não é corrigida alterando as dependências Python.
