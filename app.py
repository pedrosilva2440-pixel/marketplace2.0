import os
import sqlite3
import uuid
from functools import wraps

from flask import (
Flask,
request,
redirect,
url_for,
session,
flash,
abort,
send_from_directory,
render_template_string
)

from werkzeug.security import (
generate_password_hash,
check_password_hash
)

from werkzeug.utils import secure_filename


# ============================================================
# MARKETCLASS
# Marketplace escolar - tudo em um único app.py
# ============================================================

app = Flask(__name__)

# ------------------------------------------------------------
# CONFIGURAÇÕES
# ------------------------------------------------------------

app.secret_key = os.environ.get(
"SECRET_KEY",
"marketclass-chave-local-2026"
)

DATABASE = os.environ.get(
"DATABASE_PATH",
"marketclass.db"
)

UPLOAD_FOLDER = os.environ.get(
"UPLOAD_FOLDER",
"uploads"
)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ============================================================
# ADMINISTRADOR
# ============================================================

# Você pode colocar esses valores como Environment Variables
# no Render.
#
# ADMIN_EMAIL
# ADMIN_PASSWORD
#
# Caso não configure no Render, serão usados os valores abaixo.

ADMIN_EMAIL = os.environ.get(
"ADMIN_EMAIL",
"andrade1777791@gmail.com"
)

ADMIN_PASSWORD = os.environ.get(
"ADMIN_PASSWORD",
"pedro2009"
)

ADMIN_WHATSAPP = "5584999502071"


# ============================================================
# CONFIGURAÇÕES GERAIS
# ============================================================

ALLOWED_EXTENSIONS = {
"png",
"jpg",
"jpeg",
"webp"
}

MAX_IMAGE_SIZE = 5 * 1024 * 1024

app.config["MAX_CONTENT_LENGTH"] = MAX_IMAGE_SIZE


# ============================================================
# BANCO DE DADOS
# ============================================================

def get_db():
db = sqlite3.connect(DATABASE)
db.row_factory = sqlite3.Row
return db


def init_db():

db = get_db()

db.execute("""
CREATE TABLE IF NOT EXISTS usuarios (

id INTEGER PRIMARY KEY AUTOINCREMENT,

nome TEXT NOT NULL,

email TEXT UNIQUE NOT NULL,

senha TEXT NOT NULL,

contato TEXT NOT NULL,

tipo TEXT NOT NULL
CHECK(tipo IN ('comprador', 'vendedor')),

aprovado INTEGER NOT NULL DEFAULT 0,

criado_em TIMESTAMP
DEFAULT CURRENT_TIMESTAMP
)
""")

db.execute("""
CREATE TABLE IF NOT EXISTS produtos (

id INTEGER PRIMARY KEY AUTOINCREMENT,

usuario_id INTEGER NOT NULL,

nome TEXT NOT NULL,

categoria TEXT NOT NULL,

preco REAL NOT NULL,

conservacao TEXT NOT NULL,

tamanho TEXT,

descricao TEXT,

imagem TEXT,

criado_em TIMESTAMP
DEFAULT CURRENT_TIMESTAMP,

FOREIGN KEY(usuario_id)
REFERENCES usuarios(id)
)
""")

db.commit()
db.close()


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def allowed_file(filename):

if "." not in filename:
return False

extensao = filename.rsplit(".", 1)[1].lower()

return extensao in ALLOWED_EXTENSIONS


def limpar_whatsapp(numero):

if not numero:
return ""

numero = (
numero
.replace(" ", "")
.replace("(", "")
.replace(")", "")
.replace("-", "")
.replace("+", "")
)

if numero.startswith("55"):
return numero

return "55" + numero


def usuario_logado():

return "usuario_id" in session


def eh_admin():

return session.get("admin") is True


def vendedor_aprovado():

if not usuario_logado():
return False

if session.get("tipo") != "vendedor":
return False

db = get_db()

