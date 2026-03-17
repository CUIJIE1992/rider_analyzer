#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF报告生成服务 - 使用ReportLab
"""

import os
from datetime import datetime
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

def get_chinese_font():
    """获取中文字体"""
    font_paths = [
        'C:/Windows/Fonts/msyh.ttc',
        'C:/Windows/Fonts/simhei.ttf',
        'C:/Windows/Fonts/simsun.ttc',
    ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            return font_path
    
    return None

def register_chinese_font():
    """注册中文字体"""
    font_path = get_chinese_font()
    if font_path:
        try:
            pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
            return 'ChineseFont'
        except:
            pass
    return 'Helvetica'

def create_styles(font_name):
    """创建样式"""
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(
        name='ChineseTitle',
        fontName=font_name,
        fontSize=24,
        leading=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=10
    ))
    
    styles.add(ParagraphStyle(
        name='ChineseSubtitle',
        fontName=font_name,
        fontSize=12,
        leading=16,
        alignment=TA_CENTER,
        textColor=colors.gray,
        spaceAfter=5
    ))
    
    styles.add(ParagraphStyle(
        name='ChineseSectionTitle',
        fontName=font_name,
        fontSize=14,
        leading=20,
        textColor=colors.white,
        spaceBefore=15,
        spaceAfter=10
    ))
    
    styles.add(ParagraphStyle(
        name='ChineseBody',
        fontName=font_name,
        fontSize=10,
        leading=16,
        alignment=TA_JUSTIFY,
        spaceAfter=8
    ))
    
    styles.add(ParagraphStyle(
        name='ChineseLabel',
        fontName=font_name,
        fontSize=9,
        leading=14,
        textColor=colors.gray
    ))
    
    styles.add(ParagraphStyle(
        name='ChineseValue',
        fontName=font_name,
        fontSize=11,
        leading=16,
        textColor=colors.HexColor('#333333')
    ))
    
    styles.add(ParagraphStyle(
        name='ChineseSummary',
        fontName=font_name,
        fontSize=11,
        leading=18,
        alignment=TA_JUSTIFY,
        backColor=colors.HexColor('#fef3c7'),
        borderPadding=10
    ))
    
    styles.add(ParagraphStyle(
        name='ChatBubble1',
        fontName=font_name,
        fontSize=10,
        leading=14,
        textColor=colors.black,
        backColor=colors.HexColor('#95ec69'),
        borderPadding=8
    ))
    
    styles.add(ParagraphStyle(
        name='ChatBubble2',
        fontName=font_name,
        fontSize=10,
        leading=14,
        textColor=colors.black,
        backColor=colors.HexColor('#f5f5f5'),
        borderPadding=8
    ))
    
    return styles

def create_section_table(title, content, styles):
    """创建带标题的内容区块"""
    data = [[Paragraph(title, styles['ChineseSectionTitle'])]]
    
    section_table = Table(data, colWidths=[180*mm])
    section_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ('ROUNDEDCORNERS', [5, 5, 5, 5]),
    ]))
    
    return section_table

def generate_pdf_report(analysis, speaker1=None, speaker2=None):
    """
    生成PDF报告
    
    Args:
        analysis: 分析结果字典
        speaker1: 说话人1的对话列表
        speaker2: 说话人2的对话列表
    
    Returns:
        bytes: PDF文件内容
    """
    buffer = BytesIO()
    
    font_name = register_chinese_font()
    styles = create_styles(font_name)
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
    )
    
    story = []
    
    # 标题
    story.append(Paragraph("🛵 骑手电瓶车租赁分析报告", styles['ChineseTitle']))
    story.append(Paragraph("AI驱动的电瓶车租赁业务洞察与骑手跟进策略", styles['ChineseSubtitle']))
    story.append(Paragraph(f"生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M')}", styles['ChineseSubtitle']))
    story.append(Spacer(1, 20))
    
    # 通话概要
    if analysis.get('通话概要'):
        story.append(create_section_table("📊 通话概要", "", styles))
        story.append(Spacer(1, 5))
        
        overview = analysis['通话概要']
        overview_data = [
            ['通话时长', '有效沟通程度', '骑手响应积极性'],
            [
                overview.get('通话时长估算', '-'),
                overview.get('有效沟通程度', '-'),
                overview.get('骑手响应积极性', '-')
            ]
        ]
        
        overview_table = Table(overview_data, colWidths=[60*mm, 60*mm, 60*mm])
        overview_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f0f0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.gray),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0')),
        ]))
        story.append(overview_table)
        story.append(Spacer(1, 15))
    
    # 客户评级
    if analysis.get('客户评级'):
        story.append(create_section_table("🏆 骑手评级", "", styles))
        story.append(Spacer(1, 5))
        
        rating = analysis['客户评级']
        
        rating_items = [
            f"🎯 租赁意向强度：{rating.get('租赁意向强度', '-')}",
            f"� 从业稳定性：{rating.get('从业稳定性', '-')}",
            f"⏱️ 决策周期：{rating.get('决策周期', '-')}",
            f"🏆 综合评级：{rating.get('综合等级', '-')}"
        ]
        
        for item in rating_items:
            story.append(Paragraph(item, styles['ChineseBody']))
        
        story.append(Paragraph(f"<b>评级说明：</b>{rating.get('等级说明', '-')}", styles['ChineseBody']))
        story.append(Spacer(1, 15))
    
    # 租赁意向
    if analysis.get('租赁意向'):
        story.append(create_section_table("🛵 租赁意向分析", "", styles))
        story.append(Spacer(1, 5))
        
        intention = analysis['租赁意向']
        intention_data = [
            ['车型需求', '预算范围', '区域偏好', '租期需求'],
            [
                intention.get('车型需求', '未提及'),
                intention.get('预算范围', '未提及'),
                intention.get('区域偏好', '未提及'),
                intention.get('租期需求', '未提及')
            ]
        ]
        
        intention_table = Table(intention_data, colWidths=[45*mm, 45*mm, 45*mm, 45*mm])
        intention_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f0f0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.gray),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0')),
        ]))
        story.append(intention_table)
        story.append(Spacer(1, 15))
    
    # 从业阶段
    if analysis.get('从业阶段'):
        story.append(create_section_table("📍 从业阶段识别", "", styles))
        story.append(Spacer(1, 5))
        
        stage = analysis['从业阶段']
        story.append(Paragraph(f"<b>当前阶段：</b>{stage.get('当前阶段', '-')}", styles['ChineseBody']))
        story.append(Paragraph(f"<b>阶段特征：</b>{stage.get('阶段特征', '-')}", styles['ChineseBody']))
        story.append(Spacer(1, 15))
    
    # 核心关注点
    if analysis.get('核心关注点'):
        story.append(create_section_table("🎯 骑手核心关注点", "", styles))
        story.append(Spacer(1, 5))
        
        concerns = analysis['核心关注点']
        
        if concerns.get('第一关注'):
            story.append(Paragraph(f"<b>1️⃣ {concerns['第一关注'].get('因素', '-')}：</b>{concerns['第一关注'].get('具体内容', '')}", styles['ChineseBody']))
        
        if concerns.get('第二关注'):
            story.append(Paragraph(f"<b>2️⃣ {concerns['第二关注'].get('因素', '-')}：</b>{concerns['第二关注'].get('具体内容', '')}", styles['ChineseBody']))
        
        if concerns.get('第三关注'):
            story.append(Paragraph(f"<b>3️⃣ {concerns['第三关注'].get('因素', '-')}：</b>{concerns['第三关注'].get('具体内容', '')}", styles['ChineseBody']))
        
        if concerns.get('其他关注'):
            story.append(Paragraph(f"<b>其他关注点：</b>{'、'.join(concerns['其他关注'])}", styles['ChineseBody']))
        
        story.append(Spacer(1, 15))
    
    # 竞品分析
    if analysis.get('竞品分析'):
        story.append(create_section_table("⚖️ 竞品对比分析", "", styles))
        story.append(Spacer(1, 5))
        
        competitor = analysis['竞品分析']
        
        if competitor.get('提及竞品'):
            story.append(Paragraph(f"<b>提及竞品：</b>{'、'.join(competitor['提及竞品'])}", styles['ChineseBody']))
        
        story.append(Paragraph(f"<b>对比倾向：</b>{competitor.get('对比倾向', '-')}", styles['ChineseBody']))
        
        if competitor.get('本公司优势'):
            story.append(Paragraph("<b>✅ 本公司优势：</b>", styles['ChineseBody']))
            for item in competitor['本公司优势']:
                story.append(Paragraph(f"  • {item}", styles['ChineseBody']))
        
        if competitor.get('本公司劣势'):
            story.append(Paragraph("<b>⚠️ 本公司劣势：</b>", styles['ChineseBody']))
            for item in competitor['本公司劣势']:
                story.append(Paragraph(f"  • {item}", styles['ChineseBody']))
        
        story.append(Spacer(1, 15))
    
    # 情感分析
    if analysis.get('情感分析'):
        story.append(create_section_table("😊 情感与沟通分析", "", styles))
        story.append(Spacer(1, 5))
        
        sentiment = analysis['情感分析']
        story.append(Paragraph(f"<b>骑手态度：</b>{sentiment.get('骑手态度', '-')}", styles['ChineseBody']))
        story.append(Paragraph(f"<b>租赁顾问表现：</b>{sentiment.get('租赁顾问表现', '-')}", styles['ChineseBody']))
        story.append(Paragraph(f"<b>沟通效果：</b>{sentiment.get('沟通效果', '-')}", styles['ChineseBody']))
        story.append(Spacer(1, 15))
    
    # 关键信息
    if analysis.get('关键信息'):
        story.append(create_section_table("🔑 关键信息提取", "", styles))
        story.append(Spacer(1, 5))
        
        key_info = analysis['关键信息']
        story.append(Paragraph(f"<b>📞 联系方式：</b>{key_info.get('联系方式', '暂无')}", styles['ChineseBody']))
        story.append(Paragraph(f"<b>📅 试车安排：</b>{key_info.get('试车安排', '暂无')}", styles['ChineseBody']))
        story.append(Paragraph(f"<b>📝 特殊需求：</b>{key_info.get('特殊需求', '暂无')}", styles['ChineseBody']))
        story.append(Spacer(1, 15))
    
    # 跟进建议
    if analysis.get('跟进建议'):
        story.append(create_section_table("💡 跟进策略建议", "", styles))
        story.append(Spacer(1, 5))
        
        followup = analysis['跟进建议']
        
        if followup.get('推荐话术'):
            story.append(Paragraph("<b>💬 推荐话术要点：</b>", styles['ChineseBody']))
            for item in followup['推荐话术']:
                story.append(Paragraph(f"  • {item}", styles['ChineseBody']))
        
        if followup.get('卖点强调'):
            story.append(Paragraph("<b>⭐ 差异化卖点强调：</b>", styles['ChineseBody']))
            for item in followup['卖点强调']:
                story.append(Paragraph(f"  • {item}", styles['ChineseBody']))
        
        if followup.get('异议处理'):
            story.append(Paragraph("<b>🛡️ 异议处理建议：</b>", styles['ChineseBody']))
            for item in followup['异议处理']:
                story.append(Paragraph(f"  • {item}", styles['ChineseBody']))
        
        if followup.get('下一步计划'):
            story.append(Paragraph(f"<b>📋 下一步跟进计划：</b>{followup['下一步计划']}", styles['ChineseBody']))
        
        story.append(Spacer(1, 15))
    
    # 总结
    if analysis.get('总结'):
        story.append(create_section_table("✅ 分析总结", "", styles))
        story.append(Spacer(1, 5))
        story.append(Paragraph(analysis['总结'], styles['ChineseSummary']))
    
    # 对话记录
    if speaker1 or speaker2:
        story.append(PageBreak())
        story.append(create_section_table("💬 对话记录", "", styles))
        story.append(Spacer(1, 10))
        
        role1 = analysis.get('角色识别', {}).get('说话人1', '租赁顾问')
        role2 = analysis.get('角色识别', {}).get('说话人2', '骑手')
        
        max_len = max(len(speaker1 or []), len(speaker2 or []))
        
        for i in range(max_len):
            if i < len(speaker1 or []):
                text = speaker1[i].get('text', speaker1[i]) if isinstance(speaker1[i], dict) else speaker1[i]
                story.append(Paragraph(f"<b>{role1}：</b>{text}", styles['ChatBubble1']))
                story.append(Spacer(1, 5))
            
            if i < len(speaker2 or []):
                text = speaker2[i].get('text', speaker2[i]) if isinstance(speaker2[i], dict) else speaker2[i]
                story.append(Paragraph(f"<b>{role2}：</b>{text}", styles['ChatBubble2']))
                story.append(Spacer(1, 5))
    
    # 页脚
    story.append(Spacer(1, 30))
    story.append(Paragraph("—" * 50, styles['ChineseSubtitle']))
    story.append(Paragraph("本报告由骑手电瓶车租赁意向智能分析系统自动生成", styles['ChineseSubtitle']))
    story.append(Paragraph(f"© {datetime.now().year} AI驱动的电瓶车租赁业务洞察与骑手跟进策略", styles['ChineseSubtitle']))
    
    doc.build(story)
    
    buffer.seek(0)
    return buffer.getvalue()
