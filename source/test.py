# coding=utf-8
# 在线Chat节点
import sys
# import base64
import json
from time import sleep
from collections import deque
import threading

# 1.日志系统初始化,配置log等级
from utility import mlogging

mlogging.logger_config('chat', mlogging.INFO, False)
# 2.导入logger模块
from utility.mlogging import logger
# from utility.keyboard import KBHit


from mq_base_node import MqBaseNode, mq_close
from chat.openai_chat import OpenAIChat
from chat.doubao_chat import DoubaoChat


class ChatNode(MqBaseNode):
    """chat节点
    """

    def __init__(self, config: dict):
        """初始化
        Args:
            config  app参数配置信息
        """
        self.chat_config = config['chat']

        # ---------------rabbitmq------------------
        super().__init__(config['rabbitmq'])

        self.que_max_len = 5000

        self.set_que_max_len(self.que_max_len)

        # -----------------------------------------
        # 键盘控制
        # self.keyboard = KBHit()
        self.node_exit = False

        # self.chat = OpenAIChat(self.chat_config)
        self.chat = DoubaoChat(self.chat_config)
        ## 本轮聊天ID
        self.chat_id = 0
        ## 取消的聊天ID
        self.cancel_chat_id = -1

    '''
    def keyboard_control(self):
        """control task.
        """
        if self.keyboard.kbhit():
            key_value = ord(self.keyboard.getch())
            if key_value == ord('q'): 
                logger.info('keyboard exit.')
                self.close()
    '''

    @mq_close
    def close(self):
        """关闭节点
        """
        self.node_exit = True
        logger.info('app exit')

    def create_answer_msg(self, msg: dict, chat_id: int):
        """创建聊天响应消息
        Args:
            msg, 聊天响应消息
        """
        data_obj = {
            'node': "chat",
            'topic': "chat/answer",
            'type': "json",
            'data': {
                'chat_id': chat_id,
                'seq': msg['seq'],
                'text': msg['text'],
            }
        }
        return data_obj

    def handle_mq_msg(self, msg: dict, stream=True):
        """mq 消息处理, 根据请求执行相应操作
        Args:
            msg  从订阅节点接收到的消息
            stream 是否启动流失响应
        TODO: 增加聊天打断检测
        """
        logger.debug("got mq msg, topic: {}".format(msg['topic']))
        topic = msg['topic']

        if topic == 'request/cancel':
            self.cancel_chat_id = msg['data']['chat_id']
            logger.info('receive cancel signal,current chat_id: {}, cancel chat_id: {}'.format(self.chat_id,
                                                                                               self.cancel_chat_id))

        elif topic == 'asr/response':
            logger.debug(msg)
            text = msg['data']['text']
            self.chat_id = msg['data']['chat_id']
            logger.info('user: {}'.format(text))

            ## 判断是否为取消的ID,如果是则不进行chat请求
            if self.chat_id <= self.cancel_chat_id:
                logger.info('this chat already cancel, chat_id: {}, cancel chat_id: {}'.format(self.chat_id,
                                                                                               self.cancel_chat_id))
                return

            if stream:
                ## 流式对话
                # reponse = self.chat.get_response_stream(text)

                reponse = self.chat.client.chat.completions.create(
                    model=self.chat.model,
                    messages=self.chat.get_messages(),
                    temperature=self.chat.temperature,
                    stream=False,
                    )
                # logger.error(f"Chatresponse chat: {response}")
                result = {}
                result['seq'] = -1
                completionMessage = reponse.choices[0].message
                # print(completionMessage.content)
                result['text'] = completionMessage.content
                reponse = result

            for chunk in reponse:
                answer_msg = self.chat.decode_chunk(chunk)
                if answer_msg is not None:
                    logger.info("{:2} {}".format(answer_msg['seq'], answer_msg['text']))
                    self.auto_send(self.create_answer_msg(answer_msg, self.chat_id))
            else:
                answer_msg = self.chat.get_response(text)
                logger.info("{:2} {}".format(answer_msg['seq'], answer_msg['text']))
                self.auto_send(self.create_answer_msg(answer_msg, self.chat_id))

    def launch(self):
        """循环任务
        """
        ## 启动rabitmq transport线程
        self.transport_start()

        while not self.node_exit:
            sleep(0.001)
            # self.keyboard_control()
            ## 读取rabitmq数据
            mq_msg = self.auto_read()
            if mq_msg is not None:
                self.handle_mq_msg(mq_msg)


def main(config: dict):
    """入口函数
    """
    chat_node = ChatNode(config)
    chat_node.launch()


if __name__ == '__main__':
    """APP入口
    """
    logger.info('chat node start...')

    # 读取配置文件
    if len(sys.argv) < 2:
        logger.error('useage: config_file')
        exit(0)

    config_file = sys.argv[1]
    logger.info('config: %s', config_file)

    with open(config_file, 'r', encoding='utf-8') as load_f:
        config = json.load(load_f)
        logger.info(config)
        main(config)