usuario = db.execute("""
SELECT aprovado
FROM usuarios
WHERE id = ?
""", (session["usuario_id"],)).fetchone()

db.close()

return bool(usuario and usuario["aprovado"] == 1)


def exigir_login():

if not usuario_logado() and not eh_admin():

flash(
"Você precisa entrar na sua conta."
)

return False

return True


def exigir_admin():

if not eh_admin():

flash(
"Acesso permitido somente ao administrador."
)

return False

return True


def render_page(conteudo, titulo="MarketClass"):

return render_template_string(
BASE_HTML,
titulo=titulo,
conteudo=conteudo
)


# ============================================================
# CSS
# ============================================================

CSS = """

:root {
--purple: #6f2dbd;
--purple-dark: #4b168a;
--orange: #ff8500;
--green: #159447;
--red: #d63031;
--bg: #f7f5fa;
--text: #202124;
--muted: #777;
--border: #e5e0ea;
--white: #ffffff;
}

* {
box-sizing: border-box;
}

html {
scroll-behavior: smooth;
}

body {
margin: 0;
font-family:
Arial,
Helvetica,
sans-serif;

background: var(--bg);
color: var(--text);
}

a {
text-decoration: none;
color: inherit;
}

button,
input,
select,
textarea {
font-family: inherit;
}

header {
background: white;
border-bottom: 1px solid var(--border);
position: sticky;
top: 0;
z-index: 1000;
}

.navbar {
max-width: 1200px;
min-height: 70px;
margin: auto;
padding: 10px 20px;

display: flex;
align-items: center;
gap: 20px;
}

.logo {
font-size: 28px;
font-weight: 900;
color: var(--purple);
white-space: nowrap;
}

.logo span {
color: var(--orange);
}

.school {
color: var(--muted);
font-size: 13px;
margin-right: auto;
}

nav {
display: flex;
align-items: center;
gap: 5px;
flex-wrap: wrap;
}

nav a {
padding: 9px 10px;
font-size: 14px;
border-radius: 8px;
}

nav a:hover {
background: #f1e8ff;
}

.btn {
display: inline-block;
border: none;
border-radius: 10px;

padding: 11px 16px;

background: var(--purple);
color: white;

font-weight: bold;
cursor: pointer;

transition: .2s;
}

.btn:hover {
transform: translateY(-1px);
opacity: .92;
}

.btn-orange {
background: var(--orange);
}

.btn-green {
background: var(--green);
}

.btn-red {
background: var(--red);
}

.btn-gray {
background: #555;
}

.hero {
background:
linear-gradient(
135deg,
var(--purple-dark),
var(--purple)
);

color: white;
padding: 70px 20px;
}

.hero-content {
max-width: 1050px;
margin: auto;
}

.hero h1 {
font-size: 46px;
margin: 0 0 15px;
}

.hero p {
max-width: 750px;
font-size: 18px;
line-height: 1.6;
}

.search {
max-width: 950px;
background: white;
padding: 7px;
border-radius: 12px;

display: flex;
gap: 7px;

margin-top: 25px;
}

.search input,
.search select {
flex: 1;
min-width: 0;

padding: 13px;

border: none;
outline: none;

font-size: 15px;
}

.search button {
background: var(--orange);
color: white;

border: none;
border-radius: 9px;

padding: 0 22px;

font-weight: bold;
cursor: pointer;
}

main {
max-width: 1200px;
margin: auto;
padding: 35px 20px 70px;
}

.section-header {
display: flex;
justify-content: space-between;
align-items: center;

margin-bottom: 20px;
}

.products {
display: grid;
grid-template-columns:
repeat(4, minmax(0, 1fr));

gap: 18px;
}

.product {
background: white;

border: 1px solid var(--border);
border-radius: 16px;

overflow: hidden;

transition: .2s;
}

.product:hover {
transform: translateY(-3px);

box-shadow:
0 8px 25px
rgba(50, 20, 80, .10);
}

.product-image {
width: 100%;
height: 190px;
object-fit: cover;
}

.product-placeholder {
height: 190px;

display: flex;
align-items: center;
justify-content: center;

background: #f1e8ff;

font-size: 60px;
}

.product-content {
padding: 16px;
}

.category {
color: var(--purple);

font-size: 11px;
font-weight: bold;

text-transform: uppercase;
}

.product h3 {
min-height: 42px;
}

.price {
color: var(--purple);

font-size: 21px;
font-weight: 900;
}

.info {
color: var(--muted);
font-size: 13px;
}

.form-card {
max-width: 650px;

margin: 20px auto;

padding: 30px;

background: white;

border:
1px solid var(--border);

border-radius: 18px;
}

.form {
display: grid;
gap: 16px;
}

.form label {
font-weight: bold;
}

.form input,
.form select,
.form textarea {
width: 100%;

margin-top: 6px;

padding: 12px;

border:
1px solid #ddd;

border-radius: 9px;

font-size: 15px;

outline: none;
}

.form input:focus,
.form select:focus,
.form textarea:focus {
border-color: var(--purple);

box-shadow:
0 0 0 3px
rgba(111, 45, 189, .10);
}

.form textarea {
resize: vertical;
}

.tabs {
display: flex;
gap: 8px;

margin-bottom: 20px;
}

.tabs a {
flex: 1;

text-align: center;

padding: 14px;

border-radius: 10px;

background: #eee;

font-weight: bold;
}

.tabs a.active {
background: var(--purple);
color: white;
}

.warning {
background: #fff4df;
color: #8a5700;

padding: 15px;

border-radius: 10px;

margin-bottom: 20px;

line-height: 1.6;
}

.success-box {
background: #e9f8ee;
color: #17652c;

padding: 15px;

border-radius: 10px;

margin-bottom: 20px;
}

.messages {
max-width: 1100px;

margin: 15px auto;

padding: 0 15px;
}

.message {
background: #e9f8ee;
color: #17652c;

padding: 13px;

border-radius: 10px;
}

.empty {
text-align: center;

background: white;

border-radius: 15px;

padding: 50px;

grid-column: 1 / -1;
}

.detail {
display: grid;

grid-template-columns:
1fr 1fr;

gap: 45px;
}

.detail-image {
width: 100%;
max-height: 550px;

object-fit: contain;

background: #f1e8ff;

border-radius: 18px;
}

.detail-placeholder {
width: 100%;
height: 450px;

display: flex;
justify-content: center;
align-items: center;

background: #f1e8ff;

border-radius: 18px;

font-size: 100px;
}

.detail h1 {
font-size: 38px;
}

.detail-price {
color: var(--purple);

font-size: 34px;
font-weight: 900;
}

.seller {
margin-top: 25px;

padding: 20px;

background: white;

border:
1px solid #ddd;

border-radius: 15px;
}

.profile {
max-width: 950px;
margin: auto;
}

.profile-box {
background: white;

padding: 25px;

border-radius: 15px;

border:
1px solid #ddd;

margin-bottom: 25px;
}

.my-product {
display: flex;

justify-content: space-between;
align-items: center;

gap: 15px;

background: white;

padding: 15px;

margin-bottom: 10px;

border:
1px solid #ddd;

border-radius: 12px;
}

.delete {
border: none;

background: var(--red);
color: white;

padding: 9px 12px;

border-radius: 8px;

cursor: pointer;
}

.admin-card {
background: white;

padding: 20px;

margin-bottom: 15px;

border-radius: 15px;

border:
1px solid #ddd;
}

.pending {
border-left:
5px solid var(--orange);
}

.approved {
border-left:
5px solid var(--green);
}

.status {
display: inline-block;

padding: 6px 10px;

border-radius: 20px;

font-size: 12px;

font-weight: bold;

background: #fff1dc;
color: #9a5700;
}

.status-ok {
background: #e0f5e6;
color: #17652c;
}

.admin-grid {
display: grid;

grid-template-columns:
repeat(3, 1fr);

gap: 15px;

margin-bottom: 25px;
}

.stat {
background: white;

border-radius: 15px;

padding: 20px;

text-align: center;

border:
1px solid #ddd;
}

.stat-number {
font-size: 32px;

color: var(--purple);

font-weight: bold;
}

.admin-actions {
display: flex;

flex-wrap: wrap;

gap: 8px;

margin-top: 15px;
}

footer {
background: #24113b;

color: white;

text-align: center;

padding: 35px 20px;
}

footer p {
color: #ddd;
}

@media (max-width: 950px) {

.products {
grid-template-columns:
repeat(2, 1fr);
}

.detail {
grid-template-columns: 1fr;
}

.admin-grid {
grid-template-columns: 1fr;
}
}

@media (max-width: 650px) {

.navbar {
flex-wrap: wrap;
}

.school {
display: none;
}

nav {
width: 100%;
justify-content: center;
}

.hero h1 {
font-size: 32px;
}

.search {
flex-direction: column;
}

.search button {
padding: 13px;
}

.products {
grid-template-columns: 1fr;
}

.section-header {
flex-direction: column;

align-items: flex-start;

gap: 12px;
}

.detail h1 {
font-size: 30px;
}

.my-product {
flex-direction: column;

align-items: flex-start;
}

.tabs {
flex-direction: column;
}

.admin-actions {
flex-direction: column;
}

.admin-actions .btn {
width: 100%;
text-align: center;
}
}

"""


