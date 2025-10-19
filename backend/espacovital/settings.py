# ===============================================================
# Título: Settings - Espaço Vital (Versão Limpa)
# Descrição: Configurações básicas funcionais
# Autor: Will | Empresa: Espaço VItal
# Data: 07/09/2025
# ===============================================================

import sys
import os
from pathlib import Path
from decouple import config, Csv

# ===============================================================
# FORÇA ENCODING UTF-8 NO WINDOWS (CRÍTICO!)
# Resolve problemas com caracteres especiais no PostgreSQL
# ===============================================================

if sys.platform == 'win32':
    import locale
    
    # Força encoding UTF-8 em todos os streams de I/O
    if sys.stdout.encoding != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    # Define locale padrão para UTF-8
    try:
        locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_ALL, 'C.UTF-8')
        except locale.Error:
            pass  # Se não conseguir, continua com o padrão

# ===============================================================
# Build paths inside the project
# ===============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================================================
# CONFIGURAÇÕES DE AMBIENTE
# ==============================================================

# Identifica qual ambiente está rodando
ENVIRONMENT = config('ENVIRONMENT', default='development')

# Security
SECRET_KEY = config('SECRET_KEY', default='dev-secret-key-change-in-production')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

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
    'cloudinary_storage',  # C00loudinary para as imagens
    'cloudinary',           
    'allauth',
    
    # Third-party apps
    'cloudinary_storage',  # Cloudinary para as imagens
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
# CONFIGURAÇÕES DE TEMPLATES
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

# ==============================================================
# DATABASE - PostgreSQL com suporte Railway e Local
# ==============================================================

import dj_database_url

# Railway fornece DATABASE_URL automaticamente
# Local usa as variáveis individuais
DATABASE_URL = config('DATABASE_URL', default=None)

if DATABASE_URL:
    # Produção/QA (Railway) - usa DATABASE_URL
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    # Desenvolvimento local - usa variáveis individuais
    DATABASES = {
        'default': {
            'ENGINE': config('DB_ENGINE', default='django.db.backends.postgresql'),
            'NAME': config('DB_NAME', default='espacovital'),
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD', default='postgres'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
            'OPTIONS': {
                'client_encoding': 'UTF8',
                'connect_timeout': 10,
            },
            'CONN_MAX_AGE': 0,  # Não mantém conexões abertas
            'ATOMIC_REQUESTS': False,
            'AUTOCOMMIT': True,
        }
    }

# ===============================================================
# VALIDAÇÃO DE SENHAS
# ===============================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ===============================================================
# INTERNACIONALIZAÇÃO
# ===============================================================

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# ===============================================================
# ARQUIVOS ESTÁTICOS E MEDIA
# ===============================================================

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# WhiteNoise configuração
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Cloudinary Configuration
USE_CLOUDINARY = config('USE_CLOUDINARY', default=False, cast=bool)

if USE_CLOUDINARY:
    # Usar Cloudinary para mídia (produção)
    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': config('CLOUDINARY_CLOUD_NAME'),
        'API_KEY': config('CLOUDINARY_API_KEY'),
        'API_SECRET': config('CLOUDINARY_API_SECRET'),
    }
    
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    MEDIA_URL = '/media/'  # Cloudinary vai gerenciar automaticamente
else:
    # Armazenamento local (desenvolvimento)
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Configuração para S3 (preparado para futuro)
USE_S3 = config('USE_S3', default=False, cast=bool)

if USE_S3:
    # AWS S3 Settings (configurar quando for usar)
    AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='us-east-1')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'

# ===============================================================
# CONFIGURAÇÕES DO WHITENOISE (Para servir static files)
# ===============================================================

WHITENOISE_USE_FINDERS = True
WHITENOISE_MANIFEST_STRICT = False
WHITENOISE_ALLOW_ALL_ORIGINS = True


# ===============================================================
# CONFIGURAÇÕES DO CRISPY FORMS
# ===============================================================

CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"

# ===============================================================
# CONFIGURAÇÕES DO ALLAUTH
# ===============================================================

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1

# Configurações de conta
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_UNIQUE_EMAIL = True

# URLs de redirecionamento
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'

# ===============================================================
# CONFIGURAÇÕES DO CKEDITOR
# ===============================================================

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
}

CKEDITOR_UPLOAD_PATH = "uploads/"

# ===============================================================
# CONFIGURAÇÕES DE EMAIL (desenvolvimento)
# ===============================================================

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@espacovital.com.br'

# ===============================================================
# CAMPO DE CHAVE PRIMÁRIA PADRÃO
# ===============================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ===============================================================
# CONFIGURAÇÃO DO CKEDITOR
# ===============================================================

CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'full',
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

# ==============================================================
# CONFIGURAÇÕES ESPECÍFICAS POR AMBIENTE
# ==============================================================

if ENVIRONMENT == 'development':
    # Configurações apenas para DEV
    print(" Rodando em modo DESENVOLVIMENTO")
    
    # Django Debug Toolbar (opcional)
    if config('ENABLE_DEBUG_TOOLBAR', default=False, cast=bool):
        INSTALLED_APPS += ['debug_toolbar']
        MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
        INTERNAL_IPS = ['127.0.0.1']

elif ENVIRONMENT == 'qa':
    # Configurações para QA (Railway)
    print("Rodando em modo QA (Railway)")
    
    # Segurança adicional
    SECURE_SSL_REDIRECT = False  # Railway já faz isso
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

elif ENVIRONMENT == 'production':
    # Configurações para Produção (futuro)
    print("Rodando em modo PRODUÇÃO")
    
    # Segurança máxima
    DEBUG = False
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'