# coding: utf-8

import requests
import json
from .lark_app_bot.api import MessageApiClient
from .lark_app_bot.server import APP_ID, APP_SECRET, VERIFICATION_TOKEN, ENCRYPT_KEY


LARK_HOST = "https://open.feishu.cn"
webhook_url_private = ""
webhook_url_group = ""
message_api_client = MessageApiClient(APP_ID, APP_SECRET, LARK_HOST)


def send_lark_text(content, is_user):
    if is_user:
        webhook_url = webhook_url_private
    else:
        webhook_url = webhook_url_group

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", webhook_url, headers=headers, data=content)
    ss = response.text
    response.close()

    return ss

def send_lark_cus(txt):
    lark_msg = {
        "msg_type": "text",
        "content": {
            "text": txt
        }
    }
    content = json.dumps(lark_msg)

    webhook_url = 'https://open.feishu.cn/open-apis/bot/v2/hook/172dda1e-7874-49f3-9557-cba2a6d35998'
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", webhook_url, headers=headers, data=content)
    ss = response.text
    response.close()

    return ss
