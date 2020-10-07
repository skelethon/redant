#!/usr/bin/env python

from redant.utils.database import sqldb as db
from redant.utils.string_util import generate_uuid
from marshmallow_sqlalchemy import ModelSchema
from marshmallow import fields
from sqlalchemy import and_, or_

class ChannelEntity(db.Model):
    #
    __tablename__ = 'channels'
    #
    #
    channel_id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    channel_code = db.Column(db.String(64), nullable = False)
    channel_type = db.Column(db.String(16), nullable = False)
    timezone = db.Column(db.String(36), nullable = False)
    settings = db.Column(db.JSON, nullable=True, name='settings')
    enabled = db.Column(db.Boolean(), nullable = True)
    #
    #
    def __init__(self, channel_code, channel_type, timezone='UTC', settings=None, **kwargs):
        self.channel_code = channel_code
        self.channel_type = channel_type
        self.timezone = timezone
        self.settings = settings
    #
    #
    def create(self):
        db.session.add(self)
        db.session.commit()
        return self
    #
    #
    @classmethod
    def find_by__channel_code(cls, channel_code, enabled=True):
        q = cls.__apply_enabled(cls.query, enabled)
        return q.filter_by(channel_code = channel_code).first()
    #
    #
    @classmethod
    def find_all(cls, channel_type=None, enabled=True):
        q = cls.__apply_enabled(cls.query, enabled)
        if channel_type is not None:
            q = q.filter_by(channel_type = channel_type)
        return q.all()
    #
    #
    @classmethod
    def __apply_enabled(cls, q, enabled=True):
        if enabled is True:
            return q.filter(or_(ChannelEntity.enabled == None, ChannelEntity.enabled == True))
        elif enabled is False:
            return q.filter_by(enabled = False)
        return q
