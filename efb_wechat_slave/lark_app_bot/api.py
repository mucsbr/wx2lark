#! /usr/bin/env python3.8
import os
import logging
import requests
from requests_toolbelt import MultipartEncoder
from pathlib import Path
import tempfile

APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")

# const
TENANT_ACCESS_TOKEN_URI = "/open-apis/auth/v3/tenant_access_token/internal"
MESSAGE_URI = "/open-apis/im/v1/messages"
IMAGE_URI = "/open-apis/im/v1/images"
FILE_URI = "/open-apis/im/v1/files"


class MessageApiClient(object):
    def __init__(self, app_id, app_secret, lark_host):
        self._app_id = app_id
        self._app_secret = app_secret
        self._lark_host = lark_host
        self._tenant_access_token = ""

    @property
    def tenant_access_token(self):
        return self._tenant_access_token

    def send_file_msg(self, content):
        chat_id = "oc_9a4a07c72b8f0202d83cf51efec0ecb0"
        print(content)
        self.send("chat_id", chat_id, "file", content)

    def upload_file(self, path, path_io, filename):
        self._authorize_tenant_access_token()
        url = "{}{}".format(self._lark_host, FILE_URI)
        form = {'file_type': 'stream'}  # 需要替换具体的path
        if path:
            form['file'] = (path, open(path, 'rb'), 'audio/mpeg')
        else:
            path = filename
            form["file"] = (path, path_io, 'audio/mpeg')

        form["file_name"] = path
        multi_form = MultipartEncoder(form)
        headers = {
            "Authorization": "Bearer " + self.tenant_access_token,
        }
        headers['Content-Type'] = multi_form.content_type

        response = requests.request("POST", url, headers=headers, data=multi_form)
        print(response.headers['X-Tt-Logid'])  # for debug or oncall
        print(response.content)  # Print Response

        MessageApiClient._check_error_response(response)

        response_dict = response.json()
        data = response_dict.get("data", "")
        try:
            image_key = data["file_key"]
        except Exception as e:
            print("upload image to lark fail:", e)
            image_key = ""

        return image_key

    def upload_audio(self, path, path_io, filename):
        self._authorize_tenant_access_token()
        url = "{}{}".format(self._lark_host, FILE_URI)
        form = {'file_type': 'stream'}  # 需要替换具体的path
        if path:
            form['file'] = (path, open(path, 'rb'), 'audio/mpeg')
        else:
            path = filename + ".mp3"
            form["file"] = (path, path_io, 'audio/mpeg')

        form["file_name"] = path
        multi_form = MultipartEncoder(form)
        headers = {
            "Authorization": "Bearer " + self.tenant_access_token,
        }
        headers['Content-Type'] = multi_form.content_type

        response = requests.request("POST", url, headers=headers, data=multi_form)
        print(response.headers['X-Tt-Logid'])  # for debug or oncall
        print(response.content)  # Print Response

        MessageApiClient._check_error_response(response)

        response_dict = response.json()
        data = response_dict.get("data", "")
        try:
            image_key = data["file_key"]
        except Exception as e:
            print("upload image to lark fail:", e)
            image_key = ""

        return image_key

    def upload_image(self, image_path, image_io):
        self._authorize_tenant_access_token()
        url = "{}{}".format(self._lark_host, IMAGE_URI)

        form = {'image_type': 'message'}  # 需要替换具体的path
        if image_path:
            form['image'] = open(image_path, 'rb')
        else:
            form["image"] = image_io

        multi_form = MultipartEncoder(form)
        headers = {
            "Authorization": "Bearer " + self.tenant_access_token,
        }
        headers['Content-Type'] = multi_form.content_type

        response = requests.request("POST", url, headers=headers, data=multi_form)
        print(response.headers['X-Tt-Logid'])  # for debug or oncall
        print(response.content)  # Print Response

        MessageApiClient._check_error_response(response)

        response_dict = response.json()
        data = response_dict.get("data", "")
        try:
            image_key = data["image_key"]
        except Exception as e:
            print("upload image to lark fail:", e)
            image_key = ""

        return image_key

    def send_text_with_open_id(self, open_id, content):
        self.send("open_id", open_id, "text", content)

    def send(self, receive_id_type, receive_id, msg_type, content):
        # send message to user, implemented based on Feishu open api capability. doc link: https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/im-v1/message/create
        self._authorize_tenant_access_token()
        url = "{}{}?receive_id_type={}".format(
            self._lark_host, MESSAGE_URI, receive_id_type
        )
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.tenant_access_token,
        }
        print(headers)

        req_body = {
            "receive_id": receive_id,
            "content": content,
            "msg_type": msg_type,
        }
        print(req_body)
        resp = requests.post(url=url, headers=headers, json=req_body)
        MessageApiClient._check_error_response(resp)

    def save_file(self, message_id, file_key):
        self._authorize_tenant_access_token()
        url = "{}/open-apis/im/v1/messages/{}/resources/{}?type=file".format(
            self._lark_host, message_id, file_key
        )
        headers = {
            "Authorization": "Bearer " + self.tenant_access_token,
        }

        file: BinaryIO = tempfile.NamedTemporaryFile()  # type: ignore

        resp = requests.get(url, stream=True, headers=headers)
        if resp.status_code != 200:
            resp.raise_for_status()

        for block in resp.iter_content(1024):
            file.write(block)

        if file.seek(0, 2) <= 0:
            raise EOFError('File downloaded is Empty')

        file.seek(0)

        return Path(file.name), file

    def _authorize_tenant_access_token(self):
        # get tenant_access_token and set, implemented based on Feishu open api capability. doc link: https://open.feishu.cn/document/ukTMukTMukTM/ukDNz4SO0MjL5QzM/auth-v3/auth/tenant_access_token_internal
        url = "{}{}".format(self._lark_host, TENANT_ACCESS_TOKEN_URI)
        req_body = {"app_id": self._app_id, "app_secret": self._app_secret}
        response = requests.post(url, req_body)
        MessageApiClient._check_error_response(response)
        self._tenant_access_token = response.json().get("tenant_access_token")

    @staticmethod
    def _check_error_response(resp):
        # check if the response contains error information
        if resp.status_code != 200:
            resp.raise_for_status()
        response_dict = resp.json()
        code = response_dict.get("code", -1)
        if code != 0:
            logging.error(response_dict)
            raise LarkException(code=code, msg=response_dict.get("msg"))


class LarkException(Exception):
    def __init__(self, code=0, msg=None):
        self.code = code
        self.msg = msg

    def __str__(self) -> str:
        return "{}:{}".format(self.code, self.msg)

    __repr__ = __str__
