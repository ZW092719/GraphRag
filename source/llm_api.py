# -*- coding: utf-8 -*-
import openai
from openai import OpenAI

# 定义可用的模型列表
AVAILABLE_MODELS = {
    "gpt-4": "gpt-4",
    "qwen-vl-max": "qwen-vl-max",
    "deepseek-r1": "deepseek-r1",
    "deepseek-v3": "deepseek-v3"
}

# 获取响应的函数
def get_respone(prompt, model_name="deepseek-v3"):
    api_key = "sk-NfZOYht4PAks38kosNZhcgvTfEs7692oKf1rjIpE2gklEjiJ"  # https://aistudio.baidu.com/account/accessToken
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.agicto.cn/v1" # 星河社区大模型API服务的BaseURL
    )
    # 准备消息格式
    messages = [{"role": "user", "content": prompt}]
    
    # 调用接口生成响应
    response = client.chat.completions.create(
        model=AVAILABLE_MODELS.get(model_name, "deepseek-v3"),  # 选择模型，如果模型不存在则使用默认模型
        messages=messages,  # 使用messages而非prompt
        max_tokens=1024,
        temperature=0.45,
        top_p=0.3,
        stream=True  # 设置stream参数为True以逐步接收响应
    )
    return response  
