# Vercel部署指南

## 概述
本文档详细介绍如何将购房意向智能分析系统部署到Vercel平台。

## 前置要求

1. GitHub账号
2. Vercel账号（可使用GitHub账号登录）
3. 项目代码已推送到GitHub仓库

## 部署步骤

### 1. 准备工作

确保您的GitHub仓库包含以下文件：
- `vercel.json` - Vercel配置文件
- `package.json` - Node.js配置文件
- `api/index.py` - Vercel入口文件
- `requirements.txt` - Python依赖
- `.env.vercel.example` - 环境变量示例

### 2. 导入项目到Vercel

1. 访问 [Vercel Dashboard](https://vercel.com/dashboard)
2. 点击 **Add New Project**
3. 选择 **Import Git Repository**
4. 找到并选择 `call_analyzer` 仓库
5. 点击 **Import**

### 3. 配置项目

在配置页面中：

#### Framework Preset
- 选择 **Other**

#### Build and Output Settings
- Build Command: `pip install -r requirements.txt`
- Output Directory: 留空
- Install Command: 留空

#### Environment Variables
添加以下环境变量：

| 变量名 | 说明 | 必需 |
|--------|------|------|
| `MINIMAX_API_KEY` | MiniMax API密钥 | ✅ |
| `MINIMAX_GROUP_ID` | MiniMax Group ID | ✅ |
| `FEISHU_APP_ID` | 飞书应用ID | ❌ |
| `FEISHU_APP_SECRET` | 飞书应用密钥 | ❌ |
| `SECRET_KEY` | Flask密钥 | ✅ |
| `VERCEL` | 设置为 `1` | ✅ |

点击 **Deploy** 开始部署。

### 4. 等待部署完成

部署过程通常需要2-5分钟。完成后，Vercel会提供一个域名（如 `https://call-analyzer.vercel.app`）。

## 项目结构说明

```
call_analyzer/
├── api/
│   ├── __init__.py
│   └── index.py          # Vercel Serverless入口
├── services/
│   ├── __init__.py
│   ├── ai_analyzer.py
│   ├── audio_processor.py
│   ├── database.py       # 已适配Vercel环境
│   ├── pdf_generator.py
│   └── speech_to_text.py
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── dashboard.js
│       ├── history.js
│       └── main.js
├── templates/
│   ├── dashboard.html
│   ├── history.html
│   └── index.html
├── app.py                # 已适配Vercel环境
├── vercel.json           # Vercel配置
├── package.json          # Node.js配置
├── requirements.txt      # Python依赖
├── .env.vercel.example   # 环境变量示例
└── VERCEL_DEPLOY.md      # 本文件
```

## 关键配置说明

### vercel.json
```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/static/(.*)",
      "dest": "/static/$1"
    },
    {
      "src": "/api/(.*)",
      "dest": "/api/index.py"
    },
    {
      "src": "/(.*)",
      "dest": "/api/index.py"
    }
  ]
}
```

### 环境适配修改

1. **上传目录适配** (`app.py`):
   ```python
   app.config['UPLOAD_FOLDER'] = '/tmp/uploads' if os.environ.get('VERCEL') else 'uploads'
   ```

2. **数据库路径适配** (`services/database.py`):
   ```python
   if os.environ.get('VERCEL'):
       DB_PATH = '/tmp/analysis.db'
   else:
       DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'analysis.db')
   ```

## 验证部署

### 1. 访问首页
打开部署后的域名，确认页面正常显示。

### 2. 测试文件上传
- 上传一个MP3文件
- 确认文件上传成功

### 3. 测试文本分析
- 切换到文本分析模式
- 粘贴测试文本
- 点击开始分析
- 确认AI分析正常返回结果

### 4. 测试历史记录
- 访问 `/history` 页面
- 确认历史记录列表正常显示

### 5. 测试统计仪表盘
- 访问 `/dashboard` 页面
- 确认图表正常显示

## 常见问题

### 1. 文件上传失败
**原因**: Vercel Serverless Functions有请求大小限制（默认4.5MB）
**解决**: 
- 在 `vercel.json` 中配置 `maxLambdaSize`
- 或者限制上传文件大小

### 2. 数据库数据丢失
**原因**: Vercel的/tmp目录在每次部署后会被清空
**解决**: 
- 使用外部数据库服务（如Supabase、PlanetScale）
- 或者定期备份数据

### 3. API请求超时
**原因**: Vercel Serverless Functions有执行时间限制（默认10秒）
**解决**: 
- 对于长时间处理的任务，使用异步处理
- 或者升级到Vercel Pro计划（60秒限制）

### 4. 静态文件404
**原因**: 路由配置不正确
**解决**: 检查 `vercel.json` 中的路由配置

## 性能优化建议

1. **启用缓存**: 在Vercel Dashboard中配置缓存策略
2. **使用CDN**: Vercel自动提供全球CDN加速
3. **压缩资源**: 确保静态文件已压缩
4. **图片优化**: 使用Vercel的图片优化功能

## 更新部署

当代码更新后，Vercel会自动重新部署：

1. 推送代码到GitHub
2. Vercel自动检测到变更
3. 自动重新构建和部署

或者手动在Vercel Dashboard中点击 **Redeploy**。

## 自定义域名

1. 在Vercel Dashboard中选择项目
2. 点击 **Settings** → **Domains**
3. 添加您的自定义域名
4. 按照提示配置DNS记录

## 监控和日志

1. 在Vercel Dashboard中查看 **Analytics**
2. 查看 **Logs** 了解应用运行状态
3. 设置 **Alerts** 监控异常

## 支持

如有问题，请查看：
- [Vercel文档](https://vercel.com/docs)
- [Flask on Vercel指南](https://vercel.com/docs/concepts/functions/serverless-functions/runtimes/python)
- 项目GitHub Issues
