#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通话录音分析应用主程序
"""

import os
import uuid
import json
import threading
import zipfile
import logging
import time
from io import BytesIO
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, url_for, send_file
from werkzeug.utils import secure_filename
from flask_cors import CORS
from dotenv import load_dotenv
from services import database

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

batch_processes = {}
batch_lock = threading.Lock()

# 批处理任务过期时间（秒）
BATCH_EXPIRE_SECONDS = 2 * 60 * 60  # 2小时
# 清理间隔（秒）
CLEANUP_INTERVAL_SECONDS = 5 * 60  # 5分钟

# 加载环境变量
load_dotenv()

# 创建Flask应用
app = Flask(__name__)
CORS(app)

# 配置
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'mp3'}
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def allowed_file(filename):
    """检查文件是否为允许的格式"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def _extract_field(data, primary_keys, sub_keys):
    """
    从嵌套字典中提取字段值,支持多种键名格式

    Args:
        data: 数据字典
        primary_keys: 主键列表,按优先级尝试
        sub_keys: 子键列表,按优先级尝试

    Returns:
        提取到的字段值,如果未找到则返回空字符串
    """
    for primary_key in primary_keys:
        if primary_key in data:
            value = data[primary_key]
            if isinstance(value, dict):
                for sub_key in sub_keys:
                    if sub_key in value:
                        return value[sub_key]
            else:
                return str(value)
    return ''


def _save_analysis_record(analysis_result, speaker1_text, speaker2_text, filename=None):
    """
    保存分析记录到数据库的公共函数

    Args:
        analysis_result: AI分析结果字典
        speaker1_text: 说话人1的文本
        speaker2_text: 说话人2的文本
        filename: 文件名,如果为None则自动生成时间戳文件名
    """
    try:
        from services.ai_analyzer import AIAnalyzer

        # 生成客户标签
        analyzer = AIAnalyzer()
        tags = analyzer.generate_customer_tags(analysis_result)

        # 统一的字段提取逻辑
        # 支持多种键名格式,优先使用新格式
        summary = _extract_field(analysis_result, ['总结', '通话概要'], ['summary', '核心内容'])
        customer_grade = _extract_field(analysis_result, ['客户评级'], ['grade', '综合等级'])
        intention_level = _extract_field(analysis_result, ['客户评级', '租赁意向'], ['租赁意向强度', 'intention'])
        purchase_stage = _extract_field(analysis_result, ['从业阶段'], ['stage', '当前阶段'])

        # 如果没有提供文件名,则自动生成
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            filename = f'文本分析_{timestamp}'
        else:
            # 提取原始文件名(去掉 file_id 前缀)
            if '_' in filename:
                parts = filename.split('_', 1)
                if len(parts) == 2 and len(parts[0]) == 36:  # UUID 长度为 36
                    filename = parts[1]

        record = {
            'filename': filename,
            'customer_grade': customer_grade,
            'intention_level': intention_level,
            'purchase_stage': purchase_stage,
            'summary': summary,
            'analysis_data': analysis_result,
            'tags': tags,
            'speaker1_data': speaker1_text,
            'speaker2_data': speaker2_text
        }

        database.save_record(record)
        logger.info(f'分析记录保存成功: {filename}')
    except Exception as e:
        logger.error(f'保存分析记录失败: {str(e)}')
        import traceback
        logger.error(traceback.format_exc())


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/history')
def history():
    """历史记录页面"""
    return render_template('history.html')


