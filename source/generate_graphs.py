import os
import pandas as pd
from pyvis.network import Network
from project_database import load_database, database_list, database_namelist

def generate_graph_for_database(database_name, output_dir="."):
    """Ϊָ����֪ʶ������ͼ��HTML�ļ�
    
    Args:
        database_name: ֪ʶ������
        output_dir: ���Ŀ¼��Ĭ��Ϊ��ǰĿ¼
    
    Returns:
        ���ɵ�HTML�ļ�·��
    """
    print(f"��ʼΪ֪ʶ�� {database_name} ����ͼ��...")
    
    # ������Ը���֪ʶ�����ƻ�ȡ��Ӧ�Ľڵ�͹�ϵ����
    # ����ÿ��֪ʶ�ⶼ�и��Ե�����·��
    base_path = os.path.join("..", "database_dir", database_name)
    
    # ����Ƿ����֪ʶ���ض��Ľڵ�͹�ϵ����
    nodes_path = os.path.join(base_path, "nodes.parquet")
    relations_path = os.path.join(base_path, "relationships.parquet")
    
    if os.path.exists(nodes_path) and os.path.exists(relations_path):
        nodes_df = pd.read_parquet(nodes_path)
        relationships_df = pd.read_parquet(relations_path)
    else:
        # ���û���ض�֪ʶ������ݣ�ʹ��Ĭ������
        print(f"δ�ҵ�֪ʶ�� {database_name} ���ض�ͼ�����ݣ�ʹ��Ĭ������")
        nodes_df = pd.read_parquet("../test/output/create_final_nodes.parquet")
        relationships_df = pd.read_parquet("../test/output/create_final_relationships.parquet")
    
    # ���� Pyvis ����
    net = Network(
        notebook=True, 
        height="800px",  
        width="100%", 
        directed=True, 
        bgcolor="#ffffff",  
        font_color="green"  
    )
    
    # ��������������
    net.barnes_hut(gravity=-2000, central_gravity=0.1, spring_length=300, spring_strength=0.05)
    
    # ��ӽڵ�
    for _, row in nodes_df.iterrows():
        net.add_node(
            row["title"],  
            label=row["title"],  
            title=f'����: {row["type"]}',  
            color="red" if row["type"] == "PERSON" else "blue",
            size=25,  
            font={"size": 14, "color": "green"}
        )
    
    # ��ӱ�
    for _, row in relationships_df.iterrows():
        net.add_edge(
            row["source"], 
            row["target"],
            value=row.get("rank", 1),
            title=f"��ϵ: {row.get('description', '������')}",  
            label=row.get("description", "������"),  
            font={"size": 10, "color": "black", "lineHeight": 50},  
            smooth=True  
        )
    
    # ����HTML�ļ�
    output_file = os.path.join(output_dir, f"graph_{database_name}.html")
    net.show(output_file)
    
    # ����Զ���CSS�ͽ�������
    with open(output_file, 'r', encoding='utf-8') as file:
        html_content = file.read()
    
    # ����Զ���CSS��ʽ
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
    
    # ����������ܺͱ���
    custom_js = f'''
        <script type="text/javascript">
            // ��ӱ���
            document.body.insertAdjacentHTML('afterbegin', 
                '<h1 class="title">֪ʶ��: {database_name} - ֪ʶͼ�׿��ӻ�</h1>' +
                '<p class="subtitle">������ʾ: ����ק�ڵ㡢�������š������ؼ���</p>'
            );
            
            // ���������
            document.body.insertAdjacentHTML('afterbegin', 
                '<div class="search-container">' +
                '<input type="text" id="search" placeholder="�����ڵ�..." />' +
                '</div>'
            );
            
            // ��������
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
                    // ����ƥ��Ľڵ������
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
                    // �ָ����нڵ�Ϊԭʼ״̬
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
            
            // ���û�����ڵ�ʱ����ԭʼ��ɫ
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
    
    # ��HTML���������Զ���CSS��JS
    modified_html = html_content.replace('</head>', f'{custom_css}</head>')
    modified_html = modified_html.replace('</body>', f'{custom_js}</body>')
    
    # д���޸ĺ��HTML
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(modified_html)
    
    print(f"֪ʶ�� {database_name} ��ͼ��������: {output_file}")
    return output_file

def generate_all_graphs():
    """Ϊ����֪ʶ������ͼ��HTML�ļ�"""
    # ��������֪ʶ��
    all_databases, all_database_names = load_database()
    
    for db_name in all_database_names:
        generate_graph_for_database(db_name)
    
    print(f"��Ϊ���� {len(all_database_names)} ��֪ʶ������ͼ��")

if __name__ == "__main__":
    # ��ֱ�����д˽ű�ʱ��Ϊ����֪ʶ������ͼ��
    generate_all_graphs() 