import os

def get_available_graph_html_files():
    """获取目录中所有可用的graph HTML文件"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_files = [f for f in os.listdir(current_dir) if f.endswith('.html')]
    return html_files

def update_graph_html(selected_html, port=8000, fullscreen=False):
    """根据选择的HTML文件更新图表显示"""
    # 根据是否全屏设置不同的样式
    if fullscreen:
        # 全屏模式下的样式
        container_style = "position:fixed; top:0; left:0; width:100vw; height:100vh; z-index:9999; background:white;"
        iframe_style = "width:100%; height:100%; border:none;"
        
        # 创建一个直接刷新页面的退出按钮
        exit_button = """
        <a href="javascript:void(0);" onclick="window.location.reload();" 
           style="position:fixed; bottom:20px; right:20px; z-index:10000; 
                  padding:10px 20px; background:#2196F3; color:white; 
                  border:none; border-radius:4px; cursor:pointer; text-decoration:none;
                  font-size:16px; font-weight:bold; box-shadow: 0 2px 5px rgba(0,0,0,0.3);">
          退出全屏
        </a>
        """
    else:
        # 非全屏模式的样式
        container_style = "width:100%; height:75vh; position:relative;"
        iframe_style = "width:100%; height:100%; border:none;"
        exit_button = ""
    
    html_content = f"""
    <div style="{container_style}">
        {exit_button}
        <iframe 
            src="http://127.0.0.1:{port}/{selected_html}" 
            style="{iframe_style}">
        </iframe>
    </div>
    
    <script>
    // 添加键盘事件监听
    window.addEventListener('keydown', function(e) {{
        // 如果按下ESC键且当前是全屏模式
        if (e.key === 'Escape' && {str(fullscreen).lower()}) {{
            // 直接刷新页面退出全屏
            window.location.reload();
        }}
    }}, true);  // 使用捕获模式以确保优先捕获事件
    </script>
    """
    return html_content

def toggle_fullscreen(selected_html, current_state, port=8000):
    """切换全屏状态并更新图表显示"""
    # 切换状态
    new_state = not current_state
    # 使用新状态更新图表
    return update_graph_html(selected_html, port, new_state), new_state


def update_button_text(is_full):
    return "🔍 退出全屏" if is_full else "📺 全屏显示"