@app.route('/dashboard')
def dashboard():
    """统计仪表盘页面"""
    return render_template('dashboard.html')


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """处理文件上传，支持单文件和多文件上传"""
    if 'files' in request.files:
        files = request.files.getlist('files')
    elif 'file' in request.files:
        files = [request.files['file']]
    else:
        return jsonify({'error': '没有选择文件'}), 400
    
    if not files or all(f.filename == '' for f in files):
        return jsonify({'error': '没有选择文件'}), 400
    
    uploaded_files = []
    batch_id = str(uuid.uuid4())
    
    for file in files:
        if file and file.filename != '' and allowed_file(file.filename):
            file_id = str(uuid.uuid4())
            original_filename = secure_filename(file.filename)
            stored_filename = f"{file_id}_{original_filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], stored_filename)
            file.save(filepath)
            
            uploaded_files.append({
                'file_id': file_id,
                'original_filename': original_filename,
                'stored_filename': stored_filename,
                'filepath': filepath
            })
    
    if not uploaded_files:
        return jsonify({'error': '没有有效的文件被上传，请上传MP3文件'}), 400
    
    if len(uploaded_files) == 1:
        return jsonify({
            'success': True,
            'message': '文件上传成功',
            'filename': uploaded_files[0]['stored_filename'],
            'filepath': uploaded_files[0]['filepath'],
            'file_id': uploaded_files[0]['file_id']
        })
    
    return jsonify({
        'success': True,
        'message': f'成功上传 {len(uploaded_files)} 个文件',
        'batch_id': batch_id,
        'files': uploaded_files,
        'total': len(uploaded_files)
    })


@app.route('/api/process', methods=['POST'])
def process_audio():
    """处理音频文件"""
    from services.audio_processor import AudioProcessor
    from services.speech_to_text import SpeechToText
    from services.ai_analyzer import AIAnalyzer
    
    data = request.json
    filename = data.get('filename')
    
    if not filename:
        return jsonify({'error': '缺少文件名'}), 400
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if not os.path.exists(filepath):
        return jsonify({'error': '文件不存在'}), 404
    
    try:
        # 步骤1: 音频处理和语音分离
        processor = AudioProcessor(filepath)
        separated_audio = processor.separate_speakers()
        
        # 获取音频真实时长
        audio_info = processor.get_audio_info()
        audio_duration = audio_info.get('duration', 0)
        
        # 步骤2: 语音转文本
        transcriber = SpeechToText()
        speaker1_text = transcriber.transcribe(separated_audio['speaker1'])
        speaker2_text = transcriber.transcribe(separated_audio['speaker2'])
        
        # 步骤3: AI分析（传入真实时长）
        analyzer = AIAnalyzer()
        analysis_result = analyzer.analyze_conversation(speaker1_text, speaker2_text, audio_duration=audio_duration)

        # 保存分析记录到数据库
        _save_analysis_record(analysis_result, speaker1_text, speaker2_text, filename)

        return jsonify({
            'success': True,
            'speaker1': speaker1_text,
            'speaker2': speaker2_text,
            'analysis': analysis_result
        })
        
    except Exception as e:
        return jsonify({'error': f'处理失败: {str(e)}'}), 500


def process_single_file(file_info, batch_id, file_index):
    """处理单个文件的函数，用于后台线程"""
    from services.audio_processor import AudioProcessor
    from services.speech_to_text import SpeechToText
    from services.ai_analyzer import AIAnalyzer
    
    filepath = file_info['filepath']
    file_id = file_info['file_id']
    original_filename = file_info['original_filename']
    
    result = {
        'file_id': file_id,
        'original_filename': original_filename,
        'status': 'processing',
        'error': None,
        'speaker1': None,
        'speaker2': None,
        'analysis': None
    }
    
    try:
        processor = AudioProcessor(filepath)
        separated_audio = processor.separate_speakers()
        
        transcriber = SpeechToText()
        speaker1_text = transcriber.transcribe(separated_audio['speaker1'])
        speaker2_text = transcriber.transcribe(separated_audio['speaker2'])
        
        analyzer = AIAnalyzer()
        analysis_result = analyzer.analyze_conversation(speaker1_text, speaker2_text)
        
        result['speaker1'] = speaker1_text
        result['speaker2'] = speaker2_text
        result['analysis'] = analysis_result
        result['status'] = 'completed'

        # 保存分析记录到数据库
        _save_analysis_record(analysis_result, speaker1_text, speaker2_text, original_filename)

    except Exception as e:
        result['status'] = 'failed'
        result['error'] = str(e)
    
    with batch_lock:
        if batch_id in batch_processes:
            batch_processes[batch_id]['results'][file_index] = result
            batch_processes[batch_id]['completed'] += 1
            if batch_processes[batch_id]['completed'] >= batch_processes[batch_id]['total']:
                batch_processes[batch_id]['status'] = 'completed'
    
    return result


