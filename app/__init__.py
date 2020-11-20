from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.config import Config

app = Flask(__name__)

app.jinja_env.filters['zip'] = zip

app.config.from_object(Config)

db = SQLAlchemy(app)

from app import views
