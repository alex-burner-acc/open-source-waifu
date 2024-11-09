# This file is the entry point for the application. 
# It creates the Flask app and registers the blueprints.
from flask import Flask
from flask_cors import CORS

from app.config import Config
from app.routes.chat_api import chat_api_bp


def create_app():
    application = Flask(__name__)
    application.config.from_object(Config)
    application.logger.setLevel(application.config['LOG_LEVEL'])
    
    CORS(application)
    
    application.register_blueprint(chat_api_bp, url_prefix='/chat_api')
    
    return application