def cleanup_old_batches():
    """清理过期的批处理任务"""
    while True:
        try:
            current_time = datetime.now()
            expired_batches = []
            
            with batch_lock:
                # 查找过期的任务
                for batch_id, batch_info in batch_processes.items():
                    created_at = datetime.fromisoformat(batch_info['created_at'])
                    age_seconds = (current_time - created_at).total_seconds()
                    
                    # 只清理已完成且超过过期时间的任务
                    if batch_info['status'] == 'completed' and age_seconds > BATCH_EXPIRE_SECONDS:
                        expired_batches.append(batch_id)
                
                # 删除过期任务
                for batch_id in expired_batches:
                    del batch_processes[batch_id]
                    logger.info(f"已清理过期批处理任务: {batch_id}")
            
            if expired_batches:
                logger.info(f"清理了 {len(expired_batches)} 个过期批处理任务")
                
        except Exception as e:
            logger.error(f"清理批处理任务时出错: {str(e)}")
        
        # 等待下一次清理
        time.sleep(CLEANUP_INTERVAL_SECONDS)


def start_cleanup_thread():
    """启动后台清理线程"""
    cleanup_thread = threading.Thread(
        target=cleanup_old_batches,
        daemon=True
    )
    cleanup_thread.start()
    logger.info("批处理任务清理线程已启动")


@app.route('/api/batch-process', methods=['POST'])
def batch_process():
    """批量处理文件接口"""
    data = request.json
    batch_id = data.get('batch_id')
    file_ids = data.get('file_ids', [])
    files_info = data.get('files', [])
    
    if not files_info:
        return jsonify({'error': '缺少文件信息'}), 400
    
    if not batch_id:
        batch_id = str(uuid.uuid4())
    
    with batch_lock:
        batch_processes[batch_id] = {
            'status': 'processing',
            'total': len(files_info),
            'completed': 0,
            'results': [None] * len(files_info),
            'files_info': files_info,
            'created_at': datetime.now().isoformat()
        }
    
    for index, file_info in enumerate(files_info):
        thread = threading.Thread(
            target=process_single_file,
            args=(file_info, batch_id, index)
        )
        thread.daemon = True
        thread.start()
    
    return jsonify({
        'success': True,
        'batch_id': batch_id,
        'status': 'processing',
        'total': len(files_info)
    })


@app.route('/api/batch-status/<batch_id>', methods=['GET'])
def get_batch_status(batch_id):
    """获取批量处理状态"""
    with batch_lock:
        if batch_id not in batch_processes:
            return jsonify({'error': '批量任务不存在'}), 404
        
        batch_info = batch_processes[batch_id].copy()
    
    return jsonify({
        'batch_id': batch_id,
        'status': batch_info['status'],
        'total': batch_info['total'],
        'completed': batch_info['completed'],
        'progress': round(batch_info['completed'] / batch_info['total'] * 100, 1) if batch_info['total'] > 0 else 0,
        'results': batch_info['results']
    })