# ============================================================
# HTML BASE
# ============================================================

BASE_HTML = """

<!DOCTYPE html>

<html lang="pt-BR">

<head>

<meta charset="UTF-8">

<meta
name="viewport"
content="width=device-width, initial-scale=1.0"
>

<meta
name="description"
content="MarketClass - Marketplace escolar"
>

<title>{{ titulo }}</title>

<style>

{{ css }}

</style>

</head>

<body>

<header>

<div class="navbar">

<a
href="{{ url_for('index') }}"
class="logo"
>
Market<span>Class</span>
</a>

<div class="school">
EEEP Jeová Costa Lima
</div>

<nav>

<a href="{{ url_for('index') }}">
🏠 Início
</a>

{% if session.get("admin") %}

<a href="{{ url_for('admin') }}">
⚙️ Administração
</a>

<a href="{{ url_for('logout') }}">
Sair
</a>

{% elif session.get("usuario_id") %}

{% if session.get("tipo") == "vendedor" %}

<a href="{{ url_for('vender') }}">
🛍️ Vender
</a>

{% endif %}

<a href="{{ url_for('perfil') }}">
👤 Minha conta
</a>

<a href="{{ url_for('logout') }}">
Sair
</a>

{% else %}

<a href="{{ url_for('login') }}">
Entrar
</a>

<a
href="{{ url_for('cadastro') }}"
class="btn"
>
Criar conta
</a>

{% endif %}

</nav>

</div>

</header>


{% with messages = get_flashed_messages() %}

{% if messages %}

<div class="messages">

{% for message in messages %}

<div class="message">
{{ message }}
</div>

{% endfor %}

</div>

{% endif %}

{% endwith %}


{{ conteudo | safe }}


<footer>

<h3>
MarketClass
</h3>

<p>
Marketplace da EEEP Jeová Costa Lima
</p>

<p>
Fardamentos, livros e materiais escolares.
</p>

<p>
© 2026 MarketClass
</p>

</footer>

</body>

</html>

"""


