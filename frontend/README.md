# Front-end — Banco Digital

Front-end simples para o Banco Digital feito com HTML, CSS e JavaScript puro.

## Arquivos
- `index.html`: telas de login, cadastro e painel.
- `style.css`: estilos.
- `script.js`: integração com a API.

## Executar
1. Inicie o backend na pasta do projeto:
   `uvicorn app.main:app --reload`
2. Abra `index.html` no navegador.
3. A API deve estar em `http://127.0.0.1:8000`.

## Observação
O backend atual cria o número da conta como `1000 + id do usuário`; o front-end usa a mesma regra após o login.
