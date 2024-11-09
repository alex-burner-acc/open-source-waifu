class Config:
    SECRET_KEY = 'your_secret_key_here'
    DEBUG = True
    LOG_LEVEL = 'INFO'
    # Database configuration
    SQLALCHEMY_DATABASE_URI = 'sqlite:///yourdatabase.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Additional configuration variables can go here
class DevelopmentConfig(Config):
    DEBUG = True
    # Development-specific configurations

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test_database.db'
    # Testing-specific configurations

class ProductionConfig(Config):
    DEBUG = False
    # Production-specific configurations