# ============================================================
# VARIÁVEL CSS PARA O TEMPLATE
# ============================================================

@app.context_processor
def inject_css():

return {
"css": CSS
}


# ============================================================
# INÍCIO
# ============================================================

@app.route("/")
def index():

busca = request.args.get(
"busca",
""
).strip()

categoria = request.args.get(
"categoria",
""
).strip()

db = get_db()

query = """

SELECT
produtos.*,
usuarios.nome AS vendedor

FROM produtos

JOIN usuarios
ON produtos.usuario_id = usuarios.id

WHERE usuarios.aprovado = 1

"""

params = []

if busca:

query += """

AND (
produtos.nome LIKE ?
OR produtos.descricao LIKE ?
)

"""

params.extend([
"%" + busca + "%",
"%" + busca + "%"
])

if categoria:

query += """
AND produtos.categoria = ?
"""

params.append(categoria)

query += """
ORDER BY produtos.id DESC
"""

produtos = db.execute(
query,
params
).fetchall()

db.close()

cards = []

for produto in produtos:

if produto["imagem"]:

imagem = f"""
<img
src="{url_for(
'uploaded_file',
filename=produto['imagem']
)}"
class="product-image"
alt="Foto do produto"
>
"""

else:

imagem = """
<div class="product-placeholder">
📦
</div>
"""

