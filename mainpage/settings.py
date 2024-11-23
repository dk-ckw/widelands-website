# Django default settings for widelands project.
# Overwrite these settings in local_settings.py!

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEBUG = True

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "dev.db",
        "USER": "",  # Not used with sqlite3.
        "PASSWORD": "",  # Not used with sqlite3.
        # Set to empty string for localhost. Not used with sqlite3.
        "HOST": "",
        # Set to empty string for default. Not used with sqlite3.
        "PORT": "",
    }
}

# See: https://docs.djangoproject.com/en/4.1/releases/3.2/#customizing-type-of-auto-created-primary-keys
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = "Europe/Berlin"
USE_TZ = False  # See https://docs.djangoproject.com/en/1.8/ref/settings/#std:setting-TIME_ZONE

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = "en"

SITE_ID = 1

# Where should logged in user go by default?
LOGIN_REDIRECT_URL = "/"

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
# Overwritten in local_settings.py
MEDIA_ROOT = ""

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = "/wlmedia/"

# Absolute path where static files from thirdparty apps will be collected using
# the command: ./manage.py collectstatic
STATIC_ROOT = os.path.join(BASE_DIR, "media/static_collected/")

# URL to use when referring to static files located in STATIC_ROOT.
# Must be different than MEDIA_URL!
# https://docs.djangoproject.com/en/1.8/howto/static-files/
STATIC_URL = "/static/"

# Make this unique, and don't share it with anybody.
SECRET_KEY = "#*bc7*q0-br42fc&6l^x@zzk&(=-#gr!)fn@t30n54n05jkqcu"

ROOT_URLCONF = "mainpage.urls"

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.humanize",
    "django.contrib.sitemaps",
    "django.contrib.redirects",
    "captcha",
    # Our own apps
    "wiki.templatetags.restructuredtext",
    "mainpage",
    "wlhelp",
    "wlimages",
    "wlwebchat",
    "wlprofile",
    "wlsearch",
    "wlpoll",
    "wlevents",
    "wlmaps.apps.WlMapsConfig",
    "wlscreens",
    "wlggz",
    "wlscheduling",
    "check_input.apps.CheckInput",
    "documentation",
    "privacy_policy.apps.PrivacyPolicyConfig",
    "wladdons_settings.apps.WladdonsSettingsConfig",
    "haystack",  # search engine; see option HAYSTACK_CONNECTIONS
    # Modified 3rd party apps
    "wiki.apps.WikiConfig",  # This is based on wikiapp, but has some local modifications
    "news",  # This is based on simple-blog, but has some local modifications
    "pybb.apps.PybbConfig",  # Feature enriched version of pybb
    # Thirdparty apps
    "threadedcomments",  # included as wlapp
    "notification",  # included as wlapp
    # "django_messages_wl.apps.WlDjangoMessagesConfig",
    # "tagging",
    "star_ratings",
    "django_filters",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.contrib.redirects.middleware.RedirectFallbackMiddleware",
    # Foreign middleware
    "mainpage.online_users_middleware.OnlineNowMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                # "django_messages.context_processors.inbox",
            ],
        },
    },
]

############################
# Activation configuration #
############################
DEFAULT_FROM_EMAIL = "noreply@widelands.org"
ACCOUNT_ACTIVATION_DAYS = 2  # Days an activation token keeps active

# SHA1 Needed as compatibility for old passwords
# https://docs.djangoproject.com/en/1.11/releases/1.10/#removed-weak-password-hashers-from-the-default-password-hashers-setting
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.SHA1PasswordHasher",
]

######################
# Wiki configuration #
######################
WIKI_LOCK_DURATION = 30
WIKI_URL_RE = r"[:\-\w ]+"
WIKI_WORD_RE = r"[:\-\w ]+"
# List pages below the URL '/wiki/...' here if they are dynamically created
WIKI_SPECIAL_PAGES = [
    "list",
    "search",
    "history",
    "feeds",
    "observe",
    "edit",
    "tag_list",
]
FORBIDDEN_WIKI_TITLES = [
    "trash",
]
######################
# User configuration #
######################
DEFAULT_TIME_DISPLAY = r"%ND(Y-m-d,) H:i"  # According to ISO 8601
DEFAULT_MARKUP = "markdown"
SIGNATURE_MAX_LENGTH = 255
SIGNATURE_MAX_LINES = 8
AVATARS_UPLOAD_TO = "profile/avatars"
AVATAR_HEIGHT = AVATAR_WIDTH = 80

######################
# Pybb Configuration #
######################
PYBB_DEFAULT_MARKUP = "markdown"
PYBB_ATTACHMENT_ENABLE = True

# To prevent sending errors from the webserver, keep
# this below the webserver settings
PYBB_ATTACHMENT_SIZE_LIMIT = 1024 * 1024 * 4
ALLOW_ATTACHMENTS_AFTER = 5  # Allow attachments only after this amount of posts
ATTACHMENT_DESCR_PAGE = "Attachments"  # Wikipage describing uploads
PYBB_DEFAULT_MARKUP = "markdown"
INTERNAL_PERM = "pybb.can_access_internal"  # The permission string derived from pybb.models.category
EDIT_HOURS = 24

