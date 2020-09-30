#!/usr/bin/env python

from redant.utils.database import sqldb as db
from redant.utils.string_util import generate_uuid
from marshmallow_sqlalchemy import ModelSchema
from marshmallow import fields

class ChatterEntity(db.Model):
    __tablename__ = 'chatters'
    chatter_id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    chatter_code = db.Column(db.String(64), nullable = False)
    notes = db.Column(db.JSON, nullable=True)
    #
    phone_number = db.Column(db.String(16), nullable = True)
    first_name = db.Column(db.String(120), unique = False, nullable = True)
    last_name = db.Column(db.String(120), unique = False, nullable = True)
    banned = db.Column(db.Boolean(), nullable = True)
    #
    #
    def __init__(self, chatter_code, phone_number=None,
            first_name=None, last_name=None, notes=None, **kwargs):
        self.chatter_code = chatter_code
        self.phone_number = phone_number
        self.first_name = first_name
        self.last_name = last_name
        self.notes = notes
    #
    #
    def create(self):
        db.session.add(self)
        db.session.commit()
        return self
    #
    #
    @classmethod
    def find_by__chatter_code(cls, chatter_code):
        return cls.query\
            .filter_by(chatter_code = chatter_code)\
            .first()
    #
    @classmethod
    def find_by__phone_number(cls, phone_number):
        return cls.query\
            .filter_by(phone_number = phone_number)\
            .first()

class ChatterSchema(ModelSchema):
    class Meta(ModelSchema.Meta):
        model = ChatterEntity
        sqla_session = db.session
    chatter_id = fields.String(dump_only=True)
    chatter_code = fields.String(required=True)
    phone_number = fields.String(required=False)
