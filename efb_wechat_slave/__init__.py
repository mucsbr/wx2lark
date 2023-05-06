# coding: utf-8

import io
import json
import logging
import tempfile
import time
import threading
from gettext import translation
from json import JSONDecodeError
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Dict, Optional, List, Tuple, Callable, BinaryIO, IO
from uuid import uuid4
from .send_lark import send_lark_cus, message_api_client

import yaml
from multiprocessing import Process
from pkg_resources import resource_filename
from pyqrcode import QRCode
from typing_extensions import Final

# from ehforwarderbot import Message, MsgType, Status, Chat, coordinator
#from ehforwarderbot import utils as efb_utils
# from ehforwarderbot.channel import SlaveChannel
# from ehforwarderbot.chat import SystemChat, SelfChatMember
# from ehforwarderbot.exceptions import EFBMessageTypeNotSupported, EFBMessageError, EFBChatNotFound, \
#     EFBOperationNotSupported
# from ehforwarderbot.message import MessageCommands, MessageCommand
# from ehforwarderbot.status import MessageRemoval
# from ehforwarderbot.types import MessageID, ModuleID, InstanceID, ChatID
# from ehforwarderbot.utils import extra
from . import utils as ews_utils
from .__version__ import __version__
from .chats import ChatManager
from .slave_message import SlaveMessageManager
from .utils import ExperimentalFlagsManager
from .vendor import wxpy
from .vendor.wxpy import ResponseError
from .vendor.wxpy.utils import PuidMap
from .lark_app_bot import app, msg_queue


