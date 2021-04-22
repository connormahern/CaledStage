import os
from main import create_app
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

config_name = os.getenv('FLASK_CONFIG')
app = create_app(config_name)


if __name__ == '__main__':
    app.run()
