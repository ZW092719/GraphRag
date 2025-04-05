# -*- coding: utf-8 -*-
import os
import pickle

import faiss
from pypinyin import lazy_pinyin
from document_emb import *
from sklearn.metrics.pairwise import cosine_similarity

# covert name to pinyin for Milvus can't use Chinese Character
def cover_name(name):
    return "_".join(lazy_pinyin(name))

# emb database(faiss & local)
# emb_model_dir: 文本向量模型路径

class EmbDataBase_Faiss():
    def __init__(self, emb_model_dir, contents, name, 
                 img_dir = None, recreate_database=False):
        global milvs_client
        self.img_dir = img_dir
        self.emb_model = EmbModel(emb_model_dir) # 包含clip的model和图像预处理preprocess
        self.embedding_dim = self.emb_model.model.visual.output_dim
        self.txt_path = os.path.join("..",".cache",f"{name}_faiss_txt_index.faiss")
        self.img_path = os.path.join("..",".cache",f"{name}_faiss_img_index.faiss")
        # 文本数据库
        if (recreate_database) or (os.path.exists(self.txt_path) == False):
            if os.path.exists(self.txt_path) :
                os.remove(self.txt_path)
            txt_index = faiss.IndexFlatL2(self.embedding_dim)
            text_embs = self.emb_model.text_to_emb(contents) # 变为embedding
            txt_index.add(text_embs)
            faiss.write_index(txt_index, self.txt_path)
        else:
            txt_index = faiss.read_index(self.txt_path)
        self.txt_index = txt_index # 文本数据库
        self.contents = contents # 分块之后的txt信息
        self.adjacency_matrix = self.build_adjacency_matrix()

        if img_dir is not None and os.path.exists(img_dir):
            if (recreate_database) or (os.path.exists(self.img_path) == False):
                if os.path.exists(self.img_path):
                    os.remove(self.img_path)
                img_index = faiss.IndexFlatL2(self.embedding_dim)
                image_features = self.emb_model.img_to_emb(img_dir) # 变为embedding
                img_index.add(image_features)
                faiss.write_index(img_index, self.img_path)
            else:
                img_index = faiss.read_index(self.img_path)
            
            self.img_list =  [os.path.join(img_dir,img) for img in os.listdir(img_dir)] # 所有图像的路径
            self.img_index = img_index

         

    def build_adjacency_matrix(self):
        """
        构建文本之间的邻接矩阵，矩阵中的元素是文本之间的相似度
        """
        # 获取文本的嵌入向量
        text_embs = self.emb_model.text_to_emb(self.contents)
        similarity_matrix = cosine_similarity(text_embs)
        return similarity_matrix
    

    def search(self,content,topn=2, search_img=False):
        # 判断是否为字符串
        if isinstance(content,str):
            content = self.emb_model.text_to_emb(content) # 拿到文本变为的embbeding

        # 距离最近的3个结果
        dis, idx = self.txt_index.search(content,topn) # 拿到距离与索引  #milvus
        results = [self.contents[i] for i in idx[0]] # 根据索引返回内容
        results_img = []
        if search_img and os.path.exists(self.img_dir):
            dis_img, idx_img = self.img_index.search(content,topn) # 拿到距离与索引  #milvus
            results_img = [self.img_list[i] for i in idx_img[0]] # 根据索引返回内容
        
        if results_img:
            return results, results_img
        return results

    # def image_search(self, image_path, texts, image_paths, topk):
    #     try:
    #         image = self.emb_model.preprocess(Image.open(image_path)).unsqueeze(0).to("cpu")
    #         with torch.no_grad():
    #             img_feature = self.emb_model.encode_image(image).cpu().numpy()
    #         # 在图像库中查询
    #         image_distances, image_indices = self.image_index.search(img_feature, topk)
    #         similar_images = []
    #         for i in range(topk):
    #             similar_images.append((image_paths[image_indices[0][i]], image_distances[0][i]))

    #         return similar_images
    #     except Exception as e:
    #         print(f"Error processing image {image_path}: {e}")
    #         return [], []



