# -*- coding: utf-8 -*-
from llm_api import get_respone
import jieba.analyse as aly
from collections import Counter
import os
import shutil
import gradio as gr
from project_database import Porject_DataBase,database_namelist,database_list
from pdf_convert import*

# 生成报告
'''
input3:上传
input2:prompt list
'''
# 生成报告函数修改
# 修改报告生成函数，移除生成过程的输出
def function_report_generation(name, input3, input2):
    global database_list, database_namelist

    database = database_list[database_namelist.index(name)]  # 选择对应的数据库

    # 只保留最终报告结果
    result = []

    all_report = ""
    for p_n, group in database.prompt_data.groupby("段落"):
        p_n_content = []  # 每段的内容

        for question in group["prompt"]:
            search_result = database.search(question, 1)
            search_result = "\n".join(search_result)

            prompt = f"请根据已知内容简洁明了的回复用户的问题，\
            已知内容如下：```{search_result}```,\
            用户的问题是：{question},你的回复接下来将被用于生成专业的法律报告"

            # 调用大模型API
            response = get_respone(prompt)
            
            content = ""
            for trunk in response:
                content += trunk.choices[0].delta.content

            content = content.replace("\n", " ")
            p_n_content.append(content)

        prompt_report = f"你是一个大学教授，你需要根据相关内容书写专业的法律报告，生成的内容必须严格来自相关内容，语言必须严谨、符合事实，\
        并且不能使用第一人称，相关内容如下：\n```{''.join(p_n_content)}"
        
        # 为每段报告添加标题
        result.append(f"## 第{p_n}段报告\n\n")
        
        # 获取大模型响应
        response = get_respone(prompt_report)
        
        for trunk in response:
            result[-1] += trunk.choices[0].delta.content
            # 只返回最终报告
            yield "\n\n".join(result)

        all_report += result[-1] + "\n\n"

# 知识库回答
# text:提问的prompt
# 知识库问答函数修改
def function_QA(name, text, model_name="deepseek-v3"):
    global database_list, database_namelist
    database = database_list[database_namelist.index(name)]

    result = ["## 回答\n\n"]

    search_result, image_paths = database.search(text, 2, search_img=True)  # 返回检索到的文本
    search_result = "\n".join(search_result)  # 将结果拼接,用空格分割开

    prompt = f"请你在不违背已知内容的前提下尽可能多的回答用户的问题，已知内容如下:```{search_result}```, \
    用户的问题是：{text}，\
    如果已知内容无法回答用户的问题请你来回答内容要详尽"

    response = get_respone(prompt, model_name)  # 一个特定的类型,并不直接是文本

    for trunk in response:
        if trunk.choices[0].delta.content is not None:  # 添加对 None 值的检查
            result[-1] += trunk.choices[0].delta.content
            yield "\n".join(result), image_paths
    
    # 如果有检索到的内容，添加来源信息
    if search_result.strip():
        result.append("\n\n### 相关来源\n")
        result.append("- 来自知识库的检索结果")
        
    yield "\n".join(result), image_paths
    
    
    # return  None, image_paths

# 切换知识库
def database_change(name):
    global database_list,database_namelist

    return database_list[database_namelist.index(name)].prompt_data

# retrieve high-frequency words
def get_type_name(files):
    content = []
    for file in files:
        try:
            with open(file.name,encoding="utf-8") as f:
                data = f.readlines(1)
                content.extend(aly.tfidf(data[0]))
        except:
            continue
    count = Counter(content)
    kw = count.most_common(2)

    return "".join([i[0] for i in kw])  # return the top2 frequency words

def upload(files, input_database_select_report):  # files will be stored in a temporary space on the computer
    global database_list,database_namelist
    # 初始化标志变量
    check_txt = False
    check_pdf = False
    check_prompt_xlsx = False

    # 遍历文件列表
    for file in files:
        if file.name.endswith(".txt"):
            check_txt = True
        elif file.name.endswith(".xlsx"):
            check_prompt_xlsx = True
        elif file.name.endswith(".pdf"):
            check_pdf = True

        # 提前终止条件判断：当 xlsx 文件存在且 txt 或 pdf 文件至少有一个存在时，停止遍历
        if check_prompt_xlsx and (check_txt or check_pdf):
            break

    # 合法性检查
    if not check_prompt_xlsx:
        raise Exception("请上传包含 prompt.xlsx 文件的文件夹")
    if not (check_txt or check_pdf):
        raise Exception("请上传包含 .txt 或 .pdf 文档的文件夹")
    

    #----------------------处理上传的文件夹--------------------------#
    # create dir according to the database uploading
    #type_name = get_type_name(files)
    type_name = "未成年人保护法"
    save_path = os.path.join("..", "new_upload" ,type_name)
    txt_dir = os.path.join(save_path, "txt")
    # 递归创建目录，如果目录已存在不会抛出异常
    os.makedirs(txt_dir, exist_ok=True)


    # Save the file to a specified folder
    for file in files:
        if file.name.endswith(".txt"):
            shutil.copy(file.name, txt_dir)
        elif file.name.endswith(".xlsx"):
            shutil.copy(file.name,save_path)
        elif file.name.endswith(".pdf"): # pdf转换为图像和.txt
            os.makedirs(os.path.join(save_path, "image"), exist_ok = True)
            pdf_converter = PdfConverter(file, txt_dir, os.path.join(save_path, "image"))
            md_save_dir, every_img_dir, _ = pdf_converter.convert()


    # create database
    database = Porject_DataBase(save_path, type_name)
    database_list.append(database)
    database_namelist.append(type_name)

    update_input_database_select_report = gr.Dropdown(choices=database_namelist, 
                                                      value=database_namelist[-1])
    update_input_database_select_QA = gr.Dropdown(choices=database_namelist, 
                                                  value=database_namelist[-1])
    
    '''
    更新上传知识库的菜单, 以及prompt
    更新知识库问答的菜单选项
    '''
    return (update_input_database_select_report, 
            database.prompt_data, 
            update_input_database_select_QA
            )


