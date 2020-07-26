#!/usr/bin/env python

from redant.utils.database import sqldb as db
from redant.utils.string_util import generate_uuid
from marshmallow_sqlalchemy import ModelSchema
from marshmallow import fields

class ChatterEntity(db.Model):
    __tablename__ = 'chatters'
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    username = db.Column(db.String(120), unique = True, nullable = True)
    phone_number = db.Column(db.String(16), nullable = True)

    def create(self):
        db.session.add(self)
        db.session.commit()
        return self

    @classmethod
    def find_by_username(cls, username):
        return cls.query.filter_by(username = username).first()

class ChatterSchema(ModelSchema):
    class Meta(ModelSchema.Meta):
        model = ChatterEntity
        sqla_session = db.session
    id = fields.String(dump_only=True)
    username = fields.String(required=True)
    phone_number = fields.String(required=True)
