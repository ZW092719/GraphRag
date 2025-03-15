# -*- coding: utf-8 -*-
from embdatabase_milvus import *
from embdatabase_faiss import *
import pandas as pd
from config import *


class Porject_DataBase():
    def __init__(self, path, name=None, img_path=None):
        global database_type
        if name is None:
            name = path

        if os.path.exists(os.path.join(path,"txt"))  == False:
            print(f"知识库{name}txt文件夹不存在,可能是不完整的知识库")
            exit(-999)
        if os.path.exists(os.path.join(path,"prompt.xlsx"))  == False:
            print(f"知识库{name}的prompt文件不存在,可能是不完整的知识库")
            exit(-998)
        if os.path.exists(os.path.join("..",".cache")) == False:
            os.mkdir(os.path.join("..",".cache"))

        # 提问数据
        self.prompt_data = pd.read_excel(os.path.join(path,"prompt.xlsx"),engine="openpyxl")

        # 其包含的contents为分块后的txt
        self.document = Document(os.path.join(path,"txt"),name)

        # 向量化后的数据库
        if database_type == "Milvus":
            self.emb_database = EmbDataBase_Milvus(os.path.join("..","CLIP_model", "clip_cn_vit-b-16.pt"), 
                                                   self.document.contents,name)
        elif database_type == "Faiss":
            self.emb_database = EmbDataBase_Faiss(os.path.join("..","CLIP_model", "clip_cn_vit-b-16.pt"), 
                                                  self.document.contents, name, img_path)
        else: # default : faiss
            self.emb_database = EmbDataBase_Faiss(os.path.join("..","moka-ai_m3e-base"), self.document.contents, name)

    def search(self,text,topn=3, search_img=False):
        return self.emb_database.search(text,topn, search_img)


# ------------------------------ DataBase load ---------------------------------------#
def load_database(dir_path=os.path.join("..","database_dir")):
    dirs = [name for name in os.listdir(dir_path) if os.path.isdir(f"{dir_path}/{name}")]

    for dir in dirs:
        text_path = os.path.join(dir_path, dir)
        img_path = os.path.join(text_path, "image")
        database = Porject_DataBase(text_path, dir, img_path)
        database_list.append(database)
        database_namelist.append(dir)
        print(f"知识库{database_namelist[-1]}加载完成! ! !")

    return database_list, database_namelist