#!/usr/bin/env python

from redant.utils.database import sqldb as db
from marshmallow_sqlalchemy import ModelSchema
from marshmallow import fields

class Chatter(db.Model):
    __tablename__ = 'chatters'
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(120), unique = True, nullable = False)
    password = db.Column(db.String(120), nullable = False)

    def create(self):
        db.session.add(self)
        db.session.commit()
        return self

    @classmethod
    def find_by_username(cls, username):
        return cls.query.filter_by(username = username).first()

class ChatterSchema(ModelSchema):
    class Meta(ModelSchema.Meta):
        model = Chatter
        sqla_session = db.session
    id = fields.Number(dump_only=True)
    username = fields.String(required=True)
    password = fields.String(required=True)
