# Dantas Comércio API

API REST para gestão de pequenos comércios, feita com **FastAPI** e **Python**. Cobre cadastro de clientes e produtos, vendas com controle de estoque, **fiado** (venda a prazo com limite e pagamentos parciais), **fluxo de caixa** com relatórios e **autenticação JWT** com dois papéis de usuário.

O projeto foi pensado a partir de uma necessidade real do comércio local: vender no balcão, anotar o fiado do cliente e saber, no fim do dia, quanto entrou e saiu do caixa.

## Funcionalidades

- **Clientes**: cadastro, busca por nome, limite de fiado e saldo devedor.
- **Produtos**: cadastro, controle de estoque e listagem de produtos com estoque baixo.
- **Vendas**: venda com vários itens, baixa automática de estoque, pagamento em dinheiro, pix, cartão ou fiado, e cancelamento com estorno.
- **Fiado**: limite por cliente, pagamento parcial ou total, extrato do cliente e lista de devedores.
- **Fluxo de caixa**: despesas e entradas avulsas, saldo, listagem com filtros e relatório por dia ou por mês.
- **Autenticação**: login com token JWT e papéis de **dono** e **funcionário**.

## Tecnologias

| Área | Tecnologia |
|---|---|
| Framework | FastAPI |
| Banco de dados | SQLite (desenvolvimento) com SQLModel / SQLAlchemy |
| Validação | Pydantic |
| Autenticação | PyJWT e hash de senha com Argon2 (pwdlib) |
| Servidor | Uvicorn |
| Qualidade | pytest, pytest-cov e ruff (no `requirements.txt`) |

## Estrutura do projeto

```
comercio-api/
├── app/
│   ├── main.py            # criação do app e registro dos routers
│   ├── deps.py            # usuário logado e checagem de papel
│   ├── core/
│   │   ├── config.py      # configurações lidas do .env
│   │   └── security.py    # hash de senha e tokens JWT
│   ├── db/
│   │   └── session.py     # engine e sessão do banco
│   ├── models/            # tabelas do banco (SQLModel)
│   ├── schemas/           # formato de entrada e saída da API (Pydantic)
│   ├── routers/           # endpoints (só recebem e respondem)
│   └── services/          # regras de negócio (venda, fiado, caixa)
├── scripts/
│   └── create_owner.py    # cria o primeiro usuário (dono)
├── requirements.txt
└── .env.example
```

A requisição segue sempre o mesmo caminho:

```
router → schema (valida a entrada) → service (regra de negócio) → model (banco)
```

Os routers não têm regra de negócio. Tudo que mexe em mais de uma tabela fica nos `services`, o que facilita testar e alterar o sistema.

## Como executar

**Pré-requisito:** Python 3.11 ou superior.

```bash
# 1. Clonar o repositório
git clone <URL-DO-REPOSITORIO>
cd comercio-api

# 2. Criar e ativar o ambiente virtual
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS

# 3. Instalar as dependências
pip install -r requirements.txt

# 4. Configurar as variáveis de ambiente
copy .env.example .env         # Windows
# cp .env.example .env         # Linux / macOS
```

Gere uma chave secreta e coloque no `.env`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

```bash
# 5. Criar o primeiro usuário (dono)
python -m scripts.create_owner

# 6. Subir o servidor
uvicorn app.main:app --reload
```

A documentação interativa (Swagger) fica em **http://127.0.0.1:8000/docs**.

### Variáveis de ambiente

| Variável | Descrição | Exemplo |
|---|---|---|
| `DATABASE_URL` | Endereço do banco de dados | `sqlite:///./comercio.db` |
| `SECRET_KEY` | Chave que assina os tokens JWT. Mantenha em segredo | (gerada no passo acima) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Validade do token, em minutos | `60` |

## Autenticação e permissões

O login recebe **formulário** (e não JSON), seguindo o padrão OAuth2. O e-mail vai no campo `username`:

```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -d "username=dono@exemplo.com&password=sua-senha"
```

A resposta traz o `access_token`, que deve ser enviado nas próximas requisições:

```
Authorization: Bearer <access_token>
```

No Swagger, o botão **Authorize** faz isso automaticamente.

| Recurso | Funcionário | Dono |
|---|:---:|:---:|
| Clientes, produtos, vendas e fiado | ✅ | ✅ |
| Fluxo de caixa (`/cash`) | ❌ | ✅ |
| Criar usuários (`POST /auth/users`) | ❌ | ✅ |

Não existe cadastro público: só o dono cria novos usuários. O primeiro dono é criado pelo script `create_owner`.

## Endpoints

### Auth
| Método | Rota | Descrição | Acesso |
|---|---|---|---|
| POST | `/auth/login` | Login e geração do token | Público |
| GET | `/auth/me` | Dados do usuário logado | Logado |
| POST | `/auth/users` | Criar usuário | Dono |

