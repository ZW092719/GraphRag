# -*- coding: utf-8 -*-
#from sentence_transformers import SentenceTransformer
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader
import pickle
import os
import cn_clip.clip as clip
from cn_clip.clip import load_from_name, available_models
import torch
import PIL.Image as Image
import numpy as np

# 两个功能
# 对txt文档分块
# 对分块文档向量化

# document processing
class Document():
    def __init__(self,dir,name):
        # contents persistence
        if os.path.exists(os.path.join("..",".cache",f"{name}_contents.pkl")) == False:
            loader = DirectoryLoader(dir,show_progress=True) 
            documents = loader.load() # 读取所有txt
            # 对txt文本进行分割,并保存为.pkl文件
            text_spliter = CharacterTextSplitter(chunk_size=300,chunk_overlap=50)

            split_docs = text_spliter.split_documents(documents)
            contents = [i.page_content for i in split_docs]

            with open(os.path.join("..",".cache",f"{name}_contents.pkl"),"wb") as f:
                pickle.dump(contents,f)

        else: # 为了不每次进行txt文本的分割所以选择使用pickle保存文件
            with open(os.path.join("..",".cache",f"{name}_contents.pkl"),"rb") as f:
                contents = pickle.load(f)
        self.contents = contents

# to emb

# # emb_model_dir: 文本向量模型路径

class EmbModel():
    def __init__(self,emb_model_dir):
        #self.model = SentenceTransformer(emb_model_dir)
        self.model, self.preprocess = load_from_name("ViT-B-16", # preprocess图像预处理
                                                     device="cpu", 
                                                     download_root='../CLIP_model')

    def text_to_emb(self, sentence):
        if isinstance(sentence,str):
            sentence = [sentence]
        
        with torch.no_grad():
            sentence = clip.tokenize(sentence).to("cpu")
            sentence_features = self.model.encode_text(sentence)
            sentence_features /= sentence_features.norm(dim=-1, keepdim=True)

        print("文本已转换为向量!")
        return sentence_features.cpu().numpy() # 转换为向量
    

    def img_to_emb(self, image_paths, device="cpu"):
        if isinstance(image_paths, str):
            all_img = os.listdir(image_paths)
            image_paths = [os.path.join(image_paths,img) for img in all_img]
        image_features = []
        for image_path in image_paths:
            try:
                image = self.preprocess(Image.open(image_path)).unsqueeze(0).to(device)
                with torch.no_grad():
                    img_feature = self.model.encode_image(image)
                    img_feature /= img_feature.norm(dim=-1, keepdim=True)
                    image_features.append(img_feature.cpu().numpy())
            except Exception as e:
                print(f"Error processing image {image_path}: {e}")
        image_features = np.concatenate(image_features, axis=0)
        return image_features