####################
# threadedcomments #
####################
DEFAULT_MARKUP = 1  # "markdown"

##################
# django-tagging #
##################
FORCE_LOWERCASE_TAGS = True
MAX_TAG_LENGTH = 20

##################################
# Uploading files and validation #
##################################

# Use only this handler to get real a file in /tmp
# Some validation checks needs a real file
FILE_UPLOAD_HANDLERS = [
    "django.core.files.uploadhandler.TemporaryFileUploadHandler",
]

ALLOWED_EXTENSIONS = [
    "wgf",
    "jpg",
    "jpeg",
    "gif",
    "png",
    "ogg",
    "lua",
    "ods",
    "zip",
    "json",
    "txt",
    "csv",
    "wai",
    "wry",
]

# Widelands Savegame should contain at least these entries
WGF_CONTENT_CHECK = [
    "/binary/",
    "/map/",
    "/minimap.png",
    "/preload",
]

# Do not check mime type for these extensions
SKIP_MIME_EXTENSIONS = [
    "wai",
]

ALLOWED_WAI_SECTIONS = [
    "magic_numbers",
    "neuron_values",
    "neuron_functions",
    "fneurons",
]

# If clamav including clamdscan is installed and running
# set this to True
VIRUS_CHECK = False

##############################################
# Link classification and other Markup stuff #
##############################################
LOCAL_DOMAINS = ["xoops.widelands.org", "wl.widelands.org"]

SMILEY_DIR = STATIC_URL + "img/smileys/"
# Keep this list ordered by length of smileys
SMILEYS = [
    ("O:-)", "face-angel.png"),
    ("O:)", "face-angel.png"),
    (":-/", "face-confused.png"),
    (":/", "face-confused.png"),
    ("B-)", "face-cool.png"),
    ("B)", "face-cool.png"),
    (":'-(", "face-crying.png"),
    (":'(", "face-crying.png"),
    (":-))", "face-smile-big.png"),
    (":))", "face-smile-big.png"),
    (":-)", "face-smile.png"),
    (":)", "face-smile.png"),
    ("]:-)", "face-devilish.png"),
    ("8-)", "face-glasses.png"),
    ("8)", "face-glasses.png"),
    (":-D", "face-grin.png"),
    (":D", "face-grin.png"),
    (":-x", "face-kiss.png"),
    (":x", "face-kiss.png"),
    (":-*", "face-kiss.png"),
    (":*", "face-kiss.png"),
    (":-((", "face-mad.png"),
    (":((", "face-mad.png"),
    (":-||", "face-mad.png"),
    (":||", "face-mad.png"),
    (":(|)", "face-monkey.png"),
    (":-|", "face-plain.png"),
    (":|", "face-plain.png"),
    (":-(", "face-sad.png"),
    (":(", "face-sad.png"),
    (":-O", "face-shock.png"),
    (":O", "face-shock.png"),
    (":-o", "face-surprise.png"),
    (":o", "face-surprise.png"),
    (":-P", "face-tongue.png"),
    (":P", "face-tongue.png"),
    (":-S", "face-upset.png"),
    (":S", "face-upset.png"),
    (";-)", "face-wink.png"),
    (";)", "face-wink.png"),
]

#################
# Search Config #
#################
HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": "haystack.backends.whoosh_backend.WhooshEngine",
        "PATH": os.path.join(os.path.dirname(__file__), "whoosh_index"),
    },
}

###########################
# Widelands SVN directory #
###########################
# This is needed for various thinks, for example
# to access media (for minimap creation) or for online help
# or for ChangeLog displays
WIDELANDS_SVN_DIR = ""

###############
# Screenshots #
###############
THUMBNAIL_SIZE = (160, 160)

########
# Maps #
########
MAPS_PER_PAGE = 10

##############################################
## Recipient(s) who get an email if someone ##
## uses the form on legal notice page       ##
## Use allways the form ('name', 'Email')   ##
##############################################
INQUIRY_RECIPIENTS = [
    ("peter", "peter@example.com"),
]

##########################################
## Allowed tags/attributes for 'bleach' ##
## Used for sanitizing user input.      ##
##########################################
BLEACH_ALLOWED_TAGS = [
    "a",
    "abbr",
    "acronym",
    "blockquote",
    "br",
    "em",
    "i",
    "strong",
    "b",
    "ul",
    "ol",
    "li",
    "div",
    "p",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "pre",
    "code",
    "img",
    "hr",
    "table",
    "tbody",
    "thead",
    "th",
    "tr",
    "td",
    "sup",
]
# Note: DO NOT allow style here. See
# https://github.com/advisories/GHSA-vqhp-cxgc-6wmm
BLEACH_ALLOWED_ATTRIBUTES = {
    "img": ["src", "alt"],
    "a": ["href"],
    "td": ["align"],
    "*": ["class", "id", "title"],
}

