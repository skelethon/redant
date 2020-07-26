#!/usr/bin/env python

import logging
from flask import Blueprint, request, jsonify, make_response
from redant.models.chatters import ChatterEntity, ChatterSchema

chatter_routes = Blueprint("chatter_routes", __name__)

@chatter_routes.route('/', methods=['GET'])
def get_chatters():
    try:
        get_chatters = ChatterEntity.query.all()
        chatter_schema = ChatterSchema(many=True)
        chatters = chatter_schema.dump(get_chatters)
        return make_response(jsonify({"chatters": chatters}))
    except Exception as err:
        if log.isEnabledFor(logging.ERROR):
            log.error('Error: %s', str(err))
        raise err
