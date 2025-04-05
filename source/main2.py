import os
import threading
import numpy as np
import gradio as gr
import http.server
import socketserver
import sqlite3  # 用于存储用户信息
from project_database import *
from ui_backend import *
from config import *
from utils import get_available_graph_html_files, update_graph_html, update_button_text, toggle_fullscreen
import time

# ==== 1️⃣ 启动 HTTP 服务器，确保 graph.html 可访问 ====
PORT = 8080

# 在文件开头添加模型列表
AVAILABLE_MODELS = ["gpt-4", "qwen-vl-max", "deepseek-r1", "deepseek-v3"]

class SimpleHTTPRequestHandlerWithCORS(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        return super().end_headers()

def start_http_server():
    global PORT
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            # 使用当前工作目录
            handler = SimpleHTTPRequestHandlerWithCORS
            # 设置允许地址重用，解决端口重用问题
            socketserver.TCPServer.allow_reuse_address = True
            with socketserver.TCPServer(("", PORT), handler) as httpd:
                print(f"HTTP服务器已启动在端口 {PORT}")
                httpd.serve_forever()
            break  # 如果成功启动，跳出循环
        except OSError as e:
            if attempt < max_attempts - 1:  # 如果不是最后一次尝试
                print(f"端口 {PORT} 已被占用，尝试下一个端口")
                PORT += 1  # 尝试下一个端口
            else:
                print(f"HTTP服务器启动失败: {e}")

# 启动HTTP服务器线程
http_server_thread = threading.Thread(target=start_http_server, daemon=True)
http_server_thread.start()


# ==== 2️⃣ 加载知识库 ====
database_list, database_namelist = load_database()

# 创建测试图片
try:
    # 检查是否已存在测试图片
    if not os.path.exists("test.jpg"):
        from PIL import Image
        # 创建一个简单的渐变背景图片
        width, height = 1920, 1080
        array = np.zeros([height, width, 3], dtype=np.uint8)
        for i in range(height):
            for j in range(width):
                array[i, j, 0] = int(256 * i / height)  # 红色渐变
                array[i, j, 1] = int(256 * j / width)   # 绿色渐变
                array[i, j, 2] = 100                    # 固定蓝色值
        img = Image.fromarray(array)
        img.save("test.jpg")
        print("已创建测试背景图片")
except Exception as e:
    print(f"创建测试图片时出错: {e}")

# ==== 4️⃣ 复制必要的HTML文件到根目录以便HTTP服务器访问 ====
try:
    # 确保graph.html可以被HTTP服务器访问
    graph_file_source = os.path.join(GRAPH_HTML_PATH, DEFAULT_GRAPH_FILE)
    if os.path.exists(graph_file_source):
        import shutil
        shutil.copy2(graph_file_source, DEFAULT_GRAPH_FILE)
        print(f"已复制图谱文件到根目录: {DEFAULT_GRAPH_FILE}")
    
    # 确保logo.jpg可以被HTTP服务器访问
    if os.path.exists("logo.jpg"):
        import shutil
        # 将logo.jpg复制到当前工作目录（HTTP服务器的根目录）
        shutil.copy2("logo.jpg", os.path.join(os.getcwd(), "logo.jpg"))
        print(f"已复制Logo文件到根目录")
except Exception as e:
    print(f"复制文件时出错: {e}")

# ==== 5️⃣ Gradio 主界面 ====
with gr.Blocks(css_paths=["style.css"], theme="soft") as demo:

    # 定义应用界面
    with gr.Row(elem_classes="app-container"):
        # 左侧侧边栏 - 功能选择
        with gr.Column(elem_classes="sidebar"):
            # 添加标题到侧边栏顶部 - 使用HTML而非Markdown
            gr.HTML(f"""<div class="sidebar-title"><img src="http://127.0.0.1:{PORT}/logo.jpg" alt="智能法律助手" class="logo-image" style="max-width: 100%; max-height: 80px;"></div>""")
            
            # 使用按钮组来代替Radio
            feature_btns = []
            report_btn = gr.Button("📚 生成报告", elem_classes=["sidebar-btn", "selected"])
            qa_btn = gr.Button("⚖️ 智能问答", elem_classes=["sidebar-btn"])
            #contract_btn = gr.Button("💼 生成合同", elem_classes=["sidebar-btn"])
            graph_btn = gr.Button("📋 知识图谱", elem_classes=["sidebar-btn"])
            upload_btn = gr.Button("📤 上传知识库", elem_classes=["sidebar-btn"])
            feature_btns.extend([report_btn, qa_btn,  graph_btn, upload_btn]) # contract_btn  
            
        # 右侧主内容区
        with gr.Column(elem_classes="main-content-wrapper"):
            
            # 报告生成界面
            with gr.Group(visible=True, elem_classes="function-panel") as report_generation_panel:
                # 顶部标题和知识库选择
                with gr.Row():
                    # 标题
                    with gr.Column(scale=3):
                        gr.Markdown("""
                        ### 智能报告生成
                        请选择知识库和填写报告字段，系统将为您生成专业法律报告
                        """, elem_classes="panel-title")
                    # 知识库选择按钮
                    with gr.Column(scale=1):
                        report_kb_button = gr.Button("选择知识库 ▼", elem_classes="standard-button")
                
                # 知识库选择状态
                report_kb_panel_state = gr.State(False)
                
                # 浮动知识库选择面板 (默认隐藏)
                with gr.Column(visible=False, elem_classes="floating-kb-selector") as report_kb_panel:
                    input_database_select_report = gr.Radio(
                        choices=database_namelist,
                        label="",
                        value=database_namelist[0],
                        elem_classes=["knowledge-base-selector"],
                        interactive=True
                    )
                
                gr.Markdown("### 报告参数设置", elem_classes="input-label")
                # 简化表单结构
                input_prompt = gr.DataFrame(
                    database_list[0].prompt_data, 
                    max_height=400,
                    elem_classes="report-input"
                )

                with gr.Row():
                    submit_btn = gr.Button("⚡ 生成报告", elem_classes="standard-button")
                    refresh_db_btn_report = gr.Button("🔄 刷新知识库", elem_classes="standard-button")

                with gr.Accordion("📜 生成结果", open=True):
                    output_report = gr.Markdown(label="报告生成内容")

            # 知识库问答界面
            with gr.Group(visible=False, elem_classes="function-panel" ) as qa_panel:
                # 顶部欢迎信息和知识库选择
                with gr.Row():
                    # 欢迎信息
                    with gr.Column(scale=3):
                        gr.Markdown("""
                        ### 欢迎使用智能法律助手
                        请选择您感兴趣的法律领域，或直接输入您的问题
                        """, elem_classes="panel-title")
                    # 知识库选择按钮
                    with gr.Column(scale=1):
                        kb_button = gr.Button("选择知识库 ▼", elem_classes="standard-button")
                
                # 知识库选择状态
                kb_panel_state = gr.State(False)
                
                # 浮动知识库选择面板 (默认隐藏)
                with gr.Column(visible=False, elem_classes="floating-kb-selector") as kb_panel:
                    input_database_select_QA = gr.Radio(
                        choices=database_namelist,
                        label="",
                        value=database_namelist[0],
                        elem_classes=["knowledge-base-selector"],
                        interactive=True
                    )
                
                with gr.Accordion("📢 回答结果", open=True):
                    output_answer = gr.Markdown(label="回答")
                    output_images = gr.Gallery(label="相关图片", columns=[3], height=300)
                
                # 输入框和发送按钮 - 新样式
                with gr.Row():
                    with gr.Column():
                        # 自定义输入区样式
                        with gr.Column(elem_classes="input-container"):
                            # 输入框放在左上方，无边框色
                            input_question = gr.Textbox(
                                show_label=False,
                                placeholder="请输入您想问的法律问题...",
                                lines=3,
                                max_lines=8,
                                container=False
                            )
                            
                            # 底部操作区（左侧为模型选择，右侧为发送按钮）
                            with gr.Row(elem_classes="input-actions"):
                                # 左下方：模型选择按钮
                                model_button = gr.Button("选择模型 ▼", elem_classes="standard-button")
                                # 右下方：发送按钮
                                submit_qa_btn = gr.Button("发送", elem_classes="standard-button")
                
                # 模型选择状态
                model_panel_state = gr.State(False)
                
                # 浮动模型选择面板 (默认隐藏)
                with gr.Column(visible=False, elem_classes="floating-model-selector") as model_panel:
                    model_selector = gr.Radio(
                        choices=AVAILABLE_MODELS,
                        label="",
                        value="deepseek-v3",
                        elem_classes=["model-selector"],
                        interactive=True
                    )
                
                # 添加自定义CSS
                gr.HTML("""
                <style>
                .floating-model-selector {
                    position: absolute;
                    bottom: 100%;
                    left: 0;
                    z-index: 100;
                    background-color: white;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
                    margin-bottom: 5px;
                    padding: 10px;
                    min-width: 200px;
                }
                </style>
                """)
                
                # 添加示例问题 - 放在输入框定义之后
                with gr.Accordion("常见问题示例", open=False):
                    example_questions = gr.Examples(
                        examples=[
                            "什么是正当防卫？",
                            "劳动合同纠纷如何解决？",
                            "交通事故责任认定标准是什么？",
                            "如何申请离婚？"
                        ],
                        inputs=input_question
                    )

                # 模型选择面板控制
                def toggle_model_panel(state):
                    return not state, gr.update(visible=not state)
                
                model_button.click(
                    fn=toggle_model_panel, 
                    inputs=[model_panel_state], 
                    outputs=[model_panel_state, model_panel]
                )
                
                # 模型选择后更新按钮文本并隐藏面板
                def update_model_button(choice, state):
                    return f"选择模型: {choice} ▼", not state, gr.update(visible=False)
                
                model_selector.change(
                    fn=update_model_button, 
                    inputs=[model_selector, model_panel_state], 
                    outputs=[model_button, model_panel_state, model_panel]
                )

            # Graph 可视化界面
            with gr.Group(visible=False, elem_classes="function-panel") as graph_panel:
                # 顶部标题
                gr.Markdown("### 交互式知识图谱展示", elem_classes="panel-title")
                gr.Markdown("选择不同的知识图谱文件以查看不同的法律知识结构", elem_classes="panel-description")
                
                available_html_files = get_available_graph_html_files()
                
                graph_selector = gr.Dropdown(
                    choices=available_html_files,
                    label="选择知识图谱文件",
                    value=available_html_files[0] if available_html_files else "graph.html",
                    scale=3
                )
                fullscreen_btn = gr.Button("📺 全屏显示", elem_classes="standard-button")
                
                is_fullscreen = gr.State(False)
                graph_display = gr.HTML(
                    update_graph_html(available_html_files[0] if available_html_files else "graph.html"),
                    label="知识图谱可视化",
                    elem_id="graph_display"
                )
                
            # 上传知识库界面
            with gr.Group(visible=False, elem_classes="function-panel") as upload_panel:
                # 顶部标题
                gr.Markdown("### 上传新知识库", elem_classes="panel-title")
                gr.Markdown("请选择要上传的知识库文件夹，文件夹中应包含：\n- prompt.xlsx 文件\n- txt 或 pdf 格式的文档", elem_classes="panel-description")
                
                with gr.Row():
                    with gr.Column():
                        with gr.Column(elem_classes="input-container"):
                            # 使用单个文件上传组件
                            upload_files = gr.File(
                                label="选择文件夹", 
                                file_count="directory",
                                file_types=[".txt", ".csv", ".json", ".pdf", ".xlsx"],
                                interactive=True
                            )
                            
                            # 底部操作区
                            with gr.Row(elem_classes="input-actions"):
                                # 左侧可以放置提示信息或占位符
                                gr.Markdown("")
                                # 右侧放置上传按钮
                                upload_button = gr.Button("开始上传", 
                                                        elem_classes="standard-button")
                
                with gr.Column():
                    upload_status = gr.Textbox(
                        label="上传状态",
                        value="等待上传...",
                        interactive=False
                    )
                
                # 修改上传按钮的点击事件，使用 progress 参数
                def upload_with_progress(*args):
                    return (
                        gr.update(value="处理完成！"), 
                        *upload(*args)
                    )
                
                upload_button.click(
                    fn=upload_with_progress,
                    inputs=[upload_files, input_database_select_report], 
                    outputs=[upload_status, input_database_select_report, input_prompt, input_database_select_QA],
                    show_progress="处理中..."  # 在 Gradio 5.x 中显示进度
                )

    # 功能切换逻辑
    def show_panel(panel_name):
        if panel_name == "report":
            return (gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                    gr.update(elem_classes=["sidebar-btn", "selected"]), 
                    gr.update(elem_classes=["sidebar-btn"]), 
                    gr.update(elem_classes=["sidebar-btn"]),
                    gr.update(elem_classes=["sidebar-btn"]),
                    gr.update(elem_classes=["sidebar-btn"]))
        elif panel_name == "qa":
            return (gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), gr.update(visible=False),
                    gr.update(elem_classes=["sidebar-btn"]), 
                    gr.update(elem_classes=["sidebar-btn", "selected"]), 
                    gr.update(elem_classes=["sidebar-btn"]),
                    gr.update(elem_classes=["sidebar-btn"]),
                    gr.update(elem_classes=["sidebar-btn"]))
        elif panel_name == "contract":
            # 合同生成功能当前重定向到报告生成
            return (gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                    gr.update(elem_classes=["sidebar-btn"]), 
                    gr.update(elem_classes=["sidebar-btn"]), 
                    gr.update(elem_classes=["sidebar-btn", "selected"]),
                    gr.update(elem_classes=["sidebar-btn"]),
                    gr.update(elem_classes=["sidebar-btn"]))
        elif panel_name == "graph":
            return (gr.update(visible=False), gr.update(visible=False), gr.update(visible=True), gr.update(visible=False),
                    gr.update(elem_classes=["sidebar-btn"]), 
                    gr.update(elem_classes=["sidebar-btn"]), 
                    gr.update(elem_classes=["sidebar-btn"]),
                    gr.update(elem_classes=["sidebar-btn", "selected"]),
                    gr.update(elem_classes=["sidebar-btn"]))
        else:  # "upload"
            return (gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=True),
                    gr.update(elem_classes=["sidebar-btn"]), 
                    gr.update(elem_classes=["sidebar-btn"]), 
                    gr.update(elem_classes=["sidebar-btn"]),
                    gr.update(elem_classes=["sidebar-btn"]),
                    gr.update(elem_classes=["sidebar-btn", "selected"]))
        
    report_btn.click(
        fn=lambda: show_panel("report"),
        inputs=[],
        outputs=[report_generation_panel, qa_panel, graph_panel, upload_panel,
                 report_btn, qa_btn,  graph_btn, upload_btn] # contract_btn,
    )
    
    qa_btn.click(
        fn=lambda: show_panel("qa"),
        inputs=[],
        outputs=[report_generation_panel, qa_panel, graph_panel, upload_panel,
                 report_btn, qa_btn,  graph_btn, upload_btn] # contract_btn,
    )
    
    # contract_btn.click(
    #     fn=lambda: show_panel("contract"),
    #     inputs=[],
    #     outputs=[report_generation_panel, qa_panel, graph_panel, upload_panel,
    #              report_btn, qa_btn, contract_btn, graph_btn, upload_btn]
    # )
    
    graph_btn.click(
        fn=lambda: show_panel("graph"),
        inputs=[],
        outputs=[report_generation_panel, qa_panel, graph_panel, upload_panel,
                 report_btn, qa_btn,  graph_btn, upload_btn] # contract_btn,
    )
    
    upload_btn.click(
        fn=lambda: show_panel("upload"),
        inputs=[],
        outputs=[report_generation_panel, qa_panel, graph_panel, upload_panel,
                 report_btn, qa_btn,  graph_btn, upload_btn] # contract_btn,
    )

    # 功能事件处理
    submit_btn.click(function_report_generation, 
                     [input_database_select_report, input_prompt], 
                     [output_report])
    
    # 上传知识库后，更新所有下拉菜单
    def update_all_database_dropdowns():
        # 全局变量声明必须在函数开头
        global database_list, database_namelist
        
        # 重新加载所有数据库
        #database_list, database_namelist = load_database()
        
        # 返回更新后的下拉菜单和按钮
        return (
            gr.update(choices=database_namelist, value=database_namelist[0] if database_namelist else None),  # report radio
            gr.update(choices=database_namelist, value=database_namelist[0] if database_namelist else None),  # qa radio
            "选择知识库 ▼",  # report button
            "选择知识库 ▼"   # qa button
        )
    
    # 刷新按钮点击事件
    refresh_db_btn_report.click(
        fn=update_all_database_dropdowns,
        inputs=None,
        outputs=[input_database_select_report, input_database_select_QA, report_kb_button, kb_button]
    )
    
    # 修改问答提交事件，添加模型选择参数
    submit_qa_btn.click(
        function_QA,
        [input_database_select_QA, input_question, model_selector],
        [output_answer, output_images]
    )
    
    # 知识库选择面板控制 (问答界面)
    def toggle_kb_panel(state):
        return not state, gr.update(visible=not state)
    
    kb_button.click(
        fn=toggle_kb_panel, 
        inputs=[kb_panel_state], 
        outputs=[kb_panel_state, kb_panel]
    )
    
    # 知识库选择后更新按钮文本并隐藏面板 (问答界面)
    def update_kb_button(choice, state):
        return f"选择知识库: {choice} ▼", not state, gr.update(visible=False)
    
    input_database_select_QA.change(
        fn=update_kb_button, 
        inputs=[input_database_select_QA, kb_panel_state], 
        outputs=[kb_button, kb_panel_state, kb_panel]
    )
    
    # 知识库选择面板控制 (报告界面)
    def toggle_report_kb_panel(state):
        return not state, gr.update(visible=not state)
    
    report_kb_button.click(
        fn=toggle_report_kb_panel, 
        inputs=[report_kb_panel_state], 
        outputs=[report_kb_panel_state, report_kb_panel]
    )
    
    # 知识库选择后更新按钮文本并隐藏面板 (报告界面)
    def update_report_kb_button(choice, state):
        return f"选择知识库: {choice} ▼", not state, gr.update(visible=False)
    
    input_database_select_report.change(
        fn=update_report_kb_button, 
        inputs=[input_database_select_report, report_kb_panel_state], 
        outputs=[report_kb_button, report_kb_panel_state, report_kb_panel]
    )
    
    # 同时更新报告表单
    input_database_select_report.change(
        fn=database_change, 
        inputs=[input_database_select_report], 
        outputs=[input_prompt]
    )
    
    # 直接加载初始化下拉菜单
    demo.load(
        fn=update_all_database_dropdowns,
        inputs=None,
        outputs=[input_database_select_report, input_database_select_QA, report_kb_button, kb_button]
    )
    
    # 图表相关功能
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

if __name__ == "__main__":
    print("正在启动GraphRAG演示应用，请稍候...")
    try:
        # 等待HTTP服务器线程启动
        time.sleep(1)
        
        # 启动Gradio应用
        try:
            demo.launch(server_name="127.0.0.1", 
                        server_port=9920,  # 更改为9920端口
                        share=False,
                        show_api=False,
                        allowed_paths=["D:\LLM\QBTech_RAG_Demo"])
        except OSError:
            # 如果指定端口被占用，让Gradio自动选择可用端口
            print("指定端口已被占用，尝试启动在随机可用端口...")
            demo.launch(server_name="127.0.0.1", 
                        server_port=None,  # 自动选择可用端口
                        share=False,
                        show_api=False,
                        allowed_paths=["D:\LLM\QBTech_RAG_Demo"])
    except KeyboardInterrupt:
        print("应用已通过键盘中断退出")
    except Exception as e:
        print(f"启动应用时出错: {e}")