###########################
# Settings for displaying #
# online users            #
###########################

# Time in seconds how long a user will be shown online
ONLINE_THRESHOLD = 60 * 15
# Number of stored users
ONLINE_MAX = 25

###########################################
# Settings for users who deleted themself #
###########################################

DELETED_MAIL_ADDRESS = ""
DELETED_USERNAME = "Ex-Member"

###################
# Cookie settings #
###################

# See: https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-age
CSRF_COOKIE_AGE = None

#############################
# star_rating configuration #
#############################

STAR_RATINGS_STAR_HEIGHT = 14
STAR_RATINGS_STAR_WIDTH = 14
STAR_RATINGS_RANGE = 10

###############
# Set a cache #
###############
# See https://docs.djangoproject.com/en/1.11/topics/cache/
# The cache is used for 'Online users' and the wiki edit lock

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "wl_cache",
    }
}

#########################
# Notification settings #
#########################
# When set to True, one has to run ./manage.py emit_notices
# for sending emails

NOTIFICATION_QUEUE_ALL = False

SHOW_GIT_DATA = False  # Show git branch and commit in the header
#!/usr/bin/python
# -*- coding: utf-8 -*-
# The above leads python2.7 to read this file as utf-8
# Needs to be directly after the python shebang

import os
import re

# Absolute path for uploaded files, e.g.:
# images for avatars, wiki, wlscreens, news cathegories and also mapfiles
MEDIA_ROOT = os.path.join(os.getcwd(), 'media/')

# If you are using the developer version of widelands from Launchpad
# set WIDELANDS_SVN_DIR to the correct path. See also:
# https://wl.widelands.org/wiki/BzrPrimer/
WIDELANDS_SVN_DIR = "/path/to/widelands/trunk/"

os.environ['PATH'] = WIDELANDS_SVN_DIR + ':' + os.environ['PATH']

DATABASES = {
   'default': {
      'ENGINE': 'django.db.backends.sqlite3',
      'NAME': 'dev.db',
      'USER': '',      # Not used with sqlite3.
      'PASSWORD': '',  # Not used with sqlite3.
      'HOST': '',      # Set to empty string for localhost. Not used with sqlite3.
      'PORT': '',      # Set to empty string for default. Not used with sqlite3.
      # Next is only used for mysql. Explanations:
      # https://docs.djangoproject.com/en/1.11/ref/databases/#connecting-to-the-database
      # 'init_command': is recommended for MySQL >= 5.6
      # 'OPTIONS': {
      #   'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
      #   'isolation_level': 'read committed',
      #},
   }
}

# If you want to test the registration, you will need these keys.
# Don't use this key in production!
RECAPTCHA_PUBLIC_KEY = "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
RECAPTCHA_PRIVATE_KEY = "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"
SILENCED_SYSTEM_CHECKS = ['captcha.recaptcha_test_key_error']

# These are used in the contact form to ensure people are human.
INQUIRY_QUESTION = [
    ('What color is better than green?', 'blue'),
    ('Type one of these two words: widelands, butter', 'widelands', 'butter'),
]

# if you change this, pls edit the question -> answer
INQUIRY_CHIEFTAINS = [
    'Benedikt Straub (Nordfriese) (Since 2022).',
    'GunChleoc (2016 – 2022)',
    'Holger Rapp (SirVer) (2001 – 2016)',
]

# The logo used for mainpage
LOGO_FILE = 'logo_alpha.png'

# Setting an email backend prevents 'connection refused' errors
# Don't use this on the widelands server!
# This Backend shows Emails in console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Anti spam keywords
# If these are found, the posts/topics in forum get hidden
ANTI_SPAM_KWRDS = ['spam']
ANTI_SPAM_PHONE_NR = re.compile('\d{8,16}')
MAX_HIDDEN_POSTS = 5

#######################
#  Optional settings  #
#######################

# Set a Database cache. You won't need this for development or testing locally.
# If you want to use this, run ./manage.py createcachetable after uncommenting.
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
#         'LOCATION': 'wl_cache',
#     }
# }

# Uncomment 'LOGGING = {...}' for debugging purposes when you have set DEBUG=False.
# Use then in the code:

# import logging
# log = logging.getLogger(__name__)
# log.info('Variable x: %s', x)

# This prints the value for Variable 'x' to log.txt

#LOGGING = {
#    'version': 1,
#    'disable_existing_loggers': False,
#    'handlers': {
#        'logfile': {
#            'level':'DEBUG',
#            'class':'logging.FileHandler',
#            'filename': os.getcwd() + "/log.txt",
#        },
#    },
#    'root': {
#        'level': 'INFO',
#        'handlers': ['logfile']
#    },
#}


try:
    import local_settings
except ImportError:
    pass
