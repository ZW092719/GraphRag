# -*- coding: utf-8 -*-
import openai
from openai import OpenAI

# ��ȡ�𰸵ĺ���
def get_ans(prompt):
    openai.api_key = "your-api-key"  # ��ʹ�����Լ��� API Key

    response = openai.Completion.create(
        model="gpt-4",  # �����ѡ���ʺϵ�ģ�ͣ�gpt-4 �� gpt-3.5
        prompt=prompt,
        max_tokens=1024,
        temperature=0.45,
        top_p=0.3,
        stream=False  # stream ����Ϊ False ��һ���Ի�ȡ�����Ĵ�
    )

    return response.choices[0].text.strip()  # �������ɵ��ı���ȥ������Ŀո�

# ��ȡ��Ӧ�ĺ���
def get_respone(prompt):
    api_key = "c7219f76321b1818e9c0df788868adcd81ec2a51"  # https://aistudio.baidu.com/account/accessToken
    client = OpenAI(
        api_key=api_key,
        base_url="https://aistudio.baidu.com/llm/lmapi/v3" # �Ǻ�������ģ��API�����BaseURL
    )
    # ׼����Ϣ��ʽ
    messages = [{"role": "user", "content": prompt}]
    
    # ���ýӿ�������Ӧ
    response = client.chat.completions.create(
        model="ernie-4.0-turbo-128k",  # ѡ��ģ��
        messages=messages,  # ʹ��messages����prompt
        max_tokens=1024,
        temperature=0.45,
        top_p=0.3,
        stream=True  # ����stream����ΪTrue���𲽽�����Ӧ
    )
    return response  # ����������Ӧ���󣬿��Խ�һ������
