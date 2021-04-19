import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = b'\xe0\xc3\x98\xdbH\xbd\x12E\xc4u\x84c\xfb\x1f\xa1h'

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "").replace("postgres://", "postgresql://")
    SQLALCHEMY_TRACK_MODIFICATIONS = False 

    #FOR HOSTING LIVE
    #SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "").replace("postgres://", "postgresql://")

    #FOR HOSTING LOCAL
    #SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    #SQLALCHEMY_TRACK_MODIFICATIONS = True

class DevelopmentConfig(Config):    
    DEBUG = True
    SQLALCHEMY_ECHO = True
            
class ProductionConfig(Config):
    DEBUG = False

app_config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig
}