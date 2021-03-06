import os


class Config(object):
    DEBUG = False
    TESTING = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class Production(Config):
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if os.environ.get("DATABASE_URL"):
        SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL").replace(
            "postgres", "postgresql")
    UPLOAD_FOLDER = 'static/profile_images'


class Development(Config):
    ENV = "development"
    SECRET_KEY = "secretkeygoeshere"
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database.db'
    UPLOAD_FOLDER = 'static/profile_images'
    SEND_FILE_MAX_AGE_DEFAULT = 0
    DEBUG = True
    TESTING = True
