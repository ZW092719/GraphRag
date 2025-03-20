import pandas as pd
from pyvis.network import Network
import os

# 读取节点和关系数据
nodes_df = pd.read_parquet("../test/output/create_final_nodes.parquet")
relationships_df = pd.read_parquet("../test/output/create_final_relationships.parquet")

# 创建 Pyvis 网络
net = Network(
    notebook=True, 
    height="800px",  
    width="100%", 
    directed=True, 
    bgcolor="#ffffff",  # 修改为白色背景
    font_color="green"  
)

# 调整物理仿真
net.barnes_hut(gravity=-2000, central_gravity=0.1, spring_length=300, spring_strength=0.05)

# 添加节点
for _, row in nodes_df.iterrows():
    net.add_node(
        row["title"],  
        label=row["title"],  
        title=f'Type: {row["type"]}',  
        color="red" if row["type"] == "PERSON" else "blue",
        size=25,  
        font={"size": 14, "color": "green"}  # 调整字体大小
    )

# 添加边
for _, row in relationships_df.iterrows():
    net.add_edge(
        row["source"], 
        row["target"],
        value=row.get("rank", 1),  # 使用get避免KeyError
        title=f"关系: {row.get('description', '无描述')}",  
        #label=row.get("description", "无描述"),  
        font={"size": 10, "color": "black", "lineHeight": 50},  
        smooth=True  
    )

# 生成 HTML
net.show("graph.html")

# 在生成的HTML文件中添加自定义样式和交互功能
html_file = "graph.html"

# 读取生成的HTML文件
with open(html_file, 'r', encoding='utf-8') as file:
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
            font-size: 24px;
            margin: 20px 0;
            font-weight: 500;
        }
    </style>
'''

# 添加标题
title_html = '<div class="title">知识图谱可视化</div>\n'

# 添加搜索框
search_container = '''
    <div class="search-container">
        <input type="text" id="search" placeholder="搜索节点..." onkeyup="searchGraph()">
    </div>
'''

# 添加包裹卡片DIV，替换原有的div包装
html_content = html_content.replace('<div id="mynetwork"></div>', 
                                   '<div class="card"><div id="mynetwork" class="card-body"></div></div>')

# 添加节点选择和搜索功能脚本
node_selection_script = '''
<script>
    // 在绘图完成后添加节点选择事件
    network.on("selectNode", function(params) {
        // 获取选中的节点
        var selectedNode = params.nodes[0];
        
        // 获取与该节点相连的所有边
        var connectedEdges = network.getConnectedEdges(selectedNode);
        
        // 获取相连的节点
        var connectedNodes = new Set();
        connectedEdges.forEach(edgeId => {
            var edge = edges.get(edgeId);
            connectedNodes.add(edge.from);
            connectedNodes.add(edge.to);
        });
        
        // 更新所有节点的样式
        nodes.update(nodes.get().map(node => {
            if (node.id === selectedNode) {
                return {
                    ...node,
                    color: {background: '#2196F3', border: '#1976D2'},
                    size: 35,
                    font: {color: '#ffffff', size: 16, face: 'bold'}
                };
            } else if (connectedNodes.has(node.id)) {
                return {
                    ...node,
                    color: {background: '#64B5F6', border: '#42A5F5'},
                    size: 30,
                    font: {color: '#ffffff', size: 14}
                };
            } else {
                return {
                    ...node,
                    color: {background: '#E0E0E0', border: '#BDBDBD'},
                    size: 25,
                    font: {color: '#757575', size: 12},
                    opacity: 0.3
                };
            }
        }));
        
        // 更新所有边的样式
        edges.update(edges.get().map(edge => {
            if (connectedEdges.includes(edge.id)) {
                return {
                    ...edge,
                    color: {color: '#2196F3', highlight: '#1976D2'},
                    width: 3,
                    opacity: 1
                };
            } else {
                return {
                    ...edge,
                    color: {color: '#BDBDBD', highlight: '#9E9E9E'},
                    width: 1,
                    opacity: 0.2
                };
            }
        }));
    });
    
    // 取消选择时恢复原样
    network.on("deselectNode", function(params) {
        // 恢复所有节点的样式
        nodes.update(nodes.get().map(node => ({
            ...node,
            color: nodeColors[node.id],
            size: 25,
            font: {color: 'green', size: 14},
            opacity: 1
        })));
        
        // 恢复所有边的样式
        edges.update(edges.get().map(edge => ({
            ...edge,
            color: {color: 'gray', highlight: 'gray'},
            width: 1,
            opacity: 1
        })));
    });
    
    // 搜索功能
    function searchGraph() {
        let keyword = document.getElementById("search").value.trim().toLowerCase();
        if (!network || !network.body || !network.body.data) return;

        let nodes = network.body.data.nodes;
        let edges = network.body.data.edges;

        // 遍历所有节点，匹配搜索关键字
        nodes.update(nodes.get().map(node => {
            if (node.label && node.label.toLowerCase().includes(keyword)) {
                return {
                    ...node, 
                    color: {background: '#ffeb3b', border: '#f44336'}, 
                    size: 30, 
                    font: {color: 'black', size: 16}
                };
            } else {
                return {
                    ...node, 
                    color: nodeColors[node.id], 
                    size: 25, 
                    font: {color: 'green', size: 14},
                    opacity: keyword ? 0.3 : 1
                };
            }
        }));

        // 遍历所有边，判断是否需要高亮
        edges.update(edges.get().map(edge => {
            let highlight = [edge.from, edge.to].some(nodeId => {
                let node = nodes.get(nodeId);
                return node && node.label && node.label.toLowerCase().includes(keyword);
            });

            return highlight 
                ? {...edge, color: {color: '#f44336', highlight: '#f44336'}, width: 2, opacity: 1} 
                : {...edge, color: {color: 'gray', highlight: 'gray'}, width: 1, opacity: keyword ? 0.2 : 1};
        }));
    }
</script>
'''

# 添加自定义CSS到head部分
html_content = html_content.replace('</head>', f'{custom_css}</head>')

# 添加标题到body部分
html_content = html_content.replace('<body>', f'<body>\n{title_html}')

# 添加搜索框到body部分
html_content = html_content.replace('<body>', f'<body>\n{search_container}')

# 添加节点选择脚本到body结束前
html_content = html_content.replace('</body>', f'{node_selection_script}\n</body>')

# 保存修改后的HTML
with open(html_file, 'w', encoding='utf-8') as file:
    file.write(html_content)

print(f"已生成增强版知识图谱: {os.path.abspath(html_file)}")