@app.route('/api/batch-export/<batch_id>', methods=['GET'])
def batch_export(batch_id):
    """批量导出分析结果为ZIP文件"""
    from services.pdf_generator import generate_pdf_report
    
    with batch_lock:
        if batch_id not in batch_processes:
            return jsonify({'error': '批量任务不存在'}), 404
        
        batch_info = batch_processes[batch_id].copy()
    
    if batch_info['status'] != 'completed':
        return jsonify({'error': '批量任务尚未完成'}), 400
    
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for index, result in enumerate(batch_info['results']):
            if result and result['status'] == 'completed':
                try:
                    pdf_content = generate_pdf_report(
                        result['analysis'],
                        result['speaker1'],
                        result['speaker2']
                    )
                    
                    safe_filename = ''.join(c if c.isalnum() or c in ('_', '-') else '_' for c in result['original_filename'])
                    pdf_filename = f"{safe_filename}_报告.pdf"
                    
                    zipf.writestr(pdf_filename, pdf_content)
                except Exception as e:
                    error_filename = f"error_{index}.txt"
                    zipf.writestr(error_filename, f"生成PDF失败: {str(e)}")
        
        summary_content = f"批量处理报告\n"
        summary_content += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        summary_content += f"总文件数: {batch_info['total']}\n"
        summary_content += f"成功处理: {sum(1 for r in batch_info['results'] if r and r['status'] == 'completed')}\n"
        summary_content += f"处理失败: {sum(1 for r in batch_info['results'] if r and r['status'] == 'failed')}\n"
        
        zipf.writestr("处理摘要.txt", summary_content)
    
    zip_buffer.seek(0)
    
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'批量分析报告_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
    )


@app.route('/api/analyze', methods=['POST'])
def analyze_text():
    """分析文本内容"""
    from services.ai_analyzer import AIAnalyzer
    
    data = request.json
    speaker1_text = data.get('speaker1', '')
    speaker2_text = data.get('speaker2', '')
    
    if not speaker1_text and not speaker2_text:
        return jsonify({'error': '缺少文本内容'}), 400
    
    try:
        analyzer = AIAnalyzer()
        result = analyzer.analyze_conversation(speaker1_text, speaker2_text)
        
        return jsonify({
            'success': True,
            'analysis': result
        })
        
    except Exception as e:
        return jsonify({'error': f'分析失败: {str(e)}'}), 500


@app.route('/api/analyze-transcript', methods=['POST'])
def analyze_transcript():
    """直接分析转录文本（跳过语音转文本步骤）"""
    from services.ai_analyzer import AIAnalyzer
    
    data = request.json
    transcript = data.get('transcript', '')
    
    if not transcript:
        return jsonify({'error': '缺少转录文本'}), 400
    
    try:
        # 解析转录文本，分离两个说话人
        speaker1_text, speaker2_text = parse_transcript(transcript)
        
        # AI分析
        analyzer = AIAnalyzer()
        result = analyzer.analyze_conversation(speaker1_text, speaker2_text)

        # 保存分析记录到数据库
        _save_analysis_record(result, speaker1_text, speaker2_text)

        return jsonify({
            'success': True,
            'speaker1': speaker1_text,
            'speaker2': speaker2_text,
            'analysis': result
        })
        
    except Exception as e:
        return jsonify({'error': f'分析失败: {str(e)}'}), 500


def parse_transcript(transcript):
    """解析转录文本，分离两个说话人"""
    import re
    
    speaker1_texts = []
    speaker2_texts = []
    
    lines = transcript.strip().split('\n')
    
    current_speaker = None
    current_text = []
    
    for line in lines:
        line = line.strip()
        if not line:
            if current_speaker and current_text:
                text = ' '.join(current_text)
                if current_speaker == 1:
                    speaker1_texts.append({
                        'text': text,
                        'timestamp': '00:00'
                    })
                else:
                    speaker2_texts.append({
                        'text': text,
                        'timestamp': '00:00'
                    })
                current_text = []
            continue
        
        match = re.match(r'说话人\s*(\d+)\s+\d+:\d+', line)
        if match:
            if current_speaker and current_text:
                text = ' '.join(current_text)
                if current_speaker == 1:
                    speaker1_texts.append({
                        'text': text,
                        'timestamp': '00:00'
                    })
                else:
                    speaker2_texts.append({
                        'text': text,
                        'timestamp': '00:00'
                    })
            
            current_speaker = int(match.group(1))
            current_text = []
        else:
            if current_speaker:
                current_text.append(line)
    
    if current_speaker and current_text:
        text = ' '.join(current_text)
        if current_speaker == 1:
            speaker1_texts.append({
                'text': text,
                'timestamp': '00:00'
            })
        else:
            speaker2_texts.append({
                'text': text,
                'timestamp': '00:00'
            })
    
    return speaker1_texts, speaker2_texts


