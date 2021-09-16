import os


class Config(object):
    DEBUG = False
    TESTING = False


class ProductionConfig(Config):
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    UPLOAD_FOLDER = 'static/profile_images'


class DevelopmentConfig(Config):
    ENV = "development"
    SECRET_KEY = "secretkeygoeshere"
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database.db'
    UPLOAD_FOLDER = 'static/profile_images'
    SEND_FILE_MAX_AGE_DEFAULT = 0
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True
    TESTING = True


