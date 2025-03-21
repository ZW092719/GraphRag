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

/* 自定义侧边栏样式 */
.sidebar-menu {
    padding: 0 !important;
    margin: 0 !important;
    border-right: 1px solid rgba(0, 77, 64, 0.2);
    height: 100%;
}

.sidebar-menu .gr-button {
    border-radius: 0 !important;
    text-align: left !important;
    padding: 12px 15px !important;
    margin: 0 !important;
    border: none !important;
    border-bottom: 1px solid rgba(0, 77, 64, 0.1) !important;
    background: transparent !important;
    transition: background 0.2s ease-in-out !important;
}

.sidebar-menu .gr-button:hover {
    background: rgba(0, 77, 64, 0.1) !important;
}

.sidebar-menu .gr-button.selected {
    background: rgba(0, 77, 64, 0.2) !important;
    border-left: 4px solid #00796b !important;
}
"""


my_theme = gr.Theme.from_hub("shivi/calm_seafoam")
# ==== 5️⃣ Gradio 登录 + 主界面 ====
with gr.Blocks(css="""
    .gradio-container {background: url('file=../test.jpg')}
    
    /* 整体布局调整 */
    .app-container {
        display: flex !important;
        width: 100% !important;
        min-height: 100vh !important;
        position: relative !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* 侧边栏样式 */
    .sidebar {
        width: 220px !important;
        min-width: 220px !important;
        max-width: 220px !important;
        background-color: rgba(240, 240, 240, 0.9) !important;
        border-right: 1px solid rgba(0, 0, 0, 0.1) !important;
        box-shadow: 2px 0 5px rgba(0, 0, 0, 0.1) !important;
        height: 100% !important;
        position: fixed !important;
        left: 0 !important;
        top: 0 !important;
        z-index: 100 !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    
    /* 侧边栏按钮样式 */
    .sidebar button {
        width: 100% !important;
        text-align: left !important;
        padding: 15px 20px !important;
        border: none !important;
        border-radius: 0 !important;
        background: transparent !important;
        border-bottom: 1px solid rgba(0, 0, 0, 0.05) !important;
        transition: all 0.2s ease !important;
        font-size: 15px !important;
        color: #333 !important;
    }
    
    .sidebar button:hover {
        background-color: rgba(0, 0, 0, 0.05) !important;
    }
    
    .sidebar button.selected {
        background-color: rgba(0, 0, 0, 0.1) !important;
        border-left: 4px solid #00796b !important;
        font-weight: bold !important;
    }
    
    /* 主内容区域样式 */
    .main-content-wrapper {
        margin-left: 220px !important;
        flex: 1 !important;
        padding: 20px !important;
        width: calc(100% - 220px) !important;
    }
    
    /* 标题样式 */
    .main-title {
        margin-bottom: 20px !important;
    }
    
    /* 确保功能面板正常显示 */
    .function-panel {
        width: 100% !important;
        padding: 15px !important;
        background: rgba(255, 255, 255, 0.8) !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1) !important;
    }
""", theme=my_theme) as demo:

    # ✅ 主界面（初始时隐藏）
    with gr.Blocks(visible=False) as main_page:
        with gr.Row(elem_classes="app-container"):
            # 左侧侧边栏 - 功能选择
            with gr.Column(elem_classes="sidebar"):
                # 使用按钮组来代替Radio
                feature_btns = []
                report_btn = gr.Button("📄 报告生成", elem_classes=["sidebar-btn", "selected"])
                qa_btn = gr.Button("💡 知识库问答", elem_classes=["sidebar-btn"])
                graph_btn = gr.Button("🌐 Graph 可视化", elem_classes=["sidebar-btn"])
                feature_btns.extend([report_btn, qa_btn, graph_btn])
            
            # 右侧主内容区
            with gr.Column(elem_classes="main-content-wrapper"):
                gr.Markdown("## 🚀 GraphRAG", elem_classes="main-title")
                
                # 报告生成界面
                with gr.Group(visible=True, elem_classes="function-panel") as report_generation_panel:
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

                # 知识库问答界面
                with gr.Group(visible=False, elem_classes="function-panel") as qa_panel:
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

                # Graph 可视化界面
                with gr.Group(visible=False, elem_classes="function-panel") as graph_panel:
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

        # 功能切换逻辑
        def show_panel(panel_name):
            if panel_name == "report":
                return (gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), 
                        gr.update(elem_classes=["sidebar-btn", "selected"]), 
                        gr.update(elem_classes=["sidebar-btn"]), 
                        gr.update(elem_classes=["sidebar-btn"]))
            elif panel_name == "qa":
                return (gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), 
                        gr.update(elem_classes=["sidebar-btn"]), 
                        gr.update(elem_classes=["sidebar-btn", "selected"]), 
                        gr.update(elem_classes=["sidebar-btn"]))
            else:  # "graph"
                return (gr.update(visible=False), gr.update(visible=False), gr.update(visible=True), 
                        gr.update(elem_classes=["sidebar-btn"]), 
                        gr.update(elem_classes=["sidebar-btn"]), 
                        gr.update(elem_classes=["sidebar-btn", "selected"]))
            
        report_btn.click(
            fn=lambda: show_panel("report"),
            inputs=[],
            outputs=[report_generation_panel, qa_panel, graph_panel, 
                     report_btn, qa_btn, graph_btn]
        )
        
        qa_btn.click(
            fn=lambda: show_panel("qa"),
            inputs=[],
            outputs=[report_generation_panel, qa_panel, graph_panel, 
                     report_btn, qa_btn, graph_btn]
        )
        
        graph_btn.click(
            fn=lambda: show_panel("graph"),
            inputs=[],
            outputs=[report_generation_panel, qa_panel, graph_panel, 
                     report_btn, qa_btn, graph_btn]
        )

        # 功能事件处理
        submit_btn.click(function_report_generation, 
                         [input_database_select_report, input_prompt], 
                         [output_report])
        input_database_select_report.change(database_change, 
                                            [input_database_select_report], 
                                            [input_prompt])
        input_uploadbtn.upload(upload, 
                               [input_uploadbtn, input_database_select_report], 
                               [input_database_select_report, input_prompt])
        submit_qa_btn.click(function_QA, 
                            [input_database_select_QA, input_question], 
                            [output_answer, output_images])
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
