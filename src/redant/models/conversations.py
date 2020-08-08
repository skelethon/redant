#!/usr/bin/env python

from redant.utils.database import sqldb as db
from redant.utils.object_util import json_dumps
from redant.utils.string_util import generate_uuid
from marshmallow_sqlalchemy import ModelSchema
from marshmallow import fields
from sqlalchemy import desc

class ConversationModel(db.Model):
    __tablename__ = 'conversations'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    state = db.Column(db.String(32), nullable = False)

    story = db.Column(db.JSON, nullable=True)
    phone_number = db.Column(db.String(16), nullable = True)
    facebook_id = db.Column(db.String(36), nullable = True)

    # chatter_id = db.Column(db.String(36), db.ForeignKey('chatters.id'))
    # chatter = db.relationship('ChatterEntity', backref=db.backref('chatters', lazy='dynamic'))

    def create(self):
        db.session.add(self)
        db.session.commit()
        return self

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
            return self, None
        except Exception as exception:
            db.session.rollback()
            return None, exception

    def __init__(self, phone_number=None, facebook_id=None, state='begin', **kwargs):
        self.phone_number = phone_number
        self.facebook_id = facebook_id
        self.state = state

    def __repr__(self):
        return json_dumps(self, ['id', 'created_at', 'state', 'phone_number', 'facebook_id'])

    @classmethod
    def find_by_phone_number(cls, phone_number):
        return cls.query\
            .filter_by(phone_number = phone_number)\
            .order_by(desc(ConversationModel.created_at))\
            .first()

class ConversationSchema(ModelSchema):
    class Meta(ModelSchema.Meta):
        model = ConversationModel
        sqla_session = db.session
    id = fields.String(dump_only=True)
