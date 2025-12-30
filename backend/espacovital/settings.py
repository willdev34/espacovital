# ===============================================================
# Título: Settings - Espaço Vital
# Descrição: Configurações do projeto Django com encoding UTF-8
# Autor: Will
# Data: 07/09/2025
# ===============================================================

# ⚠️ CRÍTICO: CONFIGURAÇÃO UTF-8 DEVE VIR PRIMEIRO
# Resolve problemas de encoding no Windows com PostgreSQL
# ===============================================================

import sys
import os

# FORÇA UTF-8 NO WINDOWS (ANTES DE QUALQUER OUTRA COISA!)
if sys.platform == 'win32':
    # Define variáveis de ambiente ANTES de qualquer import
    os.environ['PYTHONUTF8'] = '1'
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['LANG'] = 'C.UTF-8'
    os.environ['LC_ALL'] = 'C.UTF-8'

# Força encoding UTF-8 em streams de saída
import io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ===============================================================
# IMPORTS PRINCIPAIS
# ===============================================================

from pathlib import Path
from decouple import config, Csv
import locale

# Tenta configurar locale para UTF-8
# (silenciosamente ignora se não disponível)
for locale_name in ['pt_BR.UTF-8', 'C.UTF-8', '']:
    try:
        locale.setlocale(locale.LC_ALL, locale_name)
        break
    except locale.Error:
        continue

# ===============================================================
# CAMINHOS DO PROJETO
# ===============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# ===============================================================
# CONFIGURAÇÕES DE AMBIENTE
# ===============================================================

ENVIRONMENT = config('ENVIRONMENT', default='development')

# ===============================================================
# SEGURANÇA
# ===============================================================

SECRET_KEY = config('SECRET_KEY', default='dev-secret-key-change-in-production-INSECURE')
DEBUG = config('DEBUG', default=True, cast=bool)

# ALLOWED_HOSTS
ALLOWED_HOSTS_STR = config('ALLOWED_HOSTS', default='localhost,127.0.0.1')
ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_STR.split(',')]

# Adiciona domínio do Railway automaticamente
RAILWAY_STATIC_URL = config('RAILWAY_STATIC_URL', default='')
if RAILWAY_STATIC_URL:
    railway_domain = RAILWAY_STATIC_URL.replace('https://', '').replace('http://', '')
    if railway_domain not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(railway_domain)

# CSRF
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='http://localhost:8000',
    cast=Csv()
)

# ===============================================================
# APLICAÇÕES INSTALADAS
# ===============================================================

INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    
    # Third-party apps
    'cloudinary_storage',
    'cloudinary',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'django_filters',
    'ckeditor',
    'crispy_forms',
    'crispy_tailwind',
    
    # Local apps
    'core',
    'terapeutas',
    'espacos',
    'terapias',
    'blog',
    'agendamentos',
]

# ===============================================================
# MIDDLEWARE
# ===============================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'espacovital.urls'

# ===============================================================
# TEMPLATES
# ===============================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.global_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'espacovital.wsgi.application'

# ===============================================================
# BANCO DE DADOS - PostgreSQL
# ===============================================================

import dj_database_url

DATABASE_URL = config('DATABASE_URL', default=None)

if DATABASE_URL:
    # Produção/QA (Railway) - usa DATABASE_URL completa
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
    # FORÇA UTF-8 no PostgreSQL
    DATABASES['default']['OPTIONS'] = {
        'client_encoding': 'UTF8',
        'connect_timeout': 10,
    }
else:
    # Desenvolvimento local - variáveis individuais
    # FORÇA UTF-8 em TODAS as strings antes de conectar
    import urllib.parse
    
    db_name = config('DB_NAME', default='espacovital')
    db_user = config('DB_USER', default='postgres')
    db_password = config('DB_PASSWORD', default='postgres')
    db_host = config('DB_HOST', default='localhost')
    db_port = config('DB_PORT', default='5432')
    
    # Garante que todas as strings estão em UTF-8
    if isinstance(db_name, bytes):
        db_name = db_name.decode('utf-8')
    if isinstance(db_user, bytes):
        db_user = db_user.decode('utf-8')
    if isinstance(db_password, bytes):
        db_password = db_password.decode('utf-8')
    if isinstance(db_host, bytes):
        db_host = db_host.decode('utf-8')
    
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': db_name,
            'USER': db_user,
            'PASSWORD': db_password,
            'HOST': db_host,
            'PORT': db_port,
            'OPTIONS': {
                'client_encoding': 'UTF8',
                'connect_timeout': 10,
            },
            'CONN_MAX_AGE': 0,
            'ATOMIC_REQUESTS': False,
            'AUTOCOMMIT': True,
        }
    }