@app.route('/api/export-pdf', methods=['POST'])
def export_pdf():
    """导出PDF报告"""
    from services.pdf_generator import generate_pdf_report
    from io import BytesIO
    
    data = request.json
    analysis = data.get('analysis', {})
    speaker1 = data.get('speaker1', [])
    speaker2 = data.get('speaker2', [])
    
    if not analysis:
        return jsonify({'error': '缺少分析结果'}), 400
    
    try:
        pdf_content = generate_pdf_report(analysis, speaker1, speaker2)
        
        pdf_buffer = BytesIO(pdf_content)
        pdf_buffer.seek(0)
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'骑手租赁分析报告_{datetime.now().strftime("%Y-%m-%d")}.pdf'
        )
        
    except Exception as e:
        return jsonify({'error': f'PDF生成失败: {str(e)}'}), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    """获取历史记录列表"""
    try:
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        records = database.get_records(limit=limit, offset=offset)
        total = database.get_records_count()
        
        return jsonify({
            'records': records,
            'total': total,
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        return jsonify({'error': f'获取历史记录失败: {str(e)}'}), 500


@app.route('/api/history/<int:id>', methods=['GET'])
def get_history_detail(id):
    """获取单条记录详情"""
    try:
        record = database.get_record_by_id(id)
        
        if not record:
            return jsonify({'error': '记录不存在'}), 404
        
        return jsonify(record)
        
    except Exception as e:
        return jsonify({'error': f'获取记录详情失败: {str(e)}'}), 500


@app.route('/api/history/<int:id>', methods=['DELETE'])
def delete_history(id):
    """删除记录"""
    try:
        success = database.delete_record(id)
        
        if not success:
            return jsonify({'error': '记录不存在'}), 404
        
        return jsonify({
            'success': True,
            'message': '记录删除成功'
        })
        
    except Exception as e:
        return jsonify({'error': f'删除记录失败: {str(e)}'}), 500


@app.route('/api/history/search', methods=['POST'])
def search_history():
    """搜索筛选记录"""
    try:
        data = request.json or {}
        
        keyword = data.get('keyword', '')
        
        filters = {}
        if data.get('grade'):
            filters['customer_grade'] = data['grade']
        if data.get('intention'):
            filters['intention_level'] = data['intention']
        if data.get('start_date'):
            filters['start_date'] = data['start_date']
        if data.get('end_date'):
            filters['end_date'] = data['end_date']
        
        records = database.search_records(keyword=keyword, filters=filters)
        
        return jsonify({
            'records': records,
            'total': len(records)
        })
        
    except Exception as e:
        return jsonify({'error': f'搜索失败: {str(e)}'}), 500


@app.route('/api/history/compare', methods=['GET'])
def compare_history():
    """对比多条记录"""
    try:
        ids_param = request.args.get('ids', '')
        
        if not ids_param:
            return jsonify({'error': '缺少记录ID'}), 400
        
        try:
            ids = [int(id.strip()) for id in ids_param.split(',') if id.strip()]
        except ValueError:
            return jsonify({'error': '无效的ID格式'}), 400
        
        if len(ids) < 2:
            return jsonify({'error': '至少需要选择2条记录进行对比'}), 400
        
        records = []
        for record_id in ids:
            record = database.get_record_by_id(record_id)
            if record:
                records.append(record)
        
        if len(records) < 2:
            return jsonify({'error': '找到的有效记录不足2条'}), 404
        
        comparison = {
            'grade_distribution': {},
            'intention_distribution': {},
            'stage_distribution': {},
            'common_tags': [],
            'all_tags': set()
        }
        
        all_tags_sets = []
        
        for record in records:
            grade = record.get('customer_grade', '未知')
            comparison['grade_distribution'][grade] = comparison['grade_distribution'].get(grade, 0) + 1
            
            intention = record.get('intention_level', '未知')
            comparison['intention_distribution'][intention] = comparison['intention_distribution'].get(intention, 0) + 1
            
            stage = record.get('purchase_stage', '未知')
            comparison['stage_distribution'][stage] = comparison['stage_distribution'].get(stage, 0) + 1
            
            tags = record.get('tags', [])
            all_tags_sets.append(set(tags))
            comparison['all_tags'].update(tags)
        
        if all_tags_sets:
            comparison['common_tags'] = list(set.intersection(*all_tags_sets))
        
        comparison['all_tags'] = list(comparison['all_tags'])
        
        return jsonify({
            'records': records,
            'comparison': comparison
        })
        
    except Exception as e:
        return jsonify({'error': f'对比失败: {str(e)}'}), 500


@app.route('/api/dashboard/stats')
def get_dashboard_stats():
    """获取统计卡片数据"""
    try:
        # 获取日期筛选参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 转换日期格式（添加时间部分）
        if start_date:
            start_date = f"{start_date} 00:00:00"
        if end_date:
            end_date = f"{end_date} 23:59:59"
        
        stats = database.get_statistics(start_date=start_date, end_date=end_date)
        
        with database.get_connection() as conn:
            cursor = conn.cursor()
            
            # 构建WHERE条件
            where_clause = ''
            params = []
            if start_date:
                where_clause += ' WHERE created_at >= ?'
                params.append(start_date)
            if end_date:
                if where_clause:
                    where_clause += ' AND created_at <= ?'
                else:
                    where_clause += ' WHERE created_at <= ?'
                params.append(end_date)
            
            # 计算本周新增（如果有过滤条件，则计算过滤范围内的数量）
            if start_date or end_date:
                cursor.execute(
                    f'SELECT COUNT(*) FROM analysis_records{where_clause}',
                    params
                )
                this_week_new = cursor.fetchone()[0]
            else:
                week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute(
                    'SELECT COUNT(*) FROM analysis_records WHERE created_at >= ?',
                    (week_ago,)
                )
                this_week_new = cursor.fetchone()[0]
            
            cursor.execute(f'''
                SELECT intention_level, COUNT(*) as count 
                FROM analysis_records 
                {where_clause}
                AND intention_level IS NOT NULL AND intention_level != ''
                GROUP BY intention_level
            ''', params)
            intention_data = {row['intention_level']: row['count'] for row in cursor.fetchall()}
            
            total_intention = sum(intention_data.values())
            avg_intention = 0
            if total_intention > 0:
                high_score = intention_data.get('高', 0) * 3
                medium_score = intention_data.get('中', 0) * 2
                low_score = intention_data.get('低', 0) * 1
                avg_intention = round((high_score + medium_score + low_score) / total_intention, 2)
        
        grade_dist = stats.get('grade_distribution', {})
        
        # 计算A类客户数量
        class_a_count = grade_dist.get('A类', 0) + grade_dist.get('A', 0)
        
        # 将意向强度转换为百分制分数 (1-3分映射到40-100分)
        avg_score = min(100, max(40, avg_intention * 33.33)) if avg_intention > 0 else 0
        
        return jsonify({
            'total_analysis': stats.get('total_records', 0),
            'weekly_new': this_week_new,
            'avg_score': round(avg_score, 1),
            'class_a_count': class_a_count,
            'grade_distribution': {
                'A类': class_a_count,
                'B类': grade_dist.get('B类', 0) + grade_dist.get('B', 0),
                'C类': grade_dist.get('C类', 0) + grade_dist.get('C', 0)
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'获取统计数据失败: {str(e)}'}), 500


@app.route('/api/dashboard/grade-distribution')
def get_grade_distribution():
    """客户等级分布"""
    try:
        # 获取日期筛选参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 转换日期格式
        if start_date:
            start_date = f"{start_date} 00:00:00"
        if end_date:
            end_date = f"{end_date} 23:59:59"
        
        stats = database.get_statistics(start_date=start_date, end_date=end_date)
        grade_dist = stats.get('grade_distribution', {})
        
        return jsonify({
            'labels': ['A类', 'B类', 'C类'],
            'data': [
                grade_dist.get('A类', 0) + grade_dist.get('A', 0),
                grade_dist.get('B类', 0) + grade_dist.get('B', 0),
                grade_dist.get('C类', 0) + grade_dist.get('C', 0)
            ]
        })
        
    except Exception as e:
        return jsonify({'error': f'获取等级分布失败: {str(e)}'}), 500


@app.route('/api/dashboard/intention-trend')
def get_intention_trend():
    """意向趋势数据"""
    try:
        # 获取日期筛选参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        with database.get_connection() as conn:
            cursor = conn.cursor()
            
            labels = []
            high_data = []
            medium_data = []
            low_data = []
            
            # 如果有日期筛选参数，使用筛选范围内的日期
            if start_date and end_date:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                days = (end_dt - start_dt).days + 1
                
                for i in range(days):
                    current_date = start_dt + timedelta(days=i)
                    date_str = current_date.strftime('%Y-%m-%d')
                    labels.append(current_date.strftime('%m-%d'))
                    
                    cursor.execute('''
                        SELECT intention_level, COUNT(*) as count 
                        FROM analysis_records 
                        WHERE DATE(created_at) = ?
                        GROUP BY intention_level
                    ''', (date_str,))
                    
                    day_data = {row['intention_level']: row['count'] for row in cursor.fetchall()}
                    high_data.append(day_data.get('高', 0))
                    medium_data.append(day_data.get('中', 0))
                    low_data.append(day_data.get('低', 0))
            else:
                # 默认显示最近30天
                days = request.args.get('days', default=30, type=int)
                
                for i in range(days - 1, -1, -1):
                    date = datetime.now() - timedelta(days=i)
                    date_str = date.strftime('%Y-%m-%d')
                    labels.append(date.strftime('%m-%d'))
                    
                    cursor.execute('''
                        SELECT intention_level, COUNT(*) as count 
                        FROM analysis_records 
                        WHERE DATE(created_at) = ?
                        GROUP BY intention_level
                    ''', (date_str,))
                    
                    day_data = {row['intention_level']: row['count'] for row in cursor.fetchall()}
                    high_data.append(day_data.get('高', 0))
                    medium_data.append(day_data.get('中', 0))
                    low_data.append(day_data.get('低', 0))
            
            return jsonify({
                'labels': labels,
                'high': high_data,
                'medium': medium_data,
                'low': low_data
            })
            
    except Exception as e:
        return jsonify({'error': f'获取意向趋势失败: {str(e)}'}), 500


@app.route('/api/dashboard/concerns-ranking')
def get_concerns_ranking():
    """关注点排行"""
    try:
        # 获取日期筛选参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 转换日期格式
        if start_date:
            start_date = f"{start_date} 00:00:00"
        if end_date:
            end_date = f"{end_date} 23:59:59"
        
        tags = database.get_tags_with_date_filter(start_date=start_date, end_date=end_date)
        
        labels = [tag['tag_name'] for tag in tags[:10]]
        data = [tag['count'] for tag in tags[:10]]
        
        return jsonify({
            'labels': labels,
            'data': data
        })
        
    except Exception as e:
        return jsonify({'error': f'获取关注点排行失败: {str(e)}'}), 500


# 启动清理线程（在应用启动时执行）
start_cleanup_thread()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
