# 骑手意向智能分析系统

🛵 AI驱动的电动车租赁业务洞察与骑手跟进策略分析工具

## 功能概述

本系统专为电动车租赁业务设计，通过AI技术分析与骑手的通话录音或转录文本，自动提取关键信息并生成详细的骑手意向分析报告，帮助业务人员快速了解骑手需求、制定跟进策略。

## 核心功能

### 1. 智能通话分析
- **语音文件处理**：支持MP3格式音频文件上传（最大50MB）
- **文本直接分析**：支持粘贴飞书妙计等工具的转录文本
- **批量处理**：支持多个文件批量上传和分析

### 2. AI驱动的骑手洞察
系统自动分析并生成以下维度的报告：

| 分析维度 | 说明 |
|---------|------|
| 📊 **通话概要** | 通话时长、有效沟通程度、骑手响应积极性 |
| 🏆 **骑手评级** | 租赁意向强度、从业稳定性、决策周期、综合等级(A/B/C类) |
| 🛵 **租赁意向** | 车型需求、预算范围、区域偏好、租期需求 |
| 📍 **从业阶段** | 初步咨询/需求明确/决策阶段/犹豫观望 |
| 🎯 **核心关注点** | 续航、换电、押金、价格等关注优先级 |
| ⚖️ **竞品分析** | 提及竞品、对比倾向、优劣势分析 |
| 😊 **情感分析** | 骑手态度、租赁顾问表现、沟通效果 |
| 🔑 **关键信息** | 联系方式、试车安排、特殊需求 |
| ✅ **分析总结** | 整体评估与建议 |

### 3. 数据管理
- **历史记录**：自动保存所有分析记录，支持查看和重新分析
- **统计仪表盘**：可视化展示业务数据趋势
- **报告导出**：支持PDF报告和文本报告下载

## 技术架构

### 后端技术
- **框架**：Flask (Python)
- **数据库**：SQLite
- **AI分析**：MiniMax API
- **语音处理**：SpeechRecognition + pydub
- **PDF生成**：ReportLab

### 前端技术
- **模板引擎**：Jinja2
- **样式**：原生CSS3 (响应式设计)
- **交互**：原生JavaScript
- **图表**：Chart.js (仪表盘)

### 部署平台
- **推荐**：Render (已配置)
- **备用**：Vercel、其他云服务器

## 快速开始

### 本地开发

1. **克隆仓库**
```bash
git clone https://github.com/CUIJIE1992/rider_analyzer.git
cd rider_analyzer
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，填入你的API密钥
```

5. **运行应用**
```bash
python app.py
```

访问 http://localhost:5000

### 部署到Render

本项目已配置好Render部署文件，只需：

1. 在Render创建新的Web Service
2. 连接GitHub仓库
3. 选择Python 3环境
4. 部署完成

详细配置见 `render.yaml`

## 环境变量配置

复制 `.env.example` 为 `.env` 并配置：

```env
# MiniMax AI配置
MINIMAX_API_KEY=your_minimax_api_key
MINIMAX_GROUP_ID=your_group_id

# 飞书语音转文字配置（可选）
FEISHU_APP_ID=your_feishu_app_id
FEISHU_APP_SECRET=your_feishu_app_secret

# 数据库路径（可选，默认使用项目目录）
DATABASE_PATH=/path/to/your/database
```

## 项目结构

```
rider_analyzer/
├── app.py                 # Flask主应用
├── render.yaml           # Render部署配置
├── requirements.txt      # Python依赖
├── runtime.txt           # Python版本
├── services/             # 业务逻辑层
│   ├── ai_analyzer.py    # AI分析服务
│   ├── audio_processor.py # 音频处理
│   ├── database.py       # 数据库操作
│   ├── pdf_generator.py  # PDF报告生成
│   └── speech_to_text.py # 语音转文字
├── static/               # 静态资源
│   ├── css/style.css
│   └── js/
│       ├── main.js       # 主页面逻辑
│       ├── history.js    # 历史记录页
│       └── dashboard.js  # 仪表盘页
├── templates/            # HTML模板
│   ├── index.html        # 首页（分析页）
│   ├── history.html      # 历史记录页
│   └── dashboard.html    # 统计仪表盘
└── data/                 # 数据存储
    └── analysis.db       # SQLite数据库
```

## 使用指南

### 方式一：上传音频文件
1. 点击"选择文件"或拖放MP3文件到上传区域
2. 系统自动完成：上传 → 语音分离 → 文本转换 → AI分析
3. 查看分析结果，可导出PDF或文本报告

### 方式二：粘贴转录文本
1. 切换到"文本分析"标签
2. 粘贴飞书妙计或其他工具导出的转录文本
3. 点击"开始分析"
4. 获取AI分析结果

### 批量处理
1. 选择多个MP3文件上传
2. 文件会进入队列等待处理
3. 点击"开始批量处理"
4. 查看批量结果摘要，可导出批量报告

## 骑手评级说明

系统根据多维度评估将骑手分为：

| 等级 | 说明 | 跟进建议 |
|-----|------|---------|
| **A类** | 高意向、高稳定性 | 优先跟进，快速成交 |
| **B类** | 中等意向或稳定性 | 持续跟进，解决疑虑 |
| **C类** | 低意向或观望中 | 长期培育，定期触达 |

## 贡献指南

欢迎提交Issue和Pull Request！

## 许可证

MIT License

## 联系方式

如有问题或建议，欢迎联系：
- GitHub Issues: [提交问题](https://github.com/CUIJIE1992/rider_analyzer/issues)

---

🚀 **让AI助力你的电动车租赁业务，提升转化率！**