preco = (
f"{produto['preco']:.2f}"
.replace(".", ",")
)

tamanho = ""

if produto["tamanho"]:

tamanho = (
" • Tamanho "
+ produto["tamanho"]
)

cards.append(f"""

<article class="product">

{imagem}

<div class="product-content">

<span class="category">
{produto['categoria']}
</span>

<h3>
{produto['nome']}
</h3>

<div class="price">
R$ {preco}
</div>

<p class="info">
{produto['conservacao']}
{tamanho}
</p>

<a
href="{url_for(
'produto',
produto_id=produto['id']
)}"
class="btn"
>
Ver detalhes
</a>

</div>

</article>

""")

cards_html = "".join(cards)

if not cards_html:

cards_html = """

<div class="empty">

<h3>
Nenhum produto encontrado.
</h3>

<p>
Ainda não existem anúncios publicados
com esses critérios.
</p>

<a
href="/cadastro"
class="btn btn-orange"
>
Criar conta
</a>

</div>

"""

conteudo = f"""

<section class="hero">

<div class="hero-content">

<h1>
Compre e venda
na sua escola.
</h1>

<p>
Encontre fardamentos, livros,
materiais escolares e outros
produtos da comunidade escolar.
</p>

<form
class="search"
method="GET"
action="/"
>

<input
type="text"
name="busca"
placeholder="O que você procura?"
value="{busca}"
>

<select name="categoria">

<option value="">
Todas as categorias
</option>

<option
value="Fardamento"
{"selected" if categoria == "Fardamento" else ""}
>
Fardamento
</option>

<option
value="Livro"
{"selected" if categoria == "Livro" else ""}
>
Livro
</option>

<option
value="Material escolar"
{"selected" if categoria == "Material escolar" else ""}
>
Material escolar
</option>

<option
value="Mochila"
{"selected" if categoria == "Mochila" else ""}
>
Mochila
</option>

<option
value="Calçado"
{"selected" if categoria == "Calçado" else ""}
>
Calçado
</option>

<option
value="Outros"
{"selected" if categoria == "Outros" else ""}
>
Outros
</option>

</select>

<button type="submit">
Pesquisar
</button>

</form>

</div>

</section>

<main>

<div class="section-header">

<div>

<h2>
Produtos disponíveis
</h2>

<p class="info">
Anúncios publicados por vendedores aprovados.
</p>

</div>

<a
href="/cadastro?tipo=vendedor"
class="btn btn-orange"
>
+ Quero vender
</a>

</div>

<div class="products">

{cards_html}

</div>

</main>

"""

return render_page(
conteudo,
"MarketClass — Marketplace escolar"
)


# ============================================================
# CADASTRO
# ============================================================

@app.route(
"/cadastro",
methods=["GET", "POST"]
)
def cadastro():

if request.method == "POST":

