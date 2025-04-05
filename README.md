# 智能法律助手系统 - 使用指南

## 项目简介

智能法律助手是一个基于知识库检索增强生成(RAG)的智能问答系统，可以通过图形化界面进行法律问答、报告生成、知识图谱展示等功能。系统支持多种大语言模型，包括GPT-4、Qwen-VL-Max、Deepseek-R1和Deepseek-V3等，能够智能检索知识库并生成专业的法律解答。

## 系统要求

- Python 3.8 或更高版本
- Windows/Linux/Mac 操作系统
- 网络连接（用于调用大模型API）

## 安装步骤

### 1. 克隆或下载项目

```bash
git clone <项目仓库地址>
cd <项目目录>
```

### 2. 创建虚拟环境（推荐）

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 3. 安装依赖包

```bash
pip install -r requirements.txt
```

如果项目中没有`requirements.txt`文件，请安装以下必要依赖：

```bash
pip install gradio==5.0.0
pip install openai
pip install numpy
pip install pandas
pip install pillow
pip install jieba
pip install pymupdf
```

## 运行系统

### 1. 准备知识库

确保项目目录中已包含初始知识库，或者准备好以下文件用于上传新知识库：
- prompt.xlsx（必需）：包含知识库的提示词数据
- 法律文档：.txt 或 .pdf 格式的法律文档

### 2. 启动应用

```bash
cd source
python main2.py
```

系统将自动启动两个服务：
- HTTP服务器（默认端口：8080）：用于提供图谱文件和图片访问
- Gradio Web界面（默认端口：9920）：用户交互界面

如果端口被占用，系统会自动尝试其他可用端口。

### 3. 访问系统

启动成功后，在浏览器中访问：
```
http://127.0.0.1:9920
```

## 系统功能

### 1. 智能问答
- 选择知识库：点击"选择知识库"按钮选择相应领域的知识库
- 选择模型：点击"选择模型"按钮选择需要使用的大语言模型
- 输入问题：在文本框中输入法律问题
- 获取回答：系统会检索知识库，并通过选定的大模型生成专业回答

### 2. 生成报告
- 选择知识库：点击"选择知识库"按钮选择相应领域的知识库
- 填写报告参数：在表格中填写报告所需的信息
- 生成报告：点击"生成报告"按钮生成专业法律报告

### 3. 知识图谱
- 选择知识图谱文件：从下拉列表中选择不同的知识图谱文件
- 查看图谱：系统会显示所选知识图谱的可视化表示
- 全屏显示：点击"全屏显示"按钮可切换全屏模式

### 4. 上传知识库
- 选择文件夹：上传包含prompt.xlsx和法律文档(.txt或.pdf)的文件夹
- 开始上传：点击"开始上传"按钮，系统会自动解析并构建知识库
- 处理状态：系统会显示上传处理的状态

## 注意事项

1. 确保`logo.jpg`文件位于项目根目录，用于显示系统logo
2. 确保网络连接正常，以便调用大语言模型API
3. 上传的知识库文件夹必须包含prompt.xlsx文件和至少一个.txt或.pdf文档

## 故障排除

1. 如果界面无法正常显示，请检查浏览器控制台是否有错误信息
2. 如果图片或图谱不显示，请检查HTTP服务器是否正常启动
3. 如果模型回复失败，请检查API密钥和网络连接

## API密钥配置

系统使用的API密钥位于`source/llm_api.py`文件中，您可以根据需要更改：

```python
api_key = "您的API密钥"
base_url = "https://api.agicto.cn/v1"  # API服务地址
```

---

如有任何问题或建议，请联系项目维护人员。 