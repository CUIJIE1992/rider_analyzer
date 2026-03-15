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

# Vercel Serverless Handler
from http.server import BaseHTTPRequestHandler
from io import BytesIO

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        with app.test_client() as client:
            response = client.get(self.path)
            self.wfile.write(response.data)
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        with app.test_client() as client:
            response = client.post(
                self.path,
                data=body,
                content_type=self.headers.get('Content-Type', 'application/json')
            )
            self.wfile.write(response.data)

# 导出Flask应用供Vercel使用
application = app