nome = request.form.get(
"nome",
""
).strip()

email = request.form.get(
"email",
""
).strip().lower()

contato = request.form.get(
"contato",
""
).strip()

senha = request.form.get(
"senha",
""
)

tipo = request.form.get(
"tipo",
"comprador"
)

if tipo not in [
"comprador",
"vendedor"
]:

tipo = "comprador"

if not nome or not email or not contato or not senha:

flash(
"Preencha todos os campos."
)

return redirect(
url_for(
"cadastro",
tipo=tipo
)
)

if len(senha) < 6:

flash(
"A senha precisa ter pelo menos 6 caracteres."
)

return redirect(
url_for(
"cadastro",
tipo=tipo
)
)

if email == ADMIN_EMAIL:

flash(
"Este e-mail é reservado para o administrador."
)

return redirect(
url_for(
"cadastro",
tipo=tipo
)
)

aprovado = 1 if tipo == "comprador" else 0

db = get_db()

try:

db.execute("""
INSERT INTO usuarios
(
nome,
email,
senha,
contato,
tipo,
aprovado
)
VALUES (?, ?, ?, ?, ?, ?)
""", (
nome,
email,
generate_password_hash(senha),
contato,
tipo,
aprovado
))

db.commit()

except sqlite3.IntegrityError:

db.close()

flash(
"Este e-mail já está cadastrado."
)

return redirect(
url_for(
"cadastro",
tipo=tipo
)
)

usuario = db.execute("""
SELECT *
FROM usuarios
WHERE email = ?
""", (email,)).fetchone()

db.close()

session.clear()

session["usuario_id"] = usuario["id"]
session["usuario_nome"] = usuario["nome"]
session["tipo"] = usuario["tipo"]

if tipo == "vendedor":

flash(
"Cadastro de vendedor realizado! "
"Agora envie a solicitação pelo WhatsApp "
"e aguarde a aprovação."
)

else:

flash(
"Conta de comprador criada com sucesso!"
)

return redirect(
url_for("perfil")
)

tipo_inicial = request.args.get(
"tipo",
"comprador"
)

if tipo_inicial not in [
"comprador",
"vendedor"
]:

tipo_inicial = "comprador"

conteudo = f"""

<main>

<div class="form-card">

<h1>
Criar conta
</h1>

<p>
Escolha o tipo de conta.
</p>

<div class="tabs">

<a
href="/cadastro?tipo=comprador"
class="{
'active'
if tipo_inicial == 'comprador'
else ''
}"
>
👤 Comprador
</a>

<a
href="/cadastro?tipo=vendedor"
class="{
'active'
if tipo_inicial == 'vendedor'
else ''
}"
>
🏪 Vendedor
</a>

</div>

<div class="warning">

{
"Como vendedor, seu cadastro precisará "
"ser aprovado pelo administrador antes "
"de publicar anúncios. Depois do cadastro, "
"você poderá enviar uma solicitação pelo WhatsApp."
if tipo_inicial == "vendedor"
else
"Como comprador, você poderá visualizar "
"os produtos e entrar em contato com os vendedores."
}

</div>

<form
method="POST"
class="form"
>

<input
type="hidden"
name="tipo"
value="{tipo_inicial}"
>

<label>

Nome completo

<input
type="text"
name="nome"
placeholder="Seu nome"
required
>

</label>

<label>

E-mail

<input
type="email"
name="email"
placeholder="seu@email.com"
required
>

</label>

<label>

WhatsApp / contato

<input
type="text"
name="contato"
placeholder="(84) 99999-9999"
required
>

</label>

<label>

Senha

<input
type="password"
name="senha"
minlength="6"
required
>

</label>

<button
type="submit"
class="btn btn-orange"
>
Criar conta
</button>

</form>

<p>

Já possui uma conta?

<a
href="/login"
style="color: var(--purple); font-weight: bold;"
>
Entrar
</a>

</p>

</div>

</main>

"""

