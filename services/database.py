#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库服务模块
使用SQLite存储分析记录和标签统计
"""

import os
import json
import sqlite3
import logging
from datetime import datetime
from contextlib import contextmanager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'analysis.db')


def get_db_path():
    """获取数据库文件路径"""
    db_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
        logger.info(f"创建数据库目录: {db_dir}")
    return DB_PATH


@contextmanager
def get_connection():
    """获取数据库连接的上下文管理器"""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """初始化数据库，创建表结构"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                created_at TEXT NOT NULL,
                customer_grade TEXT,
                intention_level TEXT,
                purchase_stage TEXT,
                summary TEXT,
                analysis_data TEXT,
                tags TEXT,
                speaker1_data TEXT,
                speaker2_data TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_records_backup AS SELECT * FROM analysis_records WHERE 1=0
        ''')
        
        try:
            cursor.execute('PRAGMA table_info(analysis_records)')
            columns = [col[1] for col in cursor.fetchall()]
            if 'speaker1_data' not in columns:
                cursor.execute('ALTER TABLE analysis_records ADD COLUMN speaker1_data TEXT')
            if 'speaker2_data' not in columns:
                cursor.execute('ALTER TABLE analysis_records ADD COLUMN speaker2_data TEXT')
        except:
            pass
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customer_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag_name TEXT NOT NULL UNIQUE,
                count INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        logger.info("数据库初始化完成")


def save_record(record):
    """
    保存分析记录
    
    Args:
        record: dict 包含以下字段
            - filename: 文件名
            - customer_grade: 客户等级 (A/B/C)
            - intention_level: 意向强度 (高/中/低)
            - purchase_stage: 购房阶段
            - summary: 分析总结
            - analysis_data: 完整分析结果 (dict)
            - tags: 客户标签列表 (list)
            - speaker1_data: 说话人1对话文本 (list)
            - speaker2_data: 说话人2对话文本 (list)
    
    Returns:
        int: 新记录的ID
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        
        tags_str = ','.join(record.get('tags', [])) if isinstance(record.get('tags'), list) else record.get('tags', '')
        analysis_json = json.dumps(record.get('analysis_data', {}), ensure_ascii=False)
        speaker1_json = json.dumps(record.get('speaker1_data', []), ensure_ascii=False) if record.get('speaker1_data') else ''
        speaker2_json = json.dumps(record.get('speaker2_data', []), ensure_ascii=False) if record.get('speaker2_data') else ''
        
        cursor.execute('''
            INSERT INTO analysis_records 
            (filename, created_at, customer_grade, intention_level, purchase_stage, summary, analysis_data, tags, speaker1_data, speaker2_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            record.get('filename', ''),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            record.get('customer_grade', ''),
            record.get('intention_level', ''),
            record.get('purchase_stage', ''),
            record.get('summary', ''),
            analysis_json,
            tags_str,
            speaker1_json,
            speaker2_json
        ))
        
        record_id = cursor.lastrowid
        
        for tag in record.get('tags', []):
            if tag:
                update_tag_count(tag)
        
        conn.commit()
        logger.info(f"保存分析记录成功，ID: {record_id}")
        
        return record_id


def get_records(limit=20, offset=0):
    """
    获取记录列表
    
    Args:
        limit: 返回记录数量限制
        offset: 偏移量
    
    Returns:
        list: 记录列表
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM analysis_records 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        rows = cursor.fetchall()
        
        records = []
        for row in rows:
            record = dict(row)
            record['analysis_data'] = json.loads(record['analysis_data']) if record['analysis_data'] else {}
            record['tags'] = record['tags'].split(',') if record['tags'] else []
            records.append(record)
        
        return records


def get_record_by_id(record_id):
    """
    获取单条记录
    
    Args:
        record_id: 记录ID
    
    Returns:
        dict: 记录详情，不存在则返回None
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM analysis_records WHERE id = ?', (record_id,))
        
        row = cursor.fetchone()
        
        if row:
            record = dict(row)
            record['analysis_data'] = json.loads(record['analysis_data']) if record['analysis_data'] else {}
            record['tags'] = record['tags'].split(',') if record['tags'] else []
            record['speaker1_data'] = json.loads(record['speaker1_data']) if record.get('speaker1_data') else []
            record['speaker2_data'] = json.loads(record['speaker2_data']) if record.get('speaker2_data') else []
            return record
        
        return None


