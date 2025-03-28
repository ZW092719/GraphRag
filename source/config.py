import gradio as gr
import os
# ------------------------------ parameters setting ----------------------------------#
# database type : Faiss or Milvus
database_type = "Faiss"
# database_type = "Milvus"

# ------------------------------ 图谱相关配置 ----------------------------------#
# 图谱HTML文件路径
GRAPH_HTML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "graph")
# 默认图谱文件名
DEFAULT_GRAPH_FILE = "graph.html"

# ------------------------------ global pramaters ----------------------------------#
database_list = []
database_namelist = []
# input_database_select_report = gr.Dropdown(choices=database_namelist, label="知识库选择", value=database_namelist[0])

