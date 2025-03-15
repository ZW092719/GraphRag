# -*- coding: utf-8 -*-
from document_emb import *
from pypinyin import lazy_pinyin
from pymilvus import CollectionSchema,FieldSchema,DataType
from tqdm import tqdm
from pymilvus import MilvusClient


def Milvus_Client():
    client =  MilvusClient(uri='http://localhost:19530')   # set your own address
    return client
# covert name to pinyin for Milvus can't use Chinese Character
def cover_name(name):
    return "_".join(lazy_pinyin(name))

# emb database (milvus)
class EmbDataBase_Milvus():
    def __init__(self,emb_model_dir,contents,name,recreate_database=False):
        self.milvs_client = Milvus_Client()
        self.emb_model = EmbModel(emb_model_dir)
        self.name = cover_name(name)

        if recreate_database == True:      # should delete database when recreate database
            if self.milvs_client.has_collection(self.name):
                self.milvs_client.drop_collection(self.name)
        else:
            if self.milvs_client.has_collection(self.name) == False:
                schema = CollectionSchema([
                    FieldSchema("id",DataType.INT64,is_primary=True),
                    FieldSchema("text",DataType.VARCHAR,max_length=2000),
                    FieldSchema("emb", DataType.FLOAT_VECTOR,
                                dim=self.emb_model.model.get_sentence_embedding_dimension())
                ])

                index_params = self.milvs_client.prepare_index_params()
                index_params.add_index(
                    field_name="emb",
                    metric_type="COSINE",
                    index_type="",
                    index_name="vector_index"
                )

                self.milvs_client.create_collection(collection_name=self.name,schema=schema)
                self.milvs_client.create_index(self.name,index_params)

                for idx,content in tqdm(enumerate(contents),total=len(contents),desc=f"构建{name}向量库中..."):
                    emb = self.emb_model.to_emb(content)[0]
                    self.milvs_client.insert(self.name,{"id":idx,"text":content[:2000],"emb":emb})

                # load should be done before search
                self.milvs_client.load_collection(self.name)

    def search(self,content,topn=3):
        if isinstance(content,str):
            content = self.emb_model.to_emb(content)

        result = self.milvs_client.search(self.name,content,output_fields=["text"],limit=topn)
        _,_,t = zip(*[ (d["id"],d["distance"],d["entity"]["text"]) for d in result[0] ])

        return "".join(t)