def delete_record(record_id):
    """
    删除记录
    
    Args:
        record_id: 记录ID
    
    Returns:
        bool: 删除成功返回True，记录不存在返回False
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('SELECT tags FROM analysis_records WHERE id = ?', (record_id,))
        row = cursor.fetchone()
        
        if not row:
            return False
        
        tags = row['tags'].split(',') if row['tags'] else []
        
        cursor.execute('DELETE FROM analysis_records WHERE id = ?', (record_id,))
        
        for tag in tags:
            if tag:
                cursor.execute('''
                    UPDATE customer_tags 
                    SET count = count - 1 
                    WHERE tag_name = ?
                ''', (tag,))
                cursor.execute('DELETE FROM customer_tags WHERE tag_name = ? AND count <= 0', (tag,))
        
        conn.commit()
        logger.info(f"删除记录成功，ID: {record_id}")
        
        return True


def search_records(keyword='', filters=None):
    """
    搜索筛选记录
    
    Args:
        keyword: 搜索关键词（匹配文件名、总结、标签）
        filters: dict 筛选条件
            - customer_grade: 客户等级
            - intention_level: 意向强度
            - purchase_stage: 购房阶段
            - start_date: 开始日期
            - end_date: 结束日期
    
    Returns:
        list: 匹配的记录列表
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        
        sql = 'SELECT * FROM analysis_records WHERE 1=1'
        params = []
        
        if keyword:
            sql += ''' AND (
                filename LIKE ? OR 
                summary LIKE ? OR 
                tags LIKE ?
            )'''
            keyword_param = f'%{keyword}%'
            params.extend([keyword_param, keyword_param, keyword_param])
        
        if filters:
            if filters.get('customer_grade'):
                sql += ' AND customer_grade = ?'
                params.append(filters['customer_grade'])
            
            if filters.get('intention_level'):
                sql += ' AND intention_level = ?'
                params.append(filters['intention_level'])
            
            if filters.get('purchase_stage'):
                sql += ' AND purchase_stage LIKE ?'
                params.append(f'%{filters["purchase_stage"]}%')
            
            if filters.get('start_date'):
                sql += ' AND created_at >= ?'
                params.append(filters['start_date'])
            
            if filters.get('end_date'):
                sql += ' AND created_at <= ?'
                params.append(filters['end_date'])
        
        sql += ' ORDER BY created_at DESC'
        
        cursor.execute(sql, params)
        
        rows = cursor.fetchall()
        
        records = []
        for row in rows:
            record = dict(row)
            record['analysis_data'] = json.loads(record['analysis_data']) if record['analysis_data'] else {}
            record['tags'] = record['tags'].split(',') if record['tags'] else []
            records.append(record)
        
        return records


def update_tag_count(tag):
    """
    更新标签计数
    
    Args:
        tag: 标签名
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO customer_tags (tag_name, count) 
            VALUES (?, 1)
            ON CONFLICT(tag_name) 
            DO UPDATE SET count = count + 1
        ''', (tag,))
        
        conn.commit()


def get_all_tags():
    """
    获取所有标签
    
    Returns:
        list: 标签列表，每项包含tag_name和count
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT tag_name, count 
            FROM customer_tags 
            WHERE count > 0
            ORDER BY count DESC, tag_name ASC
        ''')
        
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]


def get_records_count():
    """
    获取记录总数
    
    Returns:
        int: 记录总数
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM analysis_records')
        return cursor.fetchone()[0]


def get_statistics():
    """
    获取统计数据
    
    Returns:
        dict: 统计信息
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM analysis_records')
        total_records = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT customer_grade, COUNT(*) as count 
            FROM analysis_records 
            GROUP BY customer_grade
        ''')
        grade_distribution = {row['customer_grade']: row['count'] for row in cursor.fetchall()}
        
        cursor.execute('''
            SELECT intention_level, COUNT(*) as count 
            FROM analysis_records 
            GROUP BY intention_level
        ''')
        intention_distribution = {row['intention_level']: row['count'] for row in cursor.fetchall()}
        
        cursor.execute('SELECT COUNT(*) FROM customer_tags WHERE count > 0')
        total_tags = cursor.fetchone()[0]
        
        return {
            'total_records': total_records,
            'total_tags': total_tags,
            'grade_distribution': grade_distribution,
            'intention_distribution': intention_distribution
        }


init_db()
