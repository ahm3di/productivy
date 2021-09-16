import os


class Config(object):
    DEBUG = False
    TESTING = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class ProductionConfig(Config):
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DATABASE_URL = os.environ.get("DATABASE_URL").replace("postgres",
                                                          "postgresql")
    UPLOAD_FOLDER = 'static/profile_images'


class DevelopmentConfig(Config):
    ENV = "development"
    SECRET_KEY = "secretkeygoeshere"
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database.db'
    UPLOAD_FOLDER = 'static/profile_images'
    SEND_FILE_MAX_AGE_DEFAULT = 0
    DEBUG = True
    TESTING = True
