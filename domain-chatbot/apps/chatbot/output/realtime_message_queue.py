import queue
import re
import threading
import traceback
import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from ..utils.chat_message_utils import format_chat_text
import threading

# 聊天消息通道
chat_channel = "chat_channel"

# 创建一个线程安全的队列
chat_queue = queue.SimpleQueue()


class RealtimeMessage():
    type: str
    user_name: str
    content: str
    expand: str

    def __init__(self, type: str, user_name: str, content: str, expand: str = None) -> None:
        self.type = type
        self.user_name = user_name
        self.content = content
        self.expand = expand

    def to_dict(self):
        return {
            "type": self.type,
            "user_name": self.user_name,
            "content": self.content,
            "expand": self.expand
        }


def put_message(message: RealtimeMessage):
    global chat_queue
    chat_queue.put(message)


def send_message():
    global chat_queue
    channel_layer = get_channel_layer()
    send_message_exe = async_to_sync(channel_layer.group_send)
    while True:
        try:
            message = chat_queue.get()
            if (message != None and message != ''):
                chat_message = {"type": "chat_message",
                                "message":  message.to_dict()}
                send_message_exe(chat_channel, chat_message)
        except Exception as e:
            traceback.print_exc()


def realtime_callback(role_name: str, you_name: str, content: str):
    if not hasattr(realtime_callback, "message_buffer"):
        realtime_callback.message_buffer = ""
    realtime_callback.message_buffer += content
    # 如果 content 以结束标点符号结尾，打印并清空缓冲区
    # if content.endswith(("。", "！", "？", "\n")):
    if re.match(r"^(.+[。．！？~\n]|.{10,}[、,])", realtime_callback.message_buffer):
        realtime_callback.message_buffer = format_chat_text(
            role_name, you_name, realtime_callback.message_buffer)
        put_message(RealtimeMessage(
            type="user", user_name=you_name, content=realtime_callback.message_buffer))
        realtime_callback.message_buffer = ""


class RealtimeMessageQueryJobTask():

    @staticmethod
    def start():
        # 创建后台线程
        background_thread = threading.Thread(target=send_message)
        # 将后台线程设置为守护线程，以便在主线程结束时自动退出
        background_thread.daemon = True
        # 启动后台线程
        background_thread.start()
        print("=> RealtimeMessageQueryJobTask start")
