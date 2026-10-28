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
│   ├── components/          # Componentes locais da interface
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
- `PERSISTIR_SESSAO_NAVEGADOR` controla a restauração da sessão ao recarregar a mesma aba (`true` por padrão).

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

### Atualizar após alterações no código

Os Dockerfiles copiam os diretórios `App/` e `View/` para dentro das imagens.
Por isso, alterações no backend, no frontend, em `pyproject.toml`, em `uv.lock`
ou nos Dockerfiles exigem uma nova imagem. Para aplicar as alterações atuais,
execute na raiz do projeto:

```powershell
docker compose up --build -d
```

Não é necessário executar `docker compose down` nem remover volumes para uma
atualização normal. O volume `mysql_data` é preservado. Para uma alteração
somente na interface, é possível reconstruir apenas o frontend:

```powershell
docker compose up --build -d frontend
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

- `POST /auth/login`: recebe `email` e `password`; retorna um token Bearer.
- `POST /predict/predictAI`: recebe uma lista multipart no campo `files` e retorna
  os resultados completos da análise. Requer autenticação.
- `GET /reports/reportpdf`: recebe no corpo JSON os dados do paciente e o
  resultado completo da predição; gera e retorna o relatório como arquivo PDF
  para download. Requer autenticação.
- `GET /user/me`: retorna os dados do usuário autenticado.
- `GET /user/userByEmail`: consulta um usuário por e-mail; requer administrador.
- `POST /user/userRegister`: cadastra um usuário; requer administrador.
- `PUT /user/userUpdate_email`: atualiza um usuário; requer administrador.
- `DELETE /user/userDelete_email`: remove um usuário; requer administrador.

Os resultados bem-sucedidos da predição seguem o contrato `predict`,
`total_fraturas`, `detections` e `final_img`. Esse mesmo resultado é enviado
pela interface ao endpoint de relatório, sem conversão de nomes.

### Geração do relatório em PDF

Na tela de resultados, a interface permite gerar e baixar um relatório PDF com
os dados do paciente, os dados do profissional autenticado e o resumo da
análise. Resultados individuais com sucesso podem incluir a imagem anotada e
suas detecções; itens com erro são omitidos dessa seção, mas aparecem na
contagem geral do relatório. O documento também informa que o resultado é
auxiliar e não substitui a avaliação de um profissional habilitado.

O endpoint `GET /reports/reportpdf` requer autenticação Bearer e recebe um
corpo JSON com esta estrutura:

```json
{
  "pacienteInfo": {
    "name": "Nome do paciente",
    "sexo": "Feminino",
    "ladoAnalisado": "Direito",
    "dataNcmto": "1990-01-31"
  },
  "resultadosInfo": {
    "status": "total_success",
    "total": 1,
    "sucessos": 1,
    "erros": 0,
    "resultados": [
      {
        "sucesso": true,
        "predict": "Nenhuma indicação de fratura",
        "total_fraturas": 0,
        "detections": [],
        "final_img": "BASE64_DA_IMAGEM_PNG"
      }
    ]
  }
}
```

`dataNcmto` deve estar no formato `AAAA-MM-DD`. `resultadosInfo` deve seguir o
mesmo formato retornado por `/predict/predictAI`; `final_img` contém a imagem
anotada em Base64. A resposta é `application/pdf`, enviada como anexo com o
nome `relatorio.pdf`. Embora use o método `GET`, essa rota recebe os dados no
corpo JSON; clientes HTTP precisam suportar esse formato de requisição.

#### Gerar um PDF de teste sem rebuild

Na raiz do repositório, execute no PowerShell:

```powershell
uv run --no-sync --group api python -m Testes.gerar_relatorio_teste
```

O comando gera um PDF em `Testes/arquivos_testes/` com dados, detecção e
imagem ilustrativos, todos fictícios. O nome inclui data e hora
(`relatorio_teste_AAAAMMDD_HHMMSS_microsegundos.pdf`) para preservar cada
execução. Para gerar também a imagem de teste (com mais de 5 MB), execute:

```powershell
uv run --no-sync --group api python Testes\gerar_imagem_teste.py
```

A imagem será salva em `Testes/arquivos_testes/`, com data e hora no nome
(`imagem_teste_AAAAMMDD_HHMMSS_microsegundos.png`). Não é necessário iniciar a
API, conectar ao banco ou reconstruir as imagens Docker; as dependências do
grupo `api` devem estar instaladas no ambiente local.

## Interface e sessão

A navegação da interface usa os parâmetros `pagina` e `modo` na URL. Isso
permite que os botões Voltar/Avançar do navegador restaurem a tela anterior e
que a página atual seja mantida ao recarregar.

Por padrão, o token de acesso é mantido em `sessionStorage`: ele sobrevive a
recarregamentos na mesma aba e é apagado ao sair da conta ou fechar a aba. O
token não é colocado na URL. Para desativar esse comportamento, inicie o
frontend com a variável `PERSISTIR_SESSAO_NAVEGADOR=false`.

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
- **A interface ou API continua exibindo uma versão anterior:** execute
  `docker compose up --build -d`. Os containers em execução não recebem os
  arquivos modificados no computador automaticamente.