# ===============================================================
# VALIDAÇÃO DE SENHAS
# ===============================================================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ===============================================================
# INTERNACIONALIZAÇÃO
# ===============================================================

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# ===============================================================
# ARQUIVOS ESTÁTICOS (Static Files)
# ===============================================================

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Configurações WhiteNoise
WHITENOISE_USE_FINDERS = True
WHITENOISE_MANIFEST_STRICT = False
WHITENOISE_ALLOW_ALL_ORIGINS = True

# ===============================================================
# ARQUIVOS DE MÍDIA (Media Files)
# ===============================================================

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Verifica se deve usar Cloudinary
USE_CLOUDINARY = os.environ.get('USE_CLOUDINARY', 'false').lower() in ['true', '1', 'yes']

if USE_CLOUDINARY:
    # Cloudinary para produção
    import cloudinary
    import cloudinary.uploader
    import cloudinary.api
    
    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
        'API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
        'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET'),
    }
    
    cloudinary.config(
        cloud_name=CLOUDINARY_STORAGE['CLOUD_NAME'],
        api_key=CLOUDINARY_STORAGE['API_KEY'],
        api_secret=CLOUDINARY_STORAGE['API_SECRET'],
        secure=True
    )
    
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    MEDIA_URL = '/media/'
    
    if DEBUG:
        print("✓ Cloudinary configurado para mídia")
else:
    # Armazenamento local para desenvolvimento
    MEDIA_URL = '/media/'
    
    if DEBUG:
        print("✓ Armazenamento local configurado para mídia")

# Preparado para S3 (futuro)
USE_S3 = config('USE_S3', default=False, cast=bool)
if USE_S3:
    AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='us-east-1')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'

# ===============================================================
# CRISPY FORMS (Tailwind)
# ===============================================================

CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"

# ===============================================================
# DJANGO ALLAUTH (Autenticação)
# ===============================================================

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1

# Configurações de conta
# Django Allauth
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'  
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'  # Permite login com email OU username
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_SIGNUP_EMAIL_ENTER_TWICE = False
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = False
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'  # Tornar verificação obrigatória

# Redirecionamentos
LOGIN_REDIRECT_URL = '/'  # Fallback (caso o adapter não funcione)
LOGOUT_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = '/accounts/login/'

# Adapter customizado do Allauth (redireciona baseado no tipo de usuário)
ACCOUNT_ADAPTER = 'core.adapters.CustomAccountAdapter'

# Formulário customizado de signup
ACCOUNT_FORMS = {
    'signup': 'core.forms.CustomSignupForm',
}

# ===============================================================
# CKEDITOR (Editor de Texto Rico)
# ===============================================================

CKEDITOR_UPLOAD_PATH = "uploads/"

CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'Custom',
        'toolbar_Custom': [
            ['Bold', 'Italic', 'Underline'],
            ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent'],
            ['Link', 'Unlink'],
            ['RemoveFormat', 'Source']
        ],
        'height': 300,
        'width': '100%',
    },
    'terapeuta_bio': {
        'toolbar': 'Custom',
        'toolbar_Custom': [
            ['Bold', 'Italic', 'Underline', 'Strike'],
            ['TextColor', 'BGColor'],
            ['NumberedList', 'BulletedList'],
            ['Link', 'Unlink'],
            ['Format'],
            ['RemoveFormat'],
            ['Smiley'],
            ['Source'],
        ],
        'format_tags': 'p;h1;h2;h3;h4',
        'height': 400,
        'width': '100%',
        'removePlugins': 'elementspath',
        'resize_enabled': False,
    },
}

# ===============================================================
# EMAIL (Console para desenvolvimento)
# ===============================================================

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@espacovital.com.br'

# ===============================================================
# CAMPO PADRÃO PARA CHAVES PRIMÁRIAS
# ===============================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ===============================================================
# CONFIGURAÇÕES POR AMBIENTE
# ===============================================================

if ENVIRONMENT == 'development':
    print("🔧 Rodando em modo DESENVOLVIMENTO")
    
    # Django Debug Toolbar (opcional)
    if config('ENABLE_DEBUG_TOOLBAR', default=False, cast=bool):
        INSTALLED_APPS += ['debug_toolbar']
        MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
        INTERNAL_IPS = ['127.0.0.1']

elif ENVIRONMENT == 'qa':
    print("🚀 Rodando em modo QA (Railway)")
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

elif ENVIRONMENT == 'production':
    print("🔒 Rodando em modo PRODUÇÃO")
    DEBUG = False
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

# ===============================================================
# FIM DAS CONFIGURAÇÕES
# ===============================================================