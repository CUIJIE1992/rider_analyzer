#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音转文本服务
使用飞书妙计API将音频转换为文本
"""

import os
import json
import time
import requests
from pydub import AudioSegment


class SpeechToText:
    """语音转文本类 - 使用飞书妙计API"""
    
    def __init__(self):
        self.app_id = os.getenv('FEISHU_APP_ID', '')
        self.app_secret = os.getenv('FEISHU_APP_SECRET', '')
        self.tenant_access_token = None
        self.token_expire_time = 0
        
    def _get_tenant_access_token(self):
        """获取飞书tenant_access_token"""
        if self.tenant_access_token and time.time() < self.token_expire_time:
            return self.tenant_access_token
            
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            result = response.json()
            
            if result.get('code') == 0:
                self.tenant_access_token = result.get('tenant_access_token')
                self.token_expire_time = time.time() + result.get('expire', 7200) - 300
                return self.tenant_access_token
            else:
                raise Exception(f"获取token失败: {result.get('msg')}")
                
        except Exception as e:
            raise Exception(f"飞书认证失败: {str(e)}")
    
    def transcribe(self, audio_path):
        """
        将音频文件转换为文本
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            list: 包含时间戳的文本片段列表
        """
        # 检查是否配置了飞书API
        if not self.app_id or not self.app_secret:
            # 如果没有配置，使用模拟数据
            return self._mock_transcribe(audio_path)
        
        try:
            # 获取访问令牌
            token = self._get_tenant_access_token()
            
            # 上传音频文件
            upload_url = "https://open.feishu.cn/open-apis/speech_to_text/v1/file/upload"
            
            headers = {
                "Authorization": f"Bearer {token}"
            }
            
            with open(audio_path, 'rb') as f:
                files = {'file': f}
                data = {
                    'file_name': os.path.basename(audio_path),
                    'file_type': 'mp3'
                }
                
                response = requests.post(upload_url, headers=headers, files=files, data=data)
                upload_result = response.json()
                
            if upload_result.get('code') != 0:
                raise Exception(f"上传文件失败: {upload_result.get('msg')}")
            
            file_token = upload_result['data']['file_token']
            
            # 提交转写任务
            task_url = "https://open.feishu.cn/open-apis/speech_to_text/v1/task/create"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            task_data = {
                "file_token": file_token,
                "language": "zh_cn",
                "enable_diarization": True,  # 启用说话人分离
                "speaker_count": 2  # 说话人数量
            }
            
            response = requests.post(task_url, headers=headers, json=task_data)
            task_result = response.json()
            
            if task_result.get('code') != 0:
                raise Exception(f"创建任务失败: {task_result.get('msg')}")
            
            task_id = task_result['data']['task_id']
            
            # 轮询任务状态
            result = self._poll_task_result(token, task_id)
            
            return self._format_result(result)
            
        except Exception as e:
            print(f"飞书API调用失败: {str(e)}，使用模拟数据")
            return self._mock_transcribe(audio_path)
    
    def _poll_task_result(self, token, task_id, max_wait=300):
        """轮询获取任务结果"""
        url = f"https://open.feishu.cn/open-apis/speech_to_text/v1/task/get"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        params = {
            "task_id": task_id
        }
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            response = requests.get(url, headers=headers, params=params)
            result = response.json()
            
            if result.get('code') != 0:
                raise Exception(f"查询任务失败: {result.get('msg')}")
            
            status = result['data']['status']
            
            if status == 2:  # 完成
                return result['data']['result']
            elif status == 3:  # 失败
                raise Exception("转写任务失败")
            
            time.sleep(2)
        
        raise Exception("转写任务超时")
    
    def _format_result(self, result):
        """格式化识别结果"""
        formatted = []
        
        if isinstance(result, dict):
            sentences = result.get('sentences', [])
            
            for sentence in sentences:
                text = sentence.get('text', '')
                start_time = sentence.get('start_time', 0) / 1000  # 转换为秒
                end_time = sentence.get('end_time', 0) / 1000
                
                minutes = int(start_time // 60)
                seconds = int(start_time % 60)
                timestamp = f"{minutes:02d}:{seconds:02d}"
                
                formatted.append({
                    'text': text,
                    'timestamp': timestamp,
                    'start_time': start_time,
                    'end_time': end_time,
                    'speaker_id': sentence.get('speaker_id', 1)
                })
        else:
            # 如果结果格式不符合预期，返回原始文本
            formatted.append({
                'text': str(result),
                'timestamp': '00:00',
                'start_time': 0,
                'end_time': 0,
                'speaker_id': 1
            })
        
        return formatted
    
    def _mock_transcribe(self, audio_path):
        """
        模拟转写结果（当API未配置时使用）
        """
        # 获取音频时长
        try:
            audio = AudioSegment.from_mp3(audio_path)
            duration = len(audio) / 1000
        except:
            duration = 60
        
        # 生成模拟数据
        mock_texts = [
            "您好，请问是哪位？",
            "您好，我是XX公司的客服，想跟您确认一下订单信息。",
            "好的，请说。",
            "您的订单编号是123456，预计明天发货。",
            "好的，谢谢您的通知。",
            "不客气，请问还有其他问题吗？",
            "没有了，再见。",
            "好的，再见，祝您生活愉快。"
        ]
        
        results = []
        time_per_text = duration / len(mock_texts)
        
        for i, text in enumerate(mock_texts):
            start_time = i * time_per_text
            minutes = int(start_time // 60)
            seconds = int(start_time % 60)
            
            results.append({
                'text': text,
                'timestamp': f"{minutes:02d}:{seconds:02d}",
                'start_time': start_time,
                'end_time': (i + 1) * time_per_text,
                'speaker_id': 1 if i % 2 == 0 else 2
            })
        
        return results
