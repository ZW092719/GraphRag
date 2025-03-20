import os
import gradio as gr
import threading
import http.server
import socketserver
import sqlite3  # 用于存储用户信息
from project_database import *
from ui_backend import *
from config import *
from utils import get_available_graph_html_files, update_graph_html, update_button_text,toggle_fullscreen
# ==== 1️⃣ 启动 HTTP 服务器，确保 graph.html 可访问 ====
PORT = 8000

def start_http_server():
    os.chdir(os.path.dirname(os.path.abspath("法律.html")))
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        httpd.serve_forever()

threading.Thread(target=start_http_server, daemon=True).start()

# ==== 2️⃣ 连接数据库，初始化用户表 ====

# ==== 3️⃣ 加载知识库 ====
database_list, database_namelist = load_database()

# ==== 自定义高级主题 ====
# ==== 自定义高级主题 ====
custom_css = """
body {
    background: linear-gradient(to right, #e0f7fa, #b2ebf2, #80deea) !important;
    background-attachment: fixed !important;
    color: #004d40 !important;
}

.dark body {
    background: linear-gradient(to right, #004d40, #00695c, #00796b) !important;
    background-attachment: fixed !important;
    color: #e0f7fa !important;
}

.contain {
    max-width: 1600px !important;
}

.tabs > .tab-nav > button {
    color: #004d40 !important;
}

.tabs > .tab-nav > button.selected {
    border-bottom: 2px solid #00796b !important;
}

button.primary {
    background-color: #00796b !important;
    color: #e0f7fa !important;
}

button.primary:hover {
    background-color: #004d40 !important;
    transform: translateY(-2px);
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
}

button {
    transition: all 0.2s ease-in-out !important;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2) !important;
}

.block {
    background: rgba(255, 255, 255, 0.8) !important;
    border-width: 0px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2) !important;
}

.block .label-wrap .block-label {
    color: #004d40 !important;
}

input, textarea, select {
    background-color: rgba(255, 255, 255, 0.9) !important;
    border-color: rgba(0, 77, 64, 0.1) !important;
    color: #004d40 !important;
}

.prose {
    color: #004d40 !important;
}

/* 添加微妙的图案背景 */
body:before {
    content: "";
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-image: url('https://i.imgur.com/4qVfSnf.png');
    background-repeat: repeat;
    background-size: 200px;
    opacity: 0.05;
    pointer-events: none;
    z-index: -1;
}
"""


my_theme = gr.Theme.from_hub("allenai/gradio-theme")
# ==== 5️⃣ Gradio 登录 + 主界面 ====
with gr.Blocks(css=".gradio-container {background: url('file=../test.jpg')}",
               theme=my_theme) as demo:

    # ✅ 主界面（初始时隐藏）
    with gr.Blocks(visible=False) as main_page:
        gr.Markdown("## 🚀 GraphRAG")
        
        with gr.Row():
            # 左侧侧边栏
            with gr.Column(scale=1, min_width=200):
                with gr.Tabs():
                    with gr.Tab("📄 报告生成"):
                        with gr.Row():
                            input_database_select_report = gr.Dropdown(
                                choices=database_namelist, 
                                label="知识库选择", 
                                value=database_namelist[0]
                            )
                            input_uploadbtn = gr.UploadButton("📂 上传知识库", 
                                                              file_types=[".txt", ".csv", ".json", ".pdf"], 
                                                              file_count="directory")

                        input_prompt = gr.DataFrame(
                            database_list[0].prompt_data, 
                            max_height=400
                        )

                        submit_btn = gr.Button("⚡ 生成报告")

                        with gr.Accordion("📜 生成结果"):
                            output_report = gr.Markdown(label="报告生成内容")

                        submit_btn.click(function_report_generation, 
                                         [input_database_select_report, input_prompt], 
                                         [output_report])
                        input_database_select_report.change(database_change, 
                                                            [input_database_select_report], 
                                                            [input_prompt])
                        input_uploadbtn.upload(upload, 
                                               [input_uploadbtn, input_database_select_report], 
                                               [input_database_select_report, input_prompt])

                    with gr.Tab("💡 知识库问答"):
                        input_database_select_QA = gr.Dropdown(
                            choices=database_namelist, 
                            label="知识库选择", 
                            value=database_namelist[0]
                        )
                        input_question = gr.Textbox(label="请输入您的问题")
                        submit_qa_btn = gr.Button("🔍 生成回答")

                        with gr.Accordion("📢 回答"):
                            output_answer = gr.Markdown(label="回答")
                            output_images = gr.Gallery(label="相关图片", columns=[3], height=300)

                        submit_qa_btn.click(function_QA, 
                                            [input_database_select_QA, input_question], 
                                            [output_answer, output_images])

                    with gr.Tab("🌐 Graph 可视化"):
                        gr.Markdown("### 交互式知识图谱展示")
                        available_html_files = get_available_graph_html_files()
                        with gr.Row():
                            graph_selector = gr.Dropdown(
                                choices=available_html_files,
                                label="选择知识图谱文件",
                                value=available_html_files[0] if available_html_files else "graph.html",
                                scale=3
                            )
                        fullscreen_btn = gr.Button("📺 全屏显示", scale=1)
                        is_fullscreen = gr.State(False)
                        graph_display = gr.HTML(
                            update_graph_html(available_html_files[0] if available_html_files else "graph.html"),
                            label="Graph Visualization",
                            elem_id="graph_display"
                        )
                        graph_selector.change(
                            fn=update_graph_html,
                            inputs=[graph_selector, is_fullscreen],
                            outputs=graph_display
                        )
                        fullscreen_btn.click(
                            fn=toggle_fullscreen,
                            inputs=[graph_selector, is_fullscreen],
                            outputs=[graph_display, is_fullscreen],
                            api_name="toggle_fullscreen"
                        ).then(
                            fn=update_button_text,
                            inputs=[is_fullscreen],
                            outputs=[fullscreen_btn]
                        )

demo.launch(server_name="127.0.0.1", 
            server_port=9909, 
            show_api=False, 
            allowed_paths=["D:\LLM\QBTech_RAG_Demo"]
            )
