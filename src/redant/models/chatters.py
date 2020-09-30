#!/usr/bin/env python

from redant.utils.database import sqldb as db
from redant.utils.string_util import generate_uuid
from marshmallow_sqlalchemy import ModelSchema
from marshmallow import fields

class ChatterEntity(db.Model):
    __tablename__ = 'chatters'
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    username = db.Column(db.String(120), nullable = True)
    phone_number = db.Column(db.String(16), nullable = True)
    notes = db.Column(db.JSON, nullable=True)
    #
    first_name = db.Column(db.String(120), unique = False, nullable = True)
    last_name = db.Column(db.String(120), unique = False, nullable = True)
    banned = db.Column(db.Boolean(), nullable = True)
    #
    #
    def __init__(self, phone_number=None, username=None, **kwargs):
        self.phone_number = phone_number
        self.username = username
    #
    #
    def create(self):
        db.session.add(self)
        db.session.commit()
        return self
    #
    #
    @classmethod
    def find_by_username(cls, username):
        return cls.query\
            .filter_by(username = username)\
            .first()
    #
    @classmethod
    def find_by_phone_number(cls, phone_number):
        return cls.query\
            .filter_by(phone_number = phone_number)\
            .first()

class ChatterSchema(ModelSchema):
    class Meta(ModelSchema.Meta):
        model = ChatterEntity
        sqla_session = db.session
    id = fields.String(dump_only=True)
    username = fields.String(required=False)
    phone_number = fields.String(required=False)
