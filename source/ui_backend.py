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
def function_report_generation(name,input3,input2):
    global database_list,database_namelist

    database = database_list[database_namelist.index(name)] # 选择对应的数据库

    result1 = []
    result2 = []

    result1.append("内容解析中......")

    yield "\n".join(result1), "\n".join(result2)

    all_report = ""
    for p_n, group in database.prompt_data.groupby("段落"):
        result1.append(f"第{p_n}段内容生成中......")
        yield "\n".join(result1), "\n".join(result2)
        p_n_content = [] # 每段的内容

        for question in group["prompt"]:
            #Project_database的search--->embdatabase的search
            search_result = database.search(question, 1) # 设置找到最近似的1个内容

            # print("向量库检索内容：", search_result)
            search_result = "\n".join(search_result)

            prompt = f"请根据已知内容简洁明了的回复用户的问题，已知内容如下：```{search_result}```,用户的问题是：{question}，如果已知内容无法回答用户的问题，无需输出其他内容" #请直接回复：不知道，无需输出其他内容"

            # generate word one by one
            response = get_respone(prompt) # 调用大模型api
            result1.append("大模型检索及回答内容:\n")

            for trunk in response:
                result1[-1] += trunk.choices[0].delta.content # 逐个添加回复
                yield "\n".join(result1), "\n".join(result2)

            result1[-1] = result1[-1].replace("\n", "")
            p_n_content.append(result1[-1])

            # result1.append(f"大模型检索及回答内容：{result1[-1] }")
            yield "\n".join(result1), "\n".join(result2)

        prompt_report = f"你是一个大学教授，你需要根据相关内容，来写一段内容，生成的内容必须严格来自相关内容，语言必须严谨、符合事实，并且不能使用第一人称，相关内容如下：\n```{''.join(p_n_content)}"
        result1.append(f"第{p_n}段报告内容：\n")
        result2.append(f"\t\t\t")
        yield "\n".join(result1), "\n".join(result2)

        response = get_respone(prompt_report)

        for trunk in response:
            result1[-1] += trunk.choices[0].delta.content  # 每次添加在末尾
            result2[-1] += trunk.choices[0].delta.content  # 每次添加在末尾

            result1[-1] = result1[-1].replace("\n", "")
            result2[-1] = result2[-1].replace("\n", "")
            yield "\n".join(result1), "\n".join(result2)

        all_report += ("    " + "".join(result2[-1]))
        all_report += "\n"

        result1.append("*" * 30)

        yield "\n".join(result1), "\n".join(result2)

# 知识库回答
# text:提问的prompt
def function_QA(name,text):
    global database_list, database_namelist
    database = database_list[database_namelist.index(name)]

    result = [""]

    search_result, image_paths = database.search(text, 3, search_img=True) # 返回检索到的文本
    search_result = "\n".join(search_result) # 将结果拼接,用空格分割开

    prompt = f"请根据已知内容简洁明了的回复用户的问题，已知内容如下:```{search_result}```,用户的问题是：{text}，如果已知内容无法回答用户的问题，请直接回复：知识库无相关信息,请完善知识库!"

    response = get_respone(prompt) # 一个特定的类型,并不直接是文本

    for trunk in response:
        result[-1] += trunk.choices[0].delta.content
        yield "\n".join(result) , image_paths
    
    
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
    type_name = get_type_name(files)
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
            pdf_converter = PdfConverter(file, txt_dir, os.path.join(save_path, "img"))
            md_save_dir, every_img_dir = pdf_converter.convert()


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


