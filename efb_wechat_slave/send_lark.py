# coding: utf-8

import requests
import json
from .lark_app_bot.api import MessageApiClient
from .lark_app_bot.server import APP_ID, APP_SECRET, VERIFICATION_TOKEN, ENCRYPT_KEY


LARK_HOST = "https://open.feishu.cn"
#填写群机器人的webhook地址, 这里填写两个意思是个人消息和群消息分成两个机器人接收比较好，如果只用一个两个可以填同一个地址
webhook_url_private = ""
webhook_url_group = ""
# 先注释掉这个飞书转微信的逻辑
# message_api_client = MessageApiClient(APP_ID, APP_SECRET, LARK_HOST)
message_api_client = None


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
