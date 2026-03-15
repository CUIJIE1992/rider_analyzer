#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vercel Serverless Function Entry Point
购房意向智能分析系统 - Vercel部署入口
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入Flask应用
from app import app

# Vercel使用Flask应用实例作为入口
# 确保应用可以在Vercel环境中运行
if __name__ == "__main__":
    app.run(debug=True)
