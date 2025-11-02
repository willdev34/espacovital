<!--
===============================================================
Título: README - Espaço Vital
Descrição: Documentação completa do projeto para GitHub
Autor: Will
Data: 01/11/2025
===============================================================
-->

<div align="center">
  <img src="backend\static\images\logo\logotipo_minimalista.png" alt="Espaço Vital Logo" width="200"/>
  
  [![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
  [![Python](https://img.shields.io/badge/Python-3.12.1-blue.svg)](https://www.python.org/)
  [![Django](https://img.shields.io/badge/Django-4.2-green.svg)](https://www.djangoproject.com/)
  [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)
  [![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4.10-blue.svg)](https://tailwindcss.com/)
  [![HTMX](https://img.shields.io/badge/HTMX-1.9.12-orange.svg)](https://htmx.org/)
  
  [✨ Demo](https://espacovital.com) • [📖 Documentação](docs/) • [🐛 Reportar Bug](issues) • [💡 Solicitar Feature](issues)
</div>

---

## 📋 Índice

- [Sobre o Projeto](#-sobre-o-projeto)
- [Funcionalidades](#-funcionalidades)
- [Tecnologias](#-tecnologias)
- [Arquitetura](#-arquitetura)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação](#-instalação)
- [Configuração](#-configuração)
- [Uso](#-uso)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Contribuindo](#-contribuindo)
- [Roadmap](#-roadmap)
- [Licença](#-licença)
- [Contato](#-contato)

---

## 🌟 Sobre o Projeto

**Espaço Vital** é uma plataforma web inovadora que conecta usuários a **terapeutas holísticos** e **espaços terapêuticos verificados**. A plataforma facilita a descoberta e agendamento de terapias complementares, promovendo bem-estar físico, mental e espiritual.

### 🎯 Objetivo Principal

Facilitar o acesso a práticas terapêuticas alternativas através de uma plataforma segura, ética e acolhedora, onde profissionais verificados e espaços certificados oferecem seus serviços.

### 👥 Público-Alvo

- **Usuários Finais**: Pessoas buscando terapias holísticas, bem-estar e autoconhecimento
- **Terapeutas**: Profissionais de terapias complementares (Reiki, Massoterapia, Aromaterapia, etc.)
- **Donos de Espaços**: Proprietários de clínicas, studios e centros terapêuticos
- **Administradores**: Equipe de moderação e gestão da plataforma

---

## ✨ Funcionalidades

### 🔍 Busca Avançada
- **Buscar Terapeutas**: Filtros por tipo de sessão (presencial/online/domicílio), perfil profissional, especialidades, localização e acessibilidade
- **Buscar Espaços**: Filtros por tipo de espaço, disponibilidade, localização, terapias oferecidas e comodidades
- **Buscar Terapias**: Lista alfabética e busca por categorias de terapias

### 👤 Perfis Detalhados
- **Perfil de Terapeuta**: Biografia, formações, especialidades, avaliações, agenda e fotos
- **Perfil de Espaço**: Descrição, localização, comodidades, terapias disponíveis, fotos e horários
- **Verificação**: Todos os profissionais e espaços são verificados pela plataforma

### 📝 Blog Educativo
- Artigos sobre terapias, bem-estar e saúde holística
- Conteúdo produzido por profissionais verificados
- Sistema de categorias e tags

### 🎨 Design Responsivo
- Interface clean e moderna
- Totalmente responsivo (mobile-first)
- Acessibilidade WCAG 2.1
- Paleta de cores suaves e terapêuticas

### 🔐 Autenticação Completa
- Login/Cadastro com django-allauth
- Login social (Google, Facebook)
- Recuperação de senha
- Perfis diferenciados por tipo de usuário

### 📊 Áreas Administrativas
- Dashboard para terapeutas (agenda, perfil, estatísticas)
- Dashboard para donos de espaços (gestão de terapeutas, comodidades)
- Painel administrativo (moderação, assinaturas, análises)

---

## 🛠 Tecnologias

### Backend
- **Python** 3.12.1
- **Django** 4.2 (LTS) - Framework web full-stack
- **PostgreSQL** 16 + **PostGIS** - Banco de dados com suporte geoespacial
- **Django Allauth** - Sistema completo de autenticação
- **Django Filter** - Filtros avançados para buscas
- **Django CKEditor** - Editor WYSIWYG para blog
- **Pillow** - Processamento de imagens

### Frontend
- **HTML5** / **CSS3** / **JavaScript (ES6+)**
- **Django Templates** - Motor de templates
- **Tailwind CSS** 3.4.10 - Framework CSS utility-first
- **HTMX** 1.9.12 - Interatividade assíncrona sem JavaScript complexo
- **Alpine.js** (opcional) - Framework JavaScript leve

### Ferramentas de Desenvolvimento
- **Git** - Controle de versão
- **VS Code** - IDE recomendada
- **PostgreSQL** - Banco de dados local
- **Virtualenv** - Ambientes virtuais Python
- **npm** - Gerenciador de pacotes para Tailwind

### Deploy e Infraestrutura
- **Railway** / **Heroku** / **DigitalOcean** - Hospedagem
- **Gunicorn** - Servidor WSGI
- **Nginx** - Servidor web reverso
- **AWS S3** / **Cloudinary** - Armazenamento de mídia
- **GitHub Actions** - CI/CD

---

## 🏗 Arquitetura

O Espaço Vital utiliza uma **arquitetura monolítica full-stack** com Django:

```
┌─────────────────────────────────────────┐
│          FRONTEND (Django Templates)     │
│  HTML + Tailwind CSS + HTMX + Alpine.js │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│          BACKEND (Django 4.2)            │
│  ├─ Apps: core, terapeutas, espacos,    │
│  │         terapias, blog, usuarios      │
│  ├─ Django ORM (Models)                  │
│  ├─ Django Views (CBV/FBV)               │
│  ├─ Django Forms & Filters               │
│  └─ Django Admin                         │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│      DATABASE (PostgreSQL 16 + PostGIS)  │
│  ├─ Tabelas principais                   │
│  ├─ Queries geoespaciais                 │
│  └─ Índices otimizados                   │
└──────────────────────────────────────────┘
```

### Fluxo de Dados
1. Usuário acessa a página
2. Django renderiza o template com Tailwind CSS
3. HTMX intercepta interações (filtros, buscas)
4. Requisições assíncronas atualizam partes da página
5. Django processa a lógica e consulta PostgreSQL
6. Resposta HTML parcial atualiza a interface

---

## 📦 Pré-requisitos

Antes de começar, certifique-se de ter instalado:

- **Python** 3.12.1 ou superior
- **PostgreSQL** 16 ou superior
- **Node.js** 18+ e **npm** (para Tailwind CSS)
- **Git** para controle de versão
- **Virtualenv** para ambientes virtuais Python

---

## 🚀 Instalação

### 1️⃣ Clone o Repositório

```bash
git clone https://github.com/seu-usuario/espacovital.git
cd espacovital
```

### 2️⃣ Crie o Ambiente Virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3️⃣ Instale as Dependências Python

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4️⃣ Instale as Dependências Node.js (Tailwind)

```bash
cd frontend
npm install
npm run build
cd ..
```

### 5️⃣ Configure o Banco de Dados PostgreSQL

```sql
-- No PostgreSQL, execute:
CREATE DATABASE espacovital;
CREATE USER espacovital_user WITH PASSWORD 'sua_senha_segura';
ALTER ROLE espacovital_user SET client_encoding TO 'utf8';
ALTER ROLE espacovital_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE espacovital_user SET timezone TO 'America/Sao_Paulo';
GRANT ALL PRIVILEGES ON DATABASE espacovital TO espacovital_user;

-- Habilite a extensão PostGIS
\c espacovital
CREATE EXTENSION postgis;
```

---

## ⚙️ Configuração

### 1️⃣ Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```bash
# Django
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_NAME=espacovital
DATABASE_USER=espacovital_user
DATABASE_PASSWORD=sua_senha_segura
DATABASE_HOST=localhost
DATABASE_PORT=5432

# Email (opcional para desenvolvimento)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-app

# Media Files (produção)
AWS_ACCESS_KEY_ID=sua-chave-aws
AWS_SECRET_ACCESS_KEY=sua-secret-aws
AWS_STORAGE_BUCKET_NAME=espacovital-media

# Outros
ENVIRONMENT=development
```

### 2️⃣ Migrações do Banco de Dados

```bash
cd backend
python manage.py makemigrations
python manage.py migrate
```

### 3️⃣ Crie um Superusuário

```bash
python manage.py createsuperuser
```

### 4️⃣ Colete Arquivos Estáticos

```bash
python manage.py collectstatic --noinput
```

### 5️⃣ Carregue Dados Iniciais (opcional)

```bash
python manage.py loaddata fixtures/terapias.json
python manage.py loaddata fixtures/estados_cidades.json
```

---

## 🎮 Uso

### Ambiente de Desenvolvimento

```bash
# Inicie o servidor Django
cd backend
python manage.py runserver

# Em outro terminal, compile o Tailwind em modo watch
cd frontend
npm run dev
```

Acesse: `http://localhost:8000`

### Admin Django

Acesse o painel administrativo: `http://localhost:8000/admin`

### Testes

```bash
# Executar todos os testes
python manage.py test

# Testes com cobertura
coverage run --source='.' manage.py test
coverage report
```

---

## 📂 Estrutura do Projeto

```
espacovital/
├── backend/                          # Backend Django
│   ├── manage.py                     # Script de gerenciamento Django
│   ├── espacovital/                  # Configurações principais
│   │   ├── settings/                 # Settings organizados por ambiente
│   │   │   ├── base.py               # Configurações base
│   │   │   ├── development.py        # Configurações desenvolvimento
│   │   │   └── production.py         # Configurações produção
│   │   ├── urls.py                   # URLs principais
│   │   ├── wsgi.py                   # Servidor WSGI
│   │   └── asgi.py                   # Servidor ASGI
│   ├── apps/                         # Aplicações Django
│   │   ├── core/                     # App principal (home, about)
│   │   │   ├── models.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   └── templates/core/
│   │   ├── terapeutas/               # App de terapeutas
│   │   │   ├── models.py             # Terapeuta, Agenda, Avaliacao
│   │   │   ├── views.py              # ListView, DetailView
│   │   │   ├── filters.py            # Filtros de busca
│   │   │   └── templates/terapeutas/
│   │   ├── espacos/                  # App de espaços terapêuticos
│   │   │   ├── models.py             # Espaco, Comodidade
│   │   │   ├── views.py
│   │   │   ├── filters.py
│   │   │   └── templates/espacos/
│   │   ├── terapias/                 # App de terapias
│   │   │   ├── models.py             # Terapia, Categoria
│   │   │   ├── views.py
│   │   │   └── templates/terapias/
│   │   ├── blog/                     # App de blog
│   │   │   ├── models.py             # Artigo, Categoria
│   │   │   ├── views.py
│   │   │   └── templates/blog/
│   │   └── usuarios/                 # App de usuários
│   │       ├── models.py             # Perfis customizados
│   │       ├── views.py
│   │       └── templates/usuarios/
│   ├── static/                       # Arquivos estáticos
│   │   ├── css/
│   │   │   └── tailwind.css          # CSS compilado do Tailwind
│   │   ├── js/
│   │   │   ├── htmx.min.js
│   │   │   └── main.js
│   │   └── images/
│   ├── media/                        # Uploads de usuários
│   ├── templates/                    # Templates base
│   │   ├── base.html                 # Template base principal
│   │   ├── components/               # Componentes reutilizáveis
│   │   │   ├── header.html
│   │   │   ├── footer.html
│   │   │   └── cards.html
│   │   └── errors/                   # Páginas de erro
│   │       ├── 404.html
│   │       └── 500.html
│   └── fixtures/                     # Dados iniciais
│       ├── terapias.json
│       └── estados_cidades.json
│
├── frontend/                         # Frontend (Tailwind + Node.js)
│   ├── package.json                  # Dependências Node.js
│   ├── tailwind.config.js            # Configuração Tailwind
│   ├── postcss.config.js             # Configuração PostCSS
│   └── src/
│       └── styles/
│           └── main.css              # Estilos Tailwind personalizados
│
├── docs/                             # Documentação
│   ├── api/                          # Documentação da API
│   ├── design/                       # Design System
│   └── deployment/                   # Guias de deploy
│
├── tests/                            # Testes
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── .env.example                      # Exemplo de variáveis de ambiente
├── .gitignore                        # Arquivos ignorados pelo Git
├── requirements.txt                  # Dependências Python
├── pytest.ini                        # Configuração pytest
├── README.md                         # Este arquivo
└── LICENSE                           # Licença do projeto
```

---

## 🤝 Contribuindo

Contribuições são muito bem-vindas! Este projeto segue o padrão de contribuição open-source.

### Como Contribuir

1. **Fork** o projeto
2. Crie uma **branch** para sua feature (`git checkout -b feature/MinhaFeature`)
3. **Commit** suas mudanças (`git commit -m 'feat: Adiciona MinhaFeature'`)
4. **Push** para a branch (`git push origin feature/MinhaFeature`)
5. Abra um **Pull Request**

### Padrões de Commit

Seguimos o [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - Nova funcionalidade
- `fix:` - Correção de bug
- `docs:` - Documentação
- `style:` - Formatação, ponto e vírgula, etc.
- `refactor:` - Refatoração de código
- `test:` - Testes
- `chore:` - Tarefas de manutenção

### Código de Conduta

Por favor, leia nosso [Código de Conduta](CODE_OF_CONDUCT.md) antes de contribuir.

---

## 🗺 Roadmap

### ✅ Fase 1 - MVP (Concluída)
- [x] Estrutura básica do projeto Django
- [x] Modelos de dados (Terapeuta, Espaço, Terapia)
- [x] Sistema de autenticação
- [x] Templates responsivos com Tailwind
- [x] Página inicial (Home)
- [x] Sistema de busca básico

### 🚧 Fase 2 - Funcionalidades Principais (Em Desenvolvimento)
- [ ] Busca avançada com filtros (HTMX)
- [ ] Perfis detalhados de terapeutas
- [ ] Perfis detalhados de espaços
- [ ] Sistema de avaliações e comentários
- [ ] Blog educativo
- [ ] Dashboard de terapeuta
- [ ] Dashboard de dono de espaço

### 📅 Fase 3 - Funcionalidades Avançadas
- [ ] Sistema de agendamento online
- [ ] Integração com calendário (Google Calendar, iCal)
- [ ] Sistema de pagamento (Stripe/PagSeguro)
- [ ] Notificações por email e WhatsApp
- [ ] App mobile (React Native)
- [ ] Sistema de mensagens interno
- [ ] Relatórios e análises

### 🔮 Fase 4 - Melhorias e Expansão
- [ ] Inteligência Artificial para recomendações
- [ ] Marketplace de produtos holísticos
- [ ] Cursos e workshops online
- [ ] Comunidade e fórum
- [ ] Programa de afiliados
- [ ] Internacionalização (i18n)

---

## 📄 Licença

Este projeto está sob a licença **MIT**. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 📞 Contato

**Will** - Desenvolvedor Full Stack

- 🌐 Website: [espacovital.com](https://espacovital.com)
- 📧 Email: contato@espacovital.com
- 💼 LinkedIn: [linkedin.com/in/will-espacovital](https://linkedin.com/in/will-espacovital)
- 📷 Instagram: [@espacovital](https://instagram.com/espacovital)

---

## 🙏 Agradecimentos

- [Django](https://www.djangoproject.com/) - Framework web Python incrível
- [Tailwind CSS](https://tailwindcss.com/) - Framework CSS utility-first
- [HTMX](https://htmx.org/) - Biblioteca para interatividade moderna
- [PostgreSQL](https://www.postgresql.org/) - Banco de dados robusto
- Comunidade open-source por todas as ferramentas fantásticas

---

<div align="center">
  <strong>Feito com 💚 e ☮️ para promover bem-estar e conexão</strong>
  
  <br/>
  
  ⭐ Se este projeto te ajudou, considere dar uma estrela!
</div>
