<!--
===============================================================
Título: README - Espaço Vital
Descrição: Documentação completa do projeto para GitHub
Autor: Will
Data: 10/05/2026
===============================================================
-->

<div align="center">
  <img src="backend/static/images/logo/logotipo_minimalista.png" alt="Espaço Vital Logo" width="200"/>
  
  [![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
  [![Python](https://img.shields.io/badge/Python-3.12.1-blue.svg)](https://www.python.org/)
  [![Django](https://img.shields.io/badge/Django-4.2-green.svg)](https://www.djangoproject.com/)
  [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)
  [![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4.10-blue.svg)](https://tailwindcss.com/)
  [![HTMX](https://img.shields.io/badge/HTMX-1.9.12-orange.svg)](https://htmx.org/)
  
  [✨ Demo](https://espacovital.onrender.com) • [📖 Documentação](docs/) • [🐛 Reportar Bug](issues) • [💡 Solicitar Feature](issues)
</div>

---

## 📋 Índice

- [Sobre o Projeto](#-sobre-o-projeto)
- [Funcionalidades](#-funcionalidades)
- [Tecnologias](#-tecnologias)
- [Arquitetura](#-arquitetura)
- [Ambientes](#-ambientes)
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

**Espaço Vital** é uma plataforma web que conecta usuários a **terapeutas holísticos** e **espaços terapêuticos verificados**. A plataforma facilita a descoberta e agendamento de terapias complementares, promovendo bem-estar físico, mental e espiritual.

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

### 📅 Agendamentos
- Sistema de agendamento de salas e espaços
- Gestão de disponibilidade por sala
- Controle de multas e cancelamentos
- Geração de PIX para pagamentos diretos entre as partes

### 💼 Planos e Assinaturas
- 7 planos segmentados por perfil de usuário
- Planos para terapeutas, donos de espaços e combinados
- Controle de recursos por plano (número de salas, agendamentos, etc.)

### 📝 Blog Educativo
- Artigos sobre terapias, bem-estar e saúde holística
- Conteúdo produzido por profissionais verificados
- Sistema de categorias e tags

### 🎨 Design Responsivo
- Interface clean e moderna
- Totalmente responsivo (mobile-first)
- Paleta de cores suaves e terapêuticas (`#1E5C5C`, `#FFB4A2`, `#56C596`, `#f2eae0`)

### 🔐 Autenticação Completa
- Login/Cadastro com django-allauth
- Login social (Google, Facebook)
- Recuperação de senha
- Perfis diferenciados por tipo de usuário

### 📊 Áreas Administrativas
- Dashboard para terapeutas (agendamentos, perfil, estatísticas)
- Dashboard para donos de espaços (gestão de salas, terapeutas vinculados)
- Painel administrativo (moderação, assinaturas, análises)

---

## 🛠 Tecnologias

### Backend
- **Python** 3.12.1
- **Django** 4.2 LTS - Framework web full-stack
- **PostgreSQL** 16 - Banco de dados principal
- **Django Allauth** - Sistema completo de autenticação
- **Django Filter** - Filtros avançados para buscas
- **Django CKEditor** - Editor WYSIWYG para blog
- **Pillow** - Processamento de imagens
- **Gunicorn** - Servidor WSGI para produção
- **WhiteNoise** - Servir arquivos estáticos em produção

### Frontend
- **HTML5** / **CSS3** / **JavaScript (ES6+)**
- **Django Templates** - Motor de templates
- **Tailwind CSS** 3.4.10 - Framework CSS utility-first
- **HTMX** 1.9.12 - Interatividade assíncrona
- **Font Awesome** - Ícones

### Ferramentas de Desenvolvimento
- **Git** - Controle de versão
- **VS Code** - IDE recomendada
- **Docker** - PostgreSQL local via container
- **WSL2 (Ubuntu)** - Ambiente de desenvolvimento no Windows
- **npm** - Gerenciador de pacotes para Tailwind

### Deploy e Infraestrutura
- **Render** - Hospedagem da aplicação (ambiente de teste)
- **Supabase** - Banco de dados PostgreSQL em nuvem
- **Cloudinary** - Armazenamento de mídia
- **GitHub Actions** - CI/CD (planejado)

---

## 🏗 Arquitetura

O Espaço Vital utiliza uma **arquitetura monolítica full-stack** com Django:

```
┌─────────────────────────────────────────┐
│          FRONTEND (Django Templates)     │
│  HTML + Tailwind CSS + HTMX             │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│          BACKEND (Django 4.2)            │
│  ├─ Apps: core, terapeutas, espacos,    │
│  │         terapias, agendamentos,       │
│  │         accounts                     │
│  ├─ Django ORM (Models)                  │
│  ├─ Django Views (CBV/FBV)               │
│  ├─ Django Forms & Filters               │
│  └─ Django Admin                         │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│      DATABASE (PostgreSQL - Supabase)    │
│  ├─ Tabelas principais                   │
│  ├─ Planos e assinaturas                 │
│  └─ Agendamentos e salas                 │
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

## 🌐 Ambientes

| Ambiente | URL | Hospedagem | Status |
|---|---|---|---|
| Local (desenvolvimento) | http://localhost:8000 | WSL2 + Docker | 💻 Local |
| Teste | https://espacovital.onrender.com | Render (free tier) | 🟢 Online |
| Produção | Em breve | A definir | 🔜 Planejado |

> **Obs:** O ambiente de teste no Render pode ter um tempo de cold start de até 30 segundos após inatividade.

---

## 📦 Pré-requisitos

Antes de começar, certifique-se de ter instalado:

- **Python** 3.12.1 ou superior
- **PostgreSQL** 16 ou superior (ou Docker para rodar via container)
- **Node.js** 18+ e **npm** (para Tailwind CSS)
- **Git** para controle de versão
- **WSL2** (recomendado para Windows)

---

## 🚀 Instalação

### 1️⃣ Clone o Repositório

```bash
git clone https://github.com/willdev34/espacovital.git
cd espacovital
```

### 2️⃣ Suba o banco via Docker (recomendado)

```bash
docker run --name espacovital-db \
  -e POSTGRES_DB=espacovital \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5433:5432 \
  -d postgres:16
```

### 3️⃣ Crie o Ambiente Virtual

```bash
# Linux/WSL2
python3 -m venv venv-wsl
source venv-wsl/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 4️⃣ Instale as Dependências Python

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5️⃣ Instale as Dependências Node.js (Tailwind)

```bash
cd frontend
npm install
npm run build
cd ..
```

---

## ⚙️ Configuração

### 1️⃣ Variáveis de Ambiente

Crie um arquivo `.env` dentro de `backend/` baseado no `.env.example`:

```bash
# Ambiente
ENVIRONMENT=development

# Django
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (local via Docker)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=espacovital
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5433

# Storage
USE_S3=False
USE_CLOUDINARY=False

# Segurança
CSRF_TRUSTED_ORIGINS=http://localhost:8000

# Debug Toolbar
ENABLE_DEBUG_TOOLBAR=True
```

### 2️⃣ Migrações do Banco de Dados

```bash
cd backend
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
python manage.py popular_planos
python manage.py popular_comodidades
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
│   ├── .python-version               # Versão do Python para deploy
│   ├── espacovital/                  # Configurações principais
│   │   ├── settings.py               # Settings unificado por ambiente
│   │   ├── urls.py                   # URLs principais
│   │   ├── wsgi.py                   # Servidor WSGI
│   │   └── asgi.py                   # Servidor ASGI
│   ├── core/                         # App principal (home, modelos base)
│   ├── terapeutas/                   # App de terapeutas
│   │   ├── models.py                 # Terapeuta, Agenda, Avaliacao
│   │   ├── views.py                  # ListView, DetailView, Dashboard
│   │   └── filters.py                # Filtros de busca
│   ├── espacos/                      # App de espaços terapêuticos
│   │   ├── models.py                 # Espaco, Comodidade
│   │   ├── views.py
│   │   └── filters.py
│   ├── terapias/                     # App de terapias
│   ├── agendamentos/                 # App de agendamentos
│   │   ├── models.py                 # Sala, Agendamento, Multa, PIXConfig
│   │   ├── views.py
│   │   ├── forms.py
│   │   └── urls.py
│   ├── accounts/                     # App de contas e assinaturas
│   │   └── models.py                 # Plano, Assinatura, HistoricoAssinatura
│   ├── static/                       # Arquivos estáticos
│   ├── media/                        # Uploads locais
│   ├── templates/                    # Templates base e por app
│   │   ├── base.html
│   │   ├── components/
│   │   └── terapeutas/dashboard/
│   └── fixtures/                     # Dados iniciais
│       ├── terapias.json
│       └── estados_cidades.json
│
├── frontend/                         # Frontend (Tailwind + Node.js)
│   ├── package.json
│   ├── tailwind.config.js
│   └── src/styles/main.css
│
├── .env.example                      # Exemplo de variáveis de ambiente
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🤝 Contribuindo

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
- `style:` - Formatação
- `refactor:` - Refatoração de código
- `test:` - Testes
- `chore:` - Tarefas de manutenção

### Branches

- `main` - Branch de produção/teste (deploy automático no Render)
- `develop` - Branch de desenvolvimento ativo

---

## 🗺 Roadmap

### ✅ Fase 1 - MVP (Concluída)
- [x] Estrutura base do projeto Django
- [x] Modelos de dados (Terapeuta, Espaço, Terapia)
- [x] Sistema de autenticação com django-allauth
- [x] Templates responsivos com Tailwind CSS
- [x] Página inicial e sistema de busca básico
- [x] Deploy em ambiente de teste (Render + Supabase)

### 🚧 Fase 2 - Funcionalidades Principais (Em Desenvolvimento)
- [x] Sistema de planos e assinaturas (7 planos)
- [x] Dashboard do terapeuta
- [x] Módulo de agendamentos (models, forms)
- [ ] CRUD completo de agendamentos
- [ ] Sistema de avaliações
- [ ] Dashboard de dono de espaço
- [ ] Blog educativo

### 📅 Fase 3 - Funcionalidades Avançadas
- [ ] Integração com calendário (Google Calendar)
- [ ] Geração de QR Code PIX para pagamentos
- [ ] Notificações por email e WhatsApp
- [ ] Relatórios e análises

### 🔮 Fase 4 - Expansão
- [ ] App mobile
- [ ] Inteligência Artificial para recomendações
- [ ] Marketplace de produtos holísticos
- [ ] Internacionalização (i18n)

---

## 📄 Licença

Este projeto está sob a licença **MIT**. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 📞 Contato

**Will** - Desenvolvedor Full Stack Sênior

- 🌐 Website: Em breve
- 📧 Email: [willdevp@icloud.com](mailto:willdevp@icloud.com)
- 💼 LinkedIn: [linkedin.com/in/willdevfull](https://linkedin.com/in/willdevfull)
- 📷 Instagram: [@espacovital](https://instagram.com/espacovital)

---

## 🙏 Agradecimentos

- [Django](https://www.djangoproject.com/) - Framework web Python
- [Tailwind CSS](https://tailwindcss.com/) - Framework CSS utility-first
- [HTMX](https://htmx.org/) - Biblioteca para interatividade moderna
- [PostgreSQL](https://www.postgresql.org/) - Banco de dados
- [Supabase](https://supabase.com/) - PostgreSQL em nuvem
- [Render](https://render.com/) - Hospedagem da aplicação
- [Cloudinary](https://cloudinary.com/) - Armazenamento de mídia
- Comunidade open-source por todas as ferramentas

---

<div align="center">
  <strong>Feito com 💚 e ☮️ para promover bem-estar e conexão</strong>
  
  <br/>
  
  ⭐ Se este projeto te ajudou, considere dar uma estrela!
</div>