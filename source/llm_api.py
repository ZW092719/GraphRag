# -*- coding: utf-8 -*-
import openai
from openai import OpenAI

# 获取答案的函数
def get_ans(prompt):
    openai.api_key = "your-api-key"  # 请使用你自己的 API Key

    response = openai.Completion.create(
        model="gpt-4",  # 你可以选择适合的模型，gpt-4 或 gpt-3.5
        prompt=prompt,
        max_tokens=1024,
        temperature=0.45,
        top_p=0.3,
        stream=False  # stream 设置为 False 以一次性获取完整的答案
    )

    return response.choices[0].text.strip()  # 返回生成的文本并去除多余的空格

# 获取响应的函数
def get_respone(prompt):
    api_key = "c7219f76321b1818e9c0df788868adcd81ec2a51"  # https://aistudio.baidu.com/account/accessToken
    client = OpenAI(
        api_key=api_key,
        base_url="https://aistudio.baidu.com/llm/lmapi/v3" # 星河社区大模型API服务的BaseURL
    )
    # 准备消息格式
    messages = [{"role": "user", "content": prompt}]
    
    # 调用接口生成响应
    response = client.chat.completions.create(
        model="ernie-4.0-turbo-128k",  # 选择模型
        messages=messages,  # 使用messages而非prompt
        max_tokens=1024,
        temperature=0.45,
        top_p=0.3,
        stream=True  # 设置stream参数为True以逐步接收响应
    )
    return response  # 返回整个响应对象，可以进一步处理
