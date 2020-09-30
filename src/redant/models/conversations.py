#!/usr/bin/env python

from redant import errors
from redant.utils.database import sqldb as db
from redant.models.channels import ChannelEntity
from redant.models.chatters import ChatterEntity
from redant.utils.object_util import json_dumps
from redant.utils.string_util import generate_uuid
from marshmallow_sqlalchemy import ModelSchema
from marshmallow import fields
from sqlalchemy import desc

class ConversationModel(db.Model):
    __tablename__ = 'conversations'
    #
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    state = db.Column(db.String(32), nullable = False)
    overall_status = db.Column(db.Integer(), nullable = False, default=0)
    #
    story = db.Column(db.JSON, nullable=True)
    phone_number = db.Column(db.String(16), nullable = True)
    #
    chatter_code = db.Column(db.String(64), nullable = False)
    chatter_id = db.Column(db.String(36), db.ForeignKey('chatters.chatter_id'), nullable=True)
    chatter = db.relationship('ChatterEntity', backref=db.backref('chatters', lazy='dynamic'))
    #
    channel_code = db.Column(db.String(64), nullable = False)
    channel_id = db.Column(db.String(36), db.ForeignKey('channels.channel_id'), nullable=True)
    channel = db.relationship('ChannelEntity', backref=db.backref('channels', lazy='dynamic'))
    #
    #
    def create(self):
        #
        if self.channel_code is None:
            raise errors.ModelArgumentError('[channel_code] is None')
        #
        channel = ChannelEntity.find_by__channel_code(self.channel_code)
        if channel is None:
            raise errors.ChannelNotFoundError('channel[' + self.channel_code + '] not found')
        self.channel_id = channel.channel_id
        #
        #
        if self.chatter_code is None:
            raise errors.ModelArgumentError('[chatter_code] is None')
        #
        chatter = ChatterEntity.find_by__chatter_code(self.chatter_code)
        if chatter is None:
            chatter = ChatterEntity(chatter_code=self.chatter_code, phone_number=self.phone_number)
            chatter.create()
            pass
        self.chatter_id = chatter.chatter_id
        #
        #
        db.session.add(self)
        db.session.commit()
        return self
    #
    #
    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
            return self, None
        except Exception as exception:
            db.session.rollback()
            return None, exception
    #
    #
    def __init__(self, channel_code, chatter_code, phone_number=None, state='begin', **kwargs):
        self.channel_code = channel_code
        self.chatter_code = chatter_code
        self.phone_number = phone_number
        self.state = state
    #
    def __repr__(self):
        return json_dumps(self, ['id', 'created_at', 'state', 'channel_code', 'chatter_code', 'phone_number'])
    #
    #
    @classmethod
    def find_by__channel__chatter(cls, channel_code, chatter_code):
        return cls.query\
            .filter_by(channel_code = channel_code)\
            .filter_by(chatter_code = chatter_code)\
            .order_by(desc(ConversationModel.created_at))\
            .first()
    #
    @classmethod
    def count_by__channel__chatter(cls, channel_code, chatter_code, overall_status=None, latest_created_time=None):
        #
        q = cls.query\
            .filter_by(channel_code = channel_code)\
            .filter_by(chatter_code = chatter_code)
        #
        if overall_status is not None:
            q = q.filter_by(overall_status = overall_status)
        #
        if latest_created_time is not None:
            q = q.filter(ConversationModel.created_at >= latest_created_time)
        #
        return q.count()


class ConversationSchema(ModelSchema):
    class Meta(ModelSchema.Meta):
        model = ConversationModel
        sqla_session = db.session
    id = fields.String(dump_only=True)