class WeChatChannel:
    """
    EFB Channel - WeChat Slave Channel
    Based on wxpy (itchat), WeChat Web Client

    Author: Eana Hufwe <https://github.com/blueset>
    """

    channel_name = "WeChat Slave"
    channel_emoji = "💬"
    # channel_id = ModuleID('blueset.wechat')

    __version__ = __version__

    # supported_message_types = {MsgType.Text, MsgType.Sticker, MsgType.Image,
    #                            MsgType.File, MsgType.Video, MsgType.Link, MsgType.Voice,
    #                            MsgType.Animation}
    logger: logging.Logger = logging.getLogger(
        "plugins.%s.WeChatChannel")
    done_reauth: threading.Event = threading.Event()
    _stop_polling_event: threading.Event = threading.Event()

    config: Dict[str, Any] = dict()

    bot: wxpy.Bot

    # GNU Gettext Translator

    translator = translation("efb_wechat_slave",
                             resource_filename('efb_wechat_slave', 'locale'),
                             fallback=True)

    _: Callable = translator.gettext
    ngettext: Callable = translator.ngettext

    # Constants
    MAX_FILE_SIZE: int = 5 * 2 ** 20
    SYSTEM_ACCOUNTS: Final = {
        # TRANSLATORS: Translate this to the corresponding display name of the WeChat system account. Guessed names are not accepted.
        'filehelper': _('filehelper'),
        # TRANSLATORS: Translate this to the corresponding display name of the WeChat system account. Guessed names are not accepted.
        'newsapp': _('newsapp'),
        # TRANSLATORS: Translate this to the corresponding display name of the WeChat system account. Guessed names are not accepted.
        'fmessage': _('fmessage'),
        # TRANSLATORS: Translate this to the corresponding display name of the WeChat system account. Guessed names are not accepted.
        'weibo': _('weibo'),
        # TRANSLATORS: Translate this to the corresponding display name of the WeChat system account. Guessed names are not accepted.
        'qqmail': _('qqmail'),
        # TRANSLATORS: Translate this to the corresponding display name of the WeChat system account. Guessed names are not accepted.
        'tmessage': _('tmessage'),
        # TRANSLATORS: Translate this to the corresponding display name of the WeChat system account. Guessed names are not accepted.
        'qmessage': _('qmessage'),
        # TRANSLATORS: Translate this to the corresponding display name of the WeChat system account. Guessed names are not accepted.
        'qqsync': _('qqsync'),
        # TRANSLATORS: Translate this to the corresponding display name of the WeChat system account. Guessed names are not accepted.
        'floatbottle': _('floatbottle'),
        # TRANSLATORS: Translate this to the corresponding display name of the WeChat system account. Guessed names are not accepted.
        'lbsapp': _('lbsapp'),
        # TRANSLATORS: Translate this to the corresponding display name of the WeChat system account. Guessed names are not accepted.
        'shakeapp': _('shakeapp'),
        # TRANSLATORS: Translate this to the corresponding display name of the WeChat system account. Guessed names are not accepted.
        'medianote': _('medianote'),
        # TRANSLATORS: Translate this to the corresponding display name of the WeChat system account. Guessed names are not accepted.
        'qqfriend': _('qqfriend'),
        # TRANSLATORS: Translate this to the corresponding display name of the WeChat system account. Guessed names are not accepted.
        'readerapp': _('readerapp'),
        # TRANSLATORS: Translate this to the corresponding display name of the WeChat system account. Guessed names are not accepted.
        'blogapp': _('blogapp'),
        # TRANSLATORS: Translate this to the corresponding display name of the WeChat system account. Guessed names are not accepted.
        'facebookapp': _('facebookapp'),
        # TRANSLATORS: Translate this to the corresponding display name of the WeChat system account. Guessed names are not accepted.
        'masssendapp': _('masssendapp'),
        # TRANSLATORS: Translate this to the corresponding display name of the WeChat system account. Guessed names are not accepted.
        'meishiapp': _('meishiapp'),
        # TRANSLATORS: Translate this to the corresponding display name of the WeChat system account. Guessed names are not accepted.
        'feedsapp': _('feedsapp'),
        # TRANSLATORS: Translate this to the corresponding display name of the WeChat system account. Guessed names are not accepted.
        'voip': _('voip'),
        # TRANSLATORS: Translate this to the corresponding display name of the WeChat system account. Guessed names are not accepted.
        'blogappweixin': _('blogappweixin'),
        # TRANSLATORS: Translate this to the corresponding display name of the WeChat system account. Guessed names are not accepted.
        'weixin': _('weixin'),
        # TRANSLATORS: Translate this to the corresponding display name of the WeChat system account. Guessed names are not accepted.
        'brandsessionholder': _('brandsessionholder'),
        # TRANSLATORS: Translate this to the corresponding display name of the WeChat system account. Guessed names are not accepted.
        'weixinreminder': _('weixinreminder'),
        # TRANSLATORS: Translate this to the corresponding display name of the WeChat system account. Guessed names are not accepted.
        'officialaccounts': _('officialaccounts'),
        # TRANSLATORS: Translate this to the corresponding display name of the WeChat system account. Guessed names are not accepted.
        'notification_messages': _('notification_messages'),
        # TRANSLATORS: Translate this to the corresponding display name of the WeChat system account. Guessed names are not accepted.
        'wxitil': _('wxitil'),
        # TRANSLATORS: Translate this to the corresponding display name of the WeChat system account. Guessed names are not accepted.
        'userexperience_alarm': _('userexperience_alarm'),
    }
    # MEDIA_MSG_TYPES: Final = {MsgType.Voice, MsgType.Video, MsgType.Animation,
    #                           MsgType.Image, MsgType.Sticker, MsgType.File}

    QUOTE_DIVIDER = "- - - - - - - - - - - - - - -"

    def __init__(self):
        """
        Initialize the channel

        Args:
            coordinator (:obj:`ehforwarderbot.coordinator.EFBCoordinator`):
                The EFB framework coordinator
        """
        # super().__init__()
        # self.load_config()

        PuidMap.SYSTEM_ACCOUNTS = self.SYSTEM_ACCOUNTS

        self.flag: ExperimentalFlagsManager = ExperimentalFlagsManager(self)

        self.qr_uuid: Tuple[str, int] = ('', 0)
        self.master_qr_picture_id: Optional[str] = None

        self.authenticate('console_qr_code', first_start=True)

        # Managers
        self.slave_message: SlaveMessageManager = SlaveMessageManager(self)
        self.chats: ChatManager = ChatManager(self)
        # self.user_auth_chat = SystemChat(channel=self,
        #                                  name=self._("EWS User Auth"),
        #                                  uid=ChatID("__ews_user_auth__"))

    # def load_config(self):
    #     """
    #     Load configuration from path specified by the framework.
    #
    #     Configuration file is in YAML format.
    #     """
    #     config_path = efb_utils.get_config_path(self.channel_id)
    #     if not config_path.exists():
    #         return
    #     with config_path.open() as f:
    #         d = yaml.full_load(f)
    #         if not d:
    #             return
    #         self.config: Dict[str, Any] = d

    #
    # Utilities
    #
    def console_qr_code(self, uuid, status, qrcode=None):
        status = int(status)
        if self.qr_uuid == (uuid, status):
            return
        self.qr_uuid = (uuid, status)
        if status == 201:
            qr = self._('Confirm on your phone.')
            return self.logger.log(99, qr)
        elif status == 200:
            qr = self._("Successfully logged in.")
            return self.logger.log(99, qr)
        else:
            # 0: First QR code
            # 408: Updated QR code
            qr = self._("EWS: Please scan the QR code with your camera, screenshots will not work. ({0}, {1})") \
                     .format(uuid, status) + "\n"
            if status == 408:
                qr += self._("QR code expired, please scan the new one.") + "\n"
            qr += "\n"
            qr_url = "https://login.weixin.qq.com/l/" + uuid
            qr_obj = QRCode(qr_url)
            if self.flag("imgcat_qr"):
                qr_file = io.BytesIO()
                qr_obj.png(qr_file, scale=10)
                qr_file.seek(0)
                qr += ews_utils.imgcat(qr_file,
                                       f"{self.channel_id}_QR_{uuid}.png")
            else:
                qr += qr_obj.terminal()
            qr += "\n" + self._("If the QR code was not shown correctly, please visit:\n"
                                "https://login.weixin.qq.com/qrcode/{0}").format(uuid)
            return self.logger.log(99, qr)

    def master_qr_code(self, uuid, status, qrcode=None):
        status = int(status)
        if self.qr_uuid == (uuid, status):
            return
        self.qr_uuid = (uuid, status)

        # msg = Message(
        #     uid=f"ews_auth_{uuid}_{status}_{uuid4()}",
        #     type=MsgType.Text,
        #     chat=self.user_auth_chat,
        #     author=self.user_auth_chat.other,
        #     deliver_to=coordinator.master,
        # )

        if status == 201:
            # msg.type = MsgType.Text
            # msg.text = self._('Confirm on your phone.')
            # self.master_qr_picture_id = None
            print('Confirm on your phone.')
        elif status == 200:
            # msg.type = MsgType.Text
            # msg.text = self._("Successfully logged in.")
            # self.master_qr_picture_id = None
            print("Successfully logged in.")
        elif uuid != self.qr_uuid:
            qr = self._("EWS: Please scan the QR code with your camera, screenshots will not work. ({0}, {1})") \
                     .format(uuid, status) + "\n"
            qr += self._("QR code expired, please scan the new one.") + "\n"
            qr += "\n"
            qr_url = "https://login.weixin.qq.com/l/" + uuid
            qr_obj = QRCode(qr_url)
            if self.flag("imgcat_qr"):
                qr_file = io.BytesIO()
                qr_obj.png(qr_file, scale=10)
                qr_file.seek(0)
                qr += ews_utils.imgcat(qr_file,
                                       f"{self.channel_id}_QR_{uuid}.png")
            else:
                qr += qr_obj.terminal()

    def exit_callback(self):
        self.logger.debug('Calling exit callback...')
        if self._stop_polling_event.is_set():
            return
        print("WeChat server has logged you out. Please log in again when you are ready.")
        on_log_out = self.flag("on_log_out")
        on_log_out = on_log_out if on_log_out in (
            "command", "idle", "reauth") else "command"
        if on_log_out == "command":
            send_lark_cus("Log in again, 掉登录了！！！")

        elif on_log_out == "reauth":
            if self.flag("qr_reload") == "console_qr_code":
                print("Please check your log to continue.")
                send_lark_cus("Please check your log to continue.")
            self.reauth()


    def flask_app(self):
        print("start app run")
        try:
            app.run(host="0.0.0.0", port=3000, debug=False)
        except Exception as e:
            print(e)

    def start_app(self):
        #先注释掉了，这里是飞书发微信的逻辑
        pass
        # threading.Thread(target=self.flask_app, name="flask thread").start()
        # threading.Thread(target=self.send_message, name="send chat thread").start()

    def poll(self):
        self.start_app()
        self.bot.start()
        self._stop_polling_event.wait()
        # while not self.stop_polling:
        #     if not self.bot.alive:
        #         self.done_reauth.wait()
        #         self.done_reauth.clear()
        self.logger.debug("%s (%s) gracefully stopped.",
                          self.channel_name)

    def send_message(self):
        """Send a message to WeChat.
        Supports text, image, sticker, and file.

        Args:
            msg (channel.Message): Message Object to be sent.

        Returns:
            This method returns nothing.

        Raises:
            EFBChatNotFound:
                Raised when a chat required is not found.

            EFBMessageTypeNotSupported:
                Raised when the message type sent is not supported by the
                channel.

            EFBOperationNotSupported:
                Raised when an message edit request is sent, but not
                supported by the channel.

            EFBMessageNotFound:
                Raised when an existing message indicated is not found.
                E.g.: The message to be edited, the message referred
                in the :attr:`msg.target <.Message.target>`
                attribute.

            EFBMessageError:
                Raised when other error occurred while sending or editing the
                message.
        """
        while True:
            try:
                message = msg_queue.get()
                content = message.content
                recv_user = "HLL"
            except Exception as e:
                print(e)
                continue

            if message.message_type == "text":
                try:
                    cc = "       "
                    json_str = json.loads(content)
                    cc = json_str["text"]
                    recv_user, real_content = cc.split("$")
                    if recv_user[0] == "@":
                        _, recv_user = recv_user.split(" ", maxsplit=1)

                except Exception as e:
                    print(e)
                    recv_user = "HLL"
                    real_content = cc

                try:
                    chat: wxpy.Chat = self.chats.get_chat_by_name(recv_user)
                    if not chat:
                        continue
                    self.logger.info("Sending message to WeChat:\n"
                                     # "uid: %s\n"
                                     "UserName: %s\n"
                                     "NickName: %s\n"
                                     # "Type: %s\n"
                                     "Text: %s",
                                     # msg.uid,
                                     # msg.chat.uid,
                                     chat.user_name, chat.name, content)

                    # chat.mark_as_read()
                    self._bot_send_msg(chat, real_content)
                except Exception as e:
                    print(e)
            elif message.content == "file":
                path = ""
                try:
                    message_id = message.message_id
                    json_str = json.loads(content)
                    file_key = json_str["file_key"]
                    file_name = json_str["file_name"]
                    path, file = message_api_client.save_file(message_id, file_key)

                    recv_user, filename = file_name.split("$")

                except Exception as e:
                    print(e)
                    if path == "":
                        continue
                    recv_user = "HLL"
                    filename = file_name

                try:
                    chat: wxpy.Chat = self.chats.get_chat_by_name(recv_user)
                    if not chat:
                        continue
                    self.logger.info("Sending message to WeChat:\n"
                                     # "uid: %s\n"
                                     "UserName: %s\n"
                                     "NickName: %s\n"
                                     # "Type: %s\n"
                                     "Text: %s",
                                     # msg.uid,
                                     # msg.chat.uid,
                                     chat.user_name, chat.name, content)

                    # chat.mark_as_read()
                    self._bot_send_file(chat, filename, file=file)
                except Exception as e:
                    self.logger.exception(
                        "Error occurred while marking chat as read. (%s)", e)

    def get_chat_list(self, param: str = "") -> str:
        refresh = False
        if param:
            if param == "-r":
                refresh = True
            else:
                return self._("Unknown parameter: {}.").format(param)
        l: List[wxpy.Chat] = self.bot.chats(refresh)

        msg = self._("Chat list:") + "\n"
        for i in l:
            alias = ews_utils.wechat_string_unescape(getattr(i, 'remark_name', '') or
                                                     getattr(i, 'display_name', ''))
            name = ews_utils.wechat_string_unescape(i.nick_name)
            display_name = "%s (%s)" % (
                alias, name) if alias and alias != name else name
            chat_type = "?"
            if isinstance(i, wxpy.MP):
                # TRANSLATORS: Acronym for MP accounts
                chat_type = self._('MP')
            elif isinstance(i, wxpy.Group):
                # TRANSLATORS: Acronym for groups
                chat_type = self._('Gr')
            elif isinstance(i, wxpy.User):
                # TRANSLATORS: Acronym for users/friends
                chat_type = self._('Fr')
            msg += "\n%s: [%s] %s" % (i.puid, chat_type, display_name)

        return msg

    # @extra(name=_("Set alias"),
    #        desc=_("Set an alias (remark name) for friends. Not applicable to "
    #               "groups and MPs.\n"
    #               "Usage:\n"
    #               "    {function_name} id [alias]\n"
    #               "    id: Chat ID, available from \"Show chat list\".\n"
    #               "    alias: Alias. Leave empty to delete alias."))
    def set_alias(self, r_param: str = "") -> str:
        if r_param:
            param = r_param.split(maxsplit=1)
            if len(param) == 1:
                cid = param[0]
                alias = ""
            else:
                cid, alias = param
        else:
            return self.set_alias.desc  # type: ignore

        chat = self.bot.search(cid)

        if not chat:
            return self._("Chat {0} is not found.").format(cid)

        if not isinstance(chat, wxpy.User):
            return self._("Remark name is only applicable to friends.")

        chat.set_remark_name(alias)

        if alias:
            return self._("\"{0}\" now has remark name \"{1}\".").format(chat.nick_name, alias)
        else:
            return self._("Remark name of \"{0}\" has been removed.").format(chat.nick_name)

    # @extra(name=_("Log out"),
    #        desc=_("Log out from WeChat and try to log in again.\n"
    #               "Usage: {function_name}"))
    def force_log_out(self, _: str = "") -> str:
        self.bot.logout()
        self.exit_callback()
        return self._("Done.")

    # region [Command functions]

    def reauth(self, command=False):
        # Remove wxpy.pkl if last edited earlier than 5 minutes ago.
        # last_session = "wxpy.pkl"
        # if (time.time() - last_session.stat().st_mtime) < (5 * 60):
        #     last_session.unlink()
        #
        msg = self._("Preparing to log in...")
        qr_reload = self.flag("qr_reload")
        if command and qr_reload == "console_qr_code":
            msg += "\n" + self._("Please check your log to continue.")

        threading.Thread(target=self.authenticate, args=(
            qr_reload,), name="EWS reauth thread").start()
        return msg

    # endregion [Command functions]

    def authenticate(self, qr_reload, first_start=False):
        self.master_qr_picture_id = None
        qr_callback = getattr(self, qr_reload, self.master_qr_code)
        if getattr(self, 'bot', None):  # if a bot exists
            self.bot.cleanup()
        # with coordinator.mutex:
        self.bot: wxpy.Bot = wxpy.Bot(cache_path=str("wxpy.pkl"),
                                      qr_callback=qr_callback,
                                      logout_callback=self.exit_callback,
                                      user_agent=self.flag('user_agent'),
                                      start_immediately=not first_start)
        self.bot.enable_puid(
            "wxpy_puid.pkl",
            self.flag('puid_logs')
        )
        self.done_reauth.set()
        if hasattr(self, "slave_message"):
            self.slave_message.bot = self.bot
            self.slave_message.wechat_msg_register()

    def add_friend(self, username: str = None, verify_information: str = "") -> str:
        if not username:
            return self._("Empty username (UE02).")
        try:
            self.bot.add_friend(
                user=username, verify_content=verify_information)
        except wxpy.ResponseError as r:
            return self._("Error occurred while processing (AF01).") + "\n\n{}: {!r}".format(r.err_code, r.err_msg)
        return self._("Request sent.")

    def accept_friend(self, username: str = None, verify_information: str = "") -> str:
        if not username:
            return self._("Empty username (UE03).")
        try:
            self.bot.accept_friend(
                user=username, verify_content=verify_information)
        except wxpy.ResponseError as r:
            return self._("Error occurred while processing (AF02).") + "n\n{}: {!r}".format(r.err_code, r.err_msg)
        return self._("Request accepted.")

    # def get_chats(self) -> List[Chat]:
    #     """
    #     Get all chats available from WeChat
    #     """
    #     return self.chats.get_chats()

    # def get_chat(self, chat_uid: str) -> Chat:
    #     chat = self.chats.search_chat(uid=chat_uid)
    #     if not chat:
    #         raise EFBChatNotFound()
    #     else:
    #         return chat

    def stop_polling(self):
        self.bot.cleanup()
        if not self._stop_polling_event.is_set():
            self._stop_polling_event.set()
        else:
            self.done_reauth.set()

    def _bot_send_msg(self, chat: wxpy.Chat, message: str) -> wxpy.SentMessage:
        try:
            return chat.send_msg(message)
        except wxpy.ResponseError as e:
            e = self.substitute_known_error_reason(e)
            raise EOFError(self._("Error from Web WeChat while sending message: [{code}] {message}")
                                  .format(code=e.err_code, message=e.err_msg))

    def _bot_send_file(self, chat: wxpy.Chat, filename: str, file: IO[bytes]) -> wxpy.SentMessage:
        try:
            return chat.send_file(filename, file=file)
        except wxpy.ResponseError as e:
            e = self.substitute_known_error_reason(e)
            raise EOFError(self._("Error from Web WeChat while sending message: [{code}] {message}")
                           .format(code=e.err_code, message=e.err_msg))

    # def _bot_send_image(self, chat: wxpy.Chat, filename: str, file: IO[bytes]) -> wxpy.SentMessage:
    #     try:
    #         return chat.send_image(filename, file=file)
    #     except wxpy.ResponseError as e:
    #         e = self.substitute_known_error_reason(e)
    #         raise EFBMessageError(self._("Error from Web WeChat while sending image: [{code}] {message}")
    #                               .format(code=e.err_code, message=e.err_msg))
    #
    # def _bot_send_video(self, chat: wxpy.Chat, filename: str, file: IO[bytes]) -> wxpy.SentMessage:
    #     try:
    #         return chat.send_video(filename, file=file)
    #     except wxpy.ResponseError as e:
    #         e = self.substitute_known_error_reason(e)
    #         raise EFBMessageError(self._("Error from Web WeChat while sending video: [{code}] {message}")
    #                               .format(code=e.err_code, message=e.err_msg))

    def substitute_known_error_reason(self, err: wxpy.ResponseError) -> wxpy.ResponseError:
        if not err.err_msg:
            issue_url = "https://ews.1a23.studio/issues/55"
            if err.err_code in (1101, 1102, 1103):
                err.err_msg = self._("Your Web WeChat session might be expired. "
                                     "Please try to log out with the “force_log_out” command, and log in again. "
                                     "If you believe that is not the case, please leave a comment at {issue_url} .").format(
                    issue_url=issue_url
                )
            elif err.err_code == 1204:
                err.err_msg = self._(
                    "You don’t have access to the chat that you are trying to send message to.")
            elif err.err_code == 1205:
                err.err_msg = self._("You might have sent your messages too fast. Please try to slow down "
                                     "and retry after a while.")
            elif err.err_code == 3:
                err.err_msg = self._("Your mobile WeChat client is offline for too long. Please ensure your mobile"
                                     "WeChat client is always online.")
            else:
                err.err_msg = self._("This is an unknown error from Web WeChat which we know nothing about why this "
                                     "is happening. If you have seen a pattern or if you happen to know the reason "
                                     "for this error code, please leave a comment at {issue_url} .").format(
                    issue_url=issue_url
                )
        return err

    # def get_message_by_id(self, chat: Chat, msg_id: MessageID) -> Optional['Message']:
    #     raise EFBOperationNotSupported()
