#!/usr/bin/env python

from redant.utils.database import sqldb as db
from redant.utils.string_util import generate_uuid
from marshmallow_sqlalchemy import ModelSchema
from marshmallow import fields

class ChannelEntity(db.Model):
    #
    __tablename__ = 'channels'
    #
    #
    channel_id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    channel_code = db.Column(db.String(64), nullable = False)
    timezone = db.Column(db.String(36), nullable = False)
    #
    #
    def __init__(self, channel_code, timezone='UTC', **kwargs):
        self.channel_code = channel_code
        self.timezone = timezone
    #
    #
    def create(self):
        db.session.add(self)
        db.session.commit()
        return self
    #
    #
    @classmethod
    def find_by__channel_code(cls, channel_code):
        return cls.query\
            .filter_by(channel_code = channel_code)\
            .first()
