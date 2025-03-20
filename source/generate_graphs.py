import os
import pandas as pd
from pyvis.network import Network
from project_database import load_database, database_list, database_namelist

def generate_graph_for_database(database_name, output_dir="."):
    """为指定的知识库生成图表HTML文件
    
    Args:
        database_name: 知识库名称
        output_dir: 输出目录，默认为当前目录
    
    Returns:
        生成的HTML文件路径
    """
    print(f"开始为知识库 {database_name} 生成图表...")
    
    # 这里可以根据知识库名称获取对应的节点和关系数据
    # 假设每个知识库都有各自的数据路径
    base_path = os.path.join("..", "database_dir", database_name)
    
    # 检查是否存在知识库特定的节点和关系数据
    nodes_path = os.path.join(base_path, "nodes.parquet")
    relations_path = os.path.join(base_path, "relationships.parquet")
    
    if os.path.exists(nodes_path) and os.path.exists(relations_path):
        nodes_df = pd.read_parquet(nodes_path)
        relationships_df = pd.read_parquet(relations_path)
    else:
        # 如果没有特定知识库的数据，使用默认数据
        print(f"未找到知识库 {database_name} 的特定图表数据，使用默认数据")
        nodes_df = pd.read_parquet("../test/output/create_final_nodes.parquet")
        relationships_df = pd.read_parquet("../test/output/create_final_relationships.parquet")
    
    # 创建 Pyvis 网络
    net = Network(
        notebook=True, 
        height="800px",  
        width="100%", 
        directed=True, 
        bgcolor="#ffffff",  
        font_color="green"  
    )
    
    # 调整物理仿真参数
    net.barnes_hut(gravity=-2000, central_gravity=0.1, spring_length=300, spring_strength=0.05)
    
    # 添加节点
    for _, row in nodes_df.iterrows():
        net.add_node(
            row["title"],  
            label=row["title"],  
            title=f'类型: {row["type"]}',  
            color="red" if row["type"] == "PERSON" else "blue",
            size=25,  
            font={"size": 14, "color": "green"}
        )
    
    # 添加边
    for _, row in relationships_df.iterrows():
        net.add_edge(
            row["source"], 
            row["target"],
            value=row.get("rank", 1),
            title=f"关系: {row.get('description', '无描述')}",  
            label=row.get("description", "无描述"),  
            font={"size": 10, "color": "black", "lineHeight": 50},  
            smooth=True  
        )
    
    # 生成HTML文件
    output_file = os.path.join(output_dir, f"graph_{database_name}.html")
    net.show(output_file)
    
    # 添加自定义CSS和交互功能
    with open(output_file, 'r', encoding='utf-8') as file:
        html_content = file.read()
    
    # 添加自定义CSS样式
    custom_css = '''
        <style type="text/css">
            body {
                background-color: #f5f5f5;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            #mynetwork {
                width: 100%;
                height: 800px;
                background-color: #ffffff;
                border: none;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                position: relative;
                float: left;
            } 
            .card {
                margin: 20px;
                border: none;
                border-radius: 12px;
                box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
            }
            .search-container {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 1000;
            }
            #search {
                width: 250px;
                padding: 12px 20px;
                border: 2px solid #e0e0e0;
                border-radius: 25px;
                font-size: 14px;
                transition: all 0.3s ease;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            }
            #search:focus {
                outline: none;
                border-color: #2196F3;
                box-shadow: 0 2px 8px rgba(33, 150, 243, 0.2);
            }
            .title {
                text-align: center;
                color: #333;
                margin: 20px 0;
                font-size: 24px;
                font-weight: 600;
            }
            .subtitle {
                text-align: center;
                color: #666;
                margin: 10px 0 30px;
                font-size: 16px;
            }
        </style>
    '''
    
    # 添加搜索功能和标题
    custom_js = f'''
        <script type="text/javascript">
            // 添加标题
            document.body.insertAdjacentHTML('afterbegin', 
                '<h1 class="title">知识库: {database_name} - 知识图谱可视化</h1>' +
                '<p class="subtitle">互动提示: 可拖拽节点、滚轮缩放、搜索关键词</p>'
            );
            
            // 添加搜索框
            document.body.insertAdjacentHTML('afterbegin', 
                '<div class="search-container">' +
                '<input type="text" id="search" placeholder="搜索节点..." />' +
                '</div>'
            );
            
            // 搜索功能
            document.getElementById('search').addEventListener('input', function(e) {{
                var value = e.target.value.toLowerCase();
                var allNodes = network.body.data.nodes.get();
                var nodesToHighlight = [];
                
                allNodes.forEach(function(node) {{
                    if (node.label.toLowerCase().includes(value)) {{
                        nodesToHighlight.push(node.id);
                    }}
                }});
                
                var connectedNodes = {{}}; 
                var allEdges = network.body.data.edges.get();
                
                if (nodesToHighlight.length > 0 && value.length > 0) {{
                    // 高亮匹配的节点和连接
                    var connectedNodeIds = [];
                    
                    allNodes.forEach(function(node) {{
                        var isHighlighted = nodesToHighlight.includes(node.id);
                        if (isHighlighted) {{
                            node.color = '#FF5722';
                            node.font = {{ color: '#FF5722', size: 18 }};
                            node.size = 35;
                        }} else {{
                            node.color = node.originalColor || '#97C2FC';
                            node.font = {{ color: 'black', size: 14 }};
                            node.size = 25;
                        }}
                        
                        connectedNodes[node.id] = {{
                            color: node.color,
                            font: node.font,
                            size: node.size
                        }};
                    }});
                    
                    network.body.data.nodes.update(allNodes);
                }} else {{
                    // 恢复所有节点为原始状态
                    allNodes.forEach(function(node) {{
                        node.color = node.originalColor || '#97C2FC';
                        node.font = {{ color: 'black', size: 14 }};
                        node.size = 25;
                        
                        connectedNodes[node.id] = {{
                            color: node.color,
                            font: node.font,
                            size: node.size
                        }};
                    }});
                    
                    network.body.data.nodes.update(allNodes);
                }}
            }});
            
            // 当用户点击节点时保存原始颜色
            network.on("selectNode", function(params) {{
                var selectedNodeId = params.nodes[0];
                var allNodes = network.body.data.nodes.get();
                
                allNodes.forEach(function(node) {{
                    if (!node.originalColor) {{
                        node.originalColor = node.color;
                    }}
                }});
                
                network.body.data.nodes.update(allNodes);
            }});
        </script>
    '''
    
    # 在HTML的最后插入自定义CSS和JS
    modified_html = html_content.replace('</head>', f'{custom_css}</head>')
    modified_html = modified_html.replace('</body>', f'{custom_js}</body>')
    
    # 写回修改后的HTML
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(modified_html)
    
    print(f"知识库 {database_name} 的图表已生成: {output_file}")
    return output_file

def generate_all_graphs():
    """为所有知识库生成图表HTML文件"""
    # 加载所有知识库
    all_databases, all_database_names = load_database()
    
    for db_name in all_database_names:
        generate_graph_for_database(db_name)
    
    print(f"已为所有 {len(all_database_names)} 个知识库生成图表")

if __name__ == "__main__":
    # 当直接运行此脚本时，为所有知识库生成图表
    generate_all_graphs() 