return render_page(
conteudo,
"Criar conta — MarketClass"
)


# ============================================================
# LOGIN
# ============================================================

@app.route(
"/login",
methods=["GET", "POST"]
)
def login():

if request.method == "POST":

email = request.form.get(
"email",
""
).strip().lower()

senha = request.form.get(
"senha",
""
)

# ----------------------------------------------------
# ADMIN
# ----------------------------------------------------

if (
email == ADMIN_EMAIL
and senha == ADMIN_PASSWORD
):

session.clear()

session["admin"] = True
session["usuario_nome"] = "Administrador"

flash(
"Login de administrador realizado."
)

return redirect(
url_for("admin")
)

# ----------------------------------------------------
# USUÁRIO
# ----------------------------------------------------

db = get_db()

usuario = db.execute("""
SELECT *
FROM usuarios
WHERE email = ?
""", (email,)).fetchone()

db.close()

if usuario and check_password_hash(
usuario["senha"],
senha
):

session.clear()

session["usuario_id"] = usuario["id"]
session["usuario_nome"] = usuario["nome"]
session["tipo"] = usuario["tipo"]

if (
usuario["tipo"] == "vendedor"
and usuario["aprovado"] == 0
):

flash(
"Sua conta de vendedor está aguardando aprovação."
)

else:

flash(
"Login realizado com sucesso!"
)

return redirect(
url_for("perfil")
)

flash(
"E-mail ou senha incorretos."
)

conteudo = """

<main>

<div class="form-card">

<h1>
Entrar
</h1>

<p>
Acesse sua conta do MarketClass.
</p>

<form
method="POST"
class="form"
>

<label>

E-mail

<input
type="email"
name="email"
required
>

</label>

<label>

Senha

<input
type="password"
name="senha"
required
>

</label>

<button
type="submit"
class="btn"
>
Entrar
</button>

</form>

<p>

Ainda não possui conta?

<a
href="/cadastro"
style="color: var(--purple); font-weight: bold;"
>
Criar conta
</a>

</p>

</div>

</main>

"""

return render_page(
conteudo,
"Entrar — MarketClass"
)


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

session.clear()

flash(
"Você saiu da sua conta."
)

return redirect(
url_for("index")
)


# ============================================================
# PERFIL
# ============================================================

@app.route("/perfil")
def perfil():

if not exigir_login():

return redirect(
url_for("login")
)

if eh_admin():

return redirect(
url_for("admin")
)

db = get_db()

usuario = db.execute("""
SELECT *
FROM usuarios
WHERE id = ?
""", (
session["usuario_id"],
)).fetchone()

if not usuario:

db.close()

session.clear()

return redirect(
url_for("login")
)

produtos = db.execute("""
SELECT *
FROM produtos
WHERE usuario_id = ?
ORDER BY id DESC
""", (
session["usuario_id"],
)).fetchall()

db.close()

if usuario["tipo"] == "vendedor":

if usuario["aprovado"]:

status = """
<span class="status status-ok">
✅ Vendedor aprovado
</span>
"""

botao_vender = """
<a
href="/vender"
class="btn btn-orange"
>
+ Novo anúncio
</a>
"""

else:

mensagem = (
"Olá! Fiz meu cadastro como vendedor "
"no MarketClass e gostaria de solicitar "
"a aprovação para poder publicar anúncios."
)

whatsapp_link = (
"https://wa.me/"
+ ADMIN_WHATSAPP
+ "?text="
+ mensagem.replace(" ", "%20")
)

status = """
<span class="status">
⏳ Aguardando aprovação
</span>
"""

botao_vender = f"""
<a
href="{whatsapp_link}"
target="_blank"
class="btn btn-orange"
>
📱 Solicitar aprovação pelo WhatsApp
</a>
"""

else:

status = """
<span class="status status-ok">
👤 Conta de comprador
</span>
...
