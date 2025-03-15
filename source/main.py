import os
import gradio as gr
import threading
import http.server
import socketserver
import sqlite3  # 用于存储用户信息
from project_database import *
from ui_backend import *
from config import *

# ==== 1️⃣ 启动 HTTP 服务器，确保 graph.html 可访问 ====
PORT = 8000

def start_http_server():
    os.chdir(os.path.dirname(os.path.abspath("graph.html")))
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        httpd.serve_forever()

threading.Thread(target=start_http_server, daemon=True).start()

# ==== 2️⃣ 连接数据库，初始化用户表 ====
def init_user_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                      id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      username TEXT UNIQUE, 
                      password TEXT)''')
    conn.commit()
    conn.close()

def check_login(username, password):
    """验证用户名和密码"""
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user is not None  # 存在即成功

init_user_db()

# ==== 3️⃣ 加载知识库 ====
database_list, database_namelist = load_database()

# ==== 4️⃣ Gradio 登录 + 主界面 ====
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    # login_status = gr.State(False)  # ⬅ 记录是否登录

    # # ✅ 登录界面
    # with gr.Row(visible=True) as login_page:
    #     gr.Markdown("## 🔐 用户登录")
    #     username_input = gr.Textbox(label="用户名")
    #     password_input = gr.Textbox(label="密码", type="password")
    #     login_btn = gr.Button("登录")
    #     login_output = gr.Textbox(label="登录状态", interactive=False)

    # ✅ 主界面（初始时隐藏）
    with gr.Blocks(visible=False) as main_page:
        gr.Markdown("## 🚀 检索与报告生成智能体")
        
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
                    output_gen_proc = gr.Textbox(label="报告生成过程", lines=11)
                    output_report = gr.Textbox(label="报告生成内容", lines=11)

                submit_btn.click(function_report_generation, 
                                 [input_database_select_report, input_prompt], 
                                 [output_gen_proc, output_report])
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
                    output_answer = gr.Textbox(label="回答", lines=5)
                    output_images = gr.Gallery(label="相关图片", columns=[3], height=300)

                submit_qa_btn.click(function_QA, 
                                    [input_database_select_QA, input_question], 
                                    [output_answer, output_images])

            # 🌐 Graph 可视化
            with gr.Tab("🌐 Graph 可视化"):
                gr.Markdown("### 交互式知识图谱展示")
                
                graph_display = gr.HTML(
                    f"""
                    <iframe 
                        src="http://127.0.0.1:{PORT}/graph.html" 
                        style="width: 100vw; height: 90vh; border: none; overflow: hidden;">
                    </iframe>
                    """,
                    label="Graph Visualization"
                )

    # # ✅ 登录验证逻辑
    # def login(username, password):
    #     if check_login(username, password):
    #         return gr.update(visible=False), gr.update(visible=True), "✅ 登录成功！"
    #     else:
    #         return gr.update(visible=True), gr.update(visible=False), "❌ 登录失败，请检查用户名和密码"

    # login_btn.click(login, 
    #                 [username_input, password_input], 
    #                 [login_page, main_page, login_output])

demo.launch(server_name="127.0.0.1", 
            server_port=9909, 
            show_api=False, 
            allowed_paths=["D:\LLM\QBTech_RAG_Demo"]
            )
