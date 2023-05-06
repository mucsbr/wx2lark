#!/usr/bin/env python3.8

import os
import logging
import requests
from .api import MessageApiClient
from .event import MessageReceiveEvent, UrlVerificationEvent, EventManager
from flask import Flask, jsonify
from queue import Queue

app = Flask(__name__)
msg_queue = Queue(maxsize=0)

# load from env
APP_ID = ""
APP_SECRET = ""
VERIFICATION_TOKEN = ""
ENCRYPT_KEY = ""
# ENCRYPT_KEY = ""
LARK_HOST = "https://open.feishu.cn"

event_manager = EventManager()


@event_manager.register("url_verification")
def request_url_verify_handler(req_data: UrlVerificationEvent):
    # url verification, just need return challenge
    if req_data.event.token != VERIFICATION_TOKEN:
        raise Exception("VERIFICATION_TOKEN is invalid")
    return jsonify({"challenge": req_data.event.challenge})


@event_manager.register("im.message.receive_v1")
def message_receive_event_handler(req_data: MessageReceiveEvent):
    sender_id = req_data.event.sender.sender_id
    message = req_data.event.message
    if message.message_type != "text" and message.message_type != "file":
        logging.warn("Other types of messages have not been processed yet")
        return jsonify()
        # get open_id and text_content
    # open_id = sender_id.open_id
    # text_content = message.content
    # echo text message
    print(message)
    msg_queue.put(message)
    # message_api_client.send_text_with_open_id(open_id, text_content)
    return jsonify()


@app.errorhandler
def msg_error_handler(ex):
    logging.error(ex)
    response = jsonify(message=str(ex))
    response.status_code = (
        ex.response.status_code if isinstance(ex, requests.HTTPError) else 500
    )
    return response


@app.route("/", methods=["POST"])
def callback_event_handler():
    # init callback instance and handle
    event_handler, event = event_manager.get_handler_with_event(VERIFICATION_TOKEN, ENCRYPT_KEY)

    return event_handler(event)
