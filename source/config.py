import gradio as gr
# ------------------------------ parameters setting ----------------------------------#
# database type : Faiss or Milvus
database_type = "Faiss"
# database_type = "Milvus"

# ------------------------------ global pramaters ----------------------------------#
database_list = []
database_namelist = []
# input_database_select_report = gr.Dropdown(choices=database_namelist, label="知识库选择", value=database_namelist[0])

