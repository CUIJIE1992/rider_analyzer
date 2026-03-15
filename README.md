# 通话录音智能分析系统

一个功能完整的网页应用，支持MP3通话录音上传、语音分离、文本转换和AI智能分析。

## 功能特性

### 1. 文件上传
- ✅ 支持拖放上传和点击选择
- ✅ 仅接受MP3格式文件
- ✅ 单文件最大50MB限制
- ✅ 实时文件预览

### 2. 语音处理
- ✅ 自动分离两个说话人的语音
- ✅ 基于音频特征的智能分类
- ✅ 支持长时间录音处理

### 3. 语音转文本
- ✅ 使用飞书妙计API进行语音识别
- ✅ 精确到秒级的时间戳
- ✅ 支持中文语音识别
- ✅ 自动说话人分离

### 4. AI智能分析
- ✅ 使用MiniMax API进行文本分析
- ✅ 通话主题提取
- ✅ 情感倾向分析
- ✅ 主要观点提取
- ✅ 争议点识别
- ✅ 关键信息提取
- ✅ 结论生成

### 5. 结果展示
- ✅ 清晰的双方对话区分
- ✅ 直观的分析结果展示
- ✅ 文本复制功能
- ✅ 结果下载功能

## 技术栈

- **后端**: Python Flask
- **前端**: HTML5, CSS3, JavaScript
- **语音处理**: pydub
- **语音识别**: 飞书妙计API
- **AI分析**: MiniMax API
- **UI设计**: 现代化响应式设计

## API接口说明

### 内部接口（4个）

1. **主页路由** `GET /`
   - 返回HTML页面

2. **文件上传** `POST /api/upload`
   - 上传MP3文件
   - 参数: `file` (MP3文件)
   - 返回: `{"success": true, "filename": "example.mp3"}`

3. **音频处理** `POST /api/process`
   - 处理音频文件（语音分离+转文本+AI分析）
   - 参数: `{"filename": "example.mp3"}`
   - 返回: 对话文本和AI分析结果

4. **文本分析** `POST /api/analyze`
   - 单独进行AI文本分析
   - 参数: `{"speaker1": "文本", "speaker2": "文本"}`
   - 返回: AI分析结果

### 外部API（2个）

1. **飞书妙计API** - 语音转文本
   - 支持说话人分离
   - 高精度中文识别
   - 时间戳精确到秒

2. **MiniMax API** - AI文本分析
   - 智能对话分析
   - 情感识别
   - 关键信息提取

## 安装步骤

### 1. 克隆项目
```bash
git clone <repository-url>
cd call_analyzer
```

### 2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 配置环境变量
```bash
cp .env.example .env
# 编辑.env文件，配置API密钥
```

### 5. 运行应用
```bash
python app.py
```

应用将在 `http://localhost:5000` 启动。

## 环境变量配置

```bash
# MiniMax API配置（必需）
MINIMAX_API_KEY=your-minimax-api-key
MINIMAX_GROUP_ID=your-group-id

# 飞书妙计API配置（可选）
FEISHU_APP_ID=your-app-id
FEISHU_APP_SECRET=your-app-secret

# 其他配置
SECRET_KEY=your-secret-key
MAX_FILE_SIZE=50
```

## 项目结构

```
call_analyzer/
├── app.py                   # 主应用文件
├── requirements.txt         # 依赖列表
├── .env.example            # 环境变量示例
├── README.md               # 项目说明
│
├── templates/              # 模板文件
│   └── index.html          # 主页面
│
├── static/                 # 静态文件
│   ├── css/
│   │   └── style.css       # 样式文件
│   └── js/
│       └── main.js         # 前端脚本
│
├── services/               # 服务模块
│   ├── audio_processor.py  # 音频处理
│   ├── speech_to_text.py   # 飞书妙计语音转文本
│   └── ai_analyzer.py      # MiniMax AI分析
│
├── routes/                 # 路由模块
│   └── api.py             # API路由
│
└── uploads/               # 上传文件目录
```

## 使用说明

### 1. 上传文件
- 访问主页
- 拖放MP3文件到上传区域，或点击选择文件
- 系统会自动验证文件格式和大小

### 2. 等待处理
- 系统自动进行语音分离
- 使用飞书妙计转换为文本
- 使用MiniMax进行AI智能分析

### 3. 查看结果
- 切换"对话文本"和"AI分析"标签页
- 查看分离后的双方对话
- 查看AI分析结果

### 4. 导出结果
- 点击"复制"按钮复制文本
- 点击"下载结果"保存完整报告

## 注意事项

1. **API密钥**: 
   - MiniMax API密钥已配置
   - 飞书妙计API可选（未配置时使用模拟数据）

2. **文件大小**: 建议文件大小不超过50MB

3. **语音质量**: 清晰的录音质量会提高识别准确率

4. **隐私保护**: 上传的文件仅用于处理，不会永久保存

## 故障排除

### 1. 文件上传失败
- 检查文件格式是否为MP3
- 确认文件大小不超过限制
- 检查网络连接

### 2. 语音识别失败
- 确认录音质量清晰
- 检查飞书API配置
- 系统会自动使用模拟数据

### 3. AI分析失败
- 检查MiniMax API密钥是否有效
- 确认API配额充足
- 检查网络连接

## 许可证

MIT License
