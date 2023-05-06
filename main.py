# coding: utf-8
from efb_wechat_slave import WeChatChannel

if __name__ == '__main__':
    wc = WeChatChannel()
    wc.poll()
