#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API路由模块
"""

import os
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename

api_bp = Blueprint('api', __name__)


@api_bp.route('/upload', methods=['POST'])
def upload():
    """文件上传API"""
    from app import allowed_file, app
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '没有选择文件'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': '没有选择文件'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        return jsonify({
            'success': True,
            'message': '文件上传成功',
            'filename': filename
        })
    
    return jsonify({'success': False, 'error': '不支持的文件格式'}), 400


@api_bp.route('/process', methods=['POST'])
def process():
    """处理音频API"""
    from services.audio_processor import AudioProcessor
    from services.speech_to_text import SpeechToText
    from services.ai_analyzer import AIAnalyzer
    from app import app
    
    data = request.json
    filename = data.get('filename')
    
    if not filename:
        return jsonify({'success': False, 'error': '缺少文件名'}), 400
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if not os.path.exists(filepath):
        return jsonify({'success': False, 'error': '文件不存在'}), 404
    
    try:
        # 音频处理
        processor = AudioProcessor(filepath)
        separated = processor.separate_speakers()
        
        # 语音转文本
        transcriber = SpeechToText()
        speaker1_text = transcriber.transcribe(separated['speaker1'])
        speaker2_text = transcriber.transcribe(separated['speaker2'])
        
        # AI分析
        analyzer = AIAnalyzer()
        analysis = analyzer.analyze_conversation(speaker1_text, speaker2_text)
        
        return jsonify({
            'success': True,
            'speaker1': speaker1_text,
            'speaker2': speaker2_text,
            'analysis': analysis
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/analyze', methods=['POST'])
def analyze():
    """文本分析API"""
    from services.ai_analyzer import AIAnalyzer
    
    data = request.json
    speaker1_text = data.get('speaker1', '')
    speaker2_text = data.get('speaker2', '')
    
    if not speaker1_text and not speaker2_text:
        return jsonify({'success': False, 'error': '缺少文本内容'}), 400
    
    try:
        analyzer = AIAnalyzer()
        result = analyzer.analyze_conversation(speaker1_text, speaker2_text)
        
        return jsonify({
            'success': True,
            'analysis': result
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