### Clientes
| Método | Rota | Descrição |
|---|---|---|
| POST | `/clientes/` | Cadastrar cliente |
| GET | `/clientes/` | Listar (filtro `q` por nome, paginação) |
| GET | `/clientes/{id}` | Consultar cliente |
| PATCH | `/clientes/{id}` | Atualização parcial |
| DELETE | `/clientes/{id}` | Desativar (recusado se houver dívida) |

### Produtos
| Método | Rota | Descrição |
|---|---|---|
| POST | `/produtos/` | Cadastrar produto |
| GET | `/produtos/` | Listar produtos |
| GET | `/produtos/estoque-baixo` | Produtos com estoque no mínimo ou abaixo |
| GET | `/produtos/{id}` | Consultar produto |
| PATCH | `/produtos/{id}` | Atualização parcial |
| DELETE | `/produtos/{id}` | Desativar produto |

### Vendas
| Método | Rota | Descrição |
|---|---|---|
| POST | `/sales/` | Registrar venda |
| GET | `/sales/` | Listar vendas (mais recentes primeiro) |
| GET | `/sales/{id}` | Consultar venda com itens |
| POST | `/sales/{id}/cancel` | Cancelar venda (estorno) |

### Fiado
| Método | Rota | Descrição |
|---|---|---|
| POST | `/fiado/payments` | Registrar pagamento da dívida |
| GET | `/fiado/debtors` | Clientes devedores |
| GET | `/fiado/clients/{id}/statement` | Extrato do cliente (vendas no fiado e pagamentos) |

### Caixa (somente dono)
| Método | Rota | Descrição |
|---|---|---|
| POST | `/cash/entries` | Lançar despesa ou entrada avulsa |
| GET | `/cash/entries` | Listar lançamentos (filtros por período, tipo e origem) |
| GET | `/cash/balance` | Entradas, saídas e saldo (com filtro de período) |
| GET | `/cash/report` | Relatório por dia ou mês (`group_by=day` ou `month`) |

## Exemplos de uso

**Venda à vista com dois produtos**

```json
POST /sales/
{
  "payment_method": "pix",
  "items": [
    { "product_id": 1, "quantity": 2 },
    { "product_id": 2, "quantity": 1 }
  ]
}
```

**Venda no fiado** (exige cliente e respeita o limite dele)

```json
POST /sales/
{
  "client_id": 1,
  "payment_method": "fiado",
  "items": [{ "product_id": 1, "quantity": 4 }]
}
```

**Pagamento parcial do fiado**

```json
POST /fiado/payments
{
  "client_id": 1,
  "amount": 8.00,
  "payment_method": "pix"
}
```

**Relatório do caixa por dia, em um período**

```
GET /cash/report?start=2026-11-01&end=2026-11-30&group_by=day
```

## Regras de negócio

- **Venda atômica:** validar estoque, baixar estoque, gravar a venda e seus itens e lançar no caixa acontecem em uma única transação. Se qualquer passo falha, nada é salvo.
- **Preço congelado:** o preço unitário é gravado no item da venda. Reajustar um produto depois não altera vendas antigas.
- **Itens repetidos:** o mesmo produto enviado duas vezes na venda tem as quantidades somadas.
- **Cancelamento é estorno:** a venda cancelada devolve o estoque, e o caixa recebe uma saída que compensa a entrada. Nada é apagado, então o histórico continua fiel.
- **Fiado:**
  - exige cliente cadastrado e respeita o limite dele;
  - não gera lançamento no caixa, porque o dinheiro ainda não entrou;
  - o pagamento (parcial ou total) abate o saldo devedor e **aí sim** entra no caixa;
  - não é possível pagar mais do que o cliente deve;
  - cancelar uma venda no fiado é recusado quando o cliente já pagou parte da dívida.
- **Exclusão lógica:** clientes e produtos são desativados, não apagados. Um cliente com dívida não pode ser desativado.
- **Dinheiro em `Decimal`:** nenhum valor monetário usa `float`.
- **Datas e fuso horário:** os lançamentos são gravados em UTC, e o relatório agrupa os dias no horário de Belém (`America/Belem`), para uma venda feita à noite não cair no dia seguinte.

## Segurança

- Senhas guardadas com hash **Argon2**, nunca em texto.
- Tokens JWT assinados e com validade configurável.
- Usuário desativado perde o acesso imediatamente, mesmo com token ainda válido.
- Login com a mesma mensagem de erro para e-mail inexistente e senha errada, para não revelar quais e-mails existem.
- A chave secreta e o banco ficam fora do repositório (`.env` e `*.db` no `.gitignore`).

## Próximos passos

- [ ] Testes automatizados com pytest
- [ ] Migrações com Alembic
- [ ] Migração para PostgreSQL
- [ ] Registro de qual usuário realizou cada venda e lançamento (auditoria)
- [ ] Deploy
