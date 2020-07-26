#!/usr/bin/env python

from flask_sqlalchemy import SQLAlchemy
sqldb = SQLAlchemy()

def sqldb_hook(app):
    sqldb.init_app(app)
    with app.app_context():
        sqldb.create_all()
