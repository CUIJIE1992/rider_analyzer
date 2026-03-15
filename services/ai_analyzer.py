#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI文本分析服务
使用MiniMax API分析对话内容
"""

import os
import json
import requests
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class AIAnalyzer:
    """AI分析器类 - 使用MiniMax API"""
    
    def __init__(self):
        self.api_key = os.getenv('MINIMAX_API_KEY', 'sk-cp-cqVKB1R2cDzGZzjoOvNr_H5IcZOujhZrlbQUxhwaEO7eJ6q1nKvKMWti622k_l2uHmv5qUkbDb-aY73qTWjISAKy-YjWupjbk5yw876Np90BMXQnCGJFvfA')
        self.group_id = os.getenv('MINIMAX_GROUP_ID', '')
        self.base_url = "https://api.minimax.chat/v1"
        
    def analyze_conversation(self, speaker1_text, speaker2_text):
        """
        分析对话内容
        
        Args:
            speaker1_text: 说话人1的文本
            speaker2_text: 说话人2的文本
            
        Returns:
            dict: 分析结果
        """
        # 准备对话内容
        conversation = self._format_conversation(speaker1_text, speaker2_text)
        
        # 构建提示词
        prompt = f"""
你是一位专业的房产销售分析师，请分析以下购房咨询通话录音的文本内容，提供专业的购房电话分析报告。

对话内容：
{conversation}

请按照以下购房电话分析框架进行详细分析：

【一、通话概要统计】
- 通话时长估算（根据对话内容推断）
- 有效沟通程度（高/中/低）
- 客户响应积极性（积极/一般/冷淡）

【二、角色识别】
识别说话人1和说话人2的身份角色（置业顾问/客户）

【三、客户购房意向分析】
1. 面积需求（具体面积区间）
2. 价格区间（预算范围）
3. 区域位置偏好（意向区域）
4. 户型需求（几室几厅等）

【四、客户购房阶段识别】
判断客户当前处于哪个阶段：
- 初步咨询阶段：刚开始了解，需求不明确
- 需求明确阶段：清楚自己想要什么，在对比选择
- 决策阶段：已有明确意向，准备购买
- 犹豫观望阶段：有需求但还在观望

【五、客户核心关注点分析】
分析客户最关心的购房因素（按重要性排序）：
- 学区教育资源
- 交通便利程度
- 配套设施（商业、医疗等）
- 开发商信誉
- 物业服务质量
- 升值潜力
- 小区环境
- 其他关注点

【六、竞品对比分析】
识别客户提及的其他楼盘信息：
- 竞品楼盘名称
- 客户对比倾向
- 本项目优劣势分析

【七、客户分类评级】
1. 购房意向强度：高/中/低
2. 购买力评估：高/中/低
3. 决策周期预估：短期（1个月内）/中期（1-3个月）/长期（3个月以上）
4. 综合客户等级：A类（高意向高购买力）/B类（中意向或中购买力）/C类（低意向或低购买力）

【八、情感与沟通分析】
1. 客户情感态度（积极/消极/中性）
2. 置业顾问表现评价
3. 沟通效果评估

【九、关键信息提取】
- 客户联系方式（如有）
- 看房时间安排
- 特殊需求备注

【十、跟进策略建议】
1. 推荐话术要点
2. 差异化卖点强调
3. 异议处理建议
4. 下一步跟进计划

请严格按照以下JSON格式返回分析结果：
{{
    "通话概要": {{
        "通话时长估算": "...",
        "有效沟通程度": "高/中/低",
        "客户响应积极性": "积极/一般/冷淡"
    }},
    "角色识别": {{
        "说话人1": "置业顾问",
        "说话人2": "客户"
    }},
    "购房意向": {{
        "面积需求": "...",
        "价格区间": "...",
        "区域偏好": "...",
        "户型需求": "..."
    }},
    "购房阶段": {{
        "当前阶段": "初步咨询/需求明确/决策阶段/犹豫观望",
        "阶段特征": "..."
    }},
    "核心关注点": {{
        "第一关注": {{"因素": "...", "具体内容": "..."}},
        "第二关注": {{"因素": "...", "具体内容": "..."}},
        "第三关注": {{"因素": "...", "具体内容": "..."}},
        "其他关注": ["...", "..."]
    }},
    "竞品分析": {{
        "提及竞品": ["...", "..."],
        "对比倾向": "倾向本项目/倾向竞品/中立对比",
        "本项目优势": ["...", "..."],
        "本项目劣势": ["...", "..."]
    }},
    "客户评级": {{
        "购房意向强度": "高/中/低",
        "购买力评估": "高/中/低",
        "决策周期": "短期/中期/长期",
        "综合等级": "A类/B类/C类",
        "等级说明": "..."
    }},
    "情感分析": {{
        "客户态度": "积极/消极/中性",
        "置业顾问表现": "...",
        "沟通效果": "..."
    }},
    "关键信息": {{
        "联系方式": "...",
        "看房安排": "...",
        "特殊需求": "..."
    }},
    "跟进建议": {{
        "推荐话术": ["...", "..."],
        "卖点强调": ["...", "..."],
        "异议处理": ["...", "..."],
        "下一步计划": "..."
    }},
    "总结": "本次通话的核心结论和跟进要点"
}}
"""
        
        try:
            # 调用MiniMax API
            result = self._call_minimax_api(prompt)
            return result
            
        except Exception as e:
            return {
                'error': f'分析失败: {str(e)}',
                '通话概要': {},
                '角色识别': {},
                '购房意向': {},
                '购房阶段': {},
                '核心关注点': {},
                '竞品分析': {},
                '客户评级': {},
                '情感分析': {},
                '关键信息': {},
                '跟进建议': {},
                '总结': ''
            }
    
    def _call_minimax_api(self, prompt):
        """调用MiniMax API"""
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "MiniMax-Text-01",
            "messages": [
                {
                    "role": "system",
                    "content": "你是一位专业的房产销售分析师，擅长分析购房咨询通话录音，能够准确识别客户需求、购房意向和跟进机会。请严格按照JSON格式返回结果。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        logger.debug(f"请求URL: {url}")
        logger.debug(f"请求参数: model={data['model']}, temperature={data['temperature']}, max_tokens={data['max_tokens']}")
        logger.debug(f"请求消息数量: {len(data['messages'])}")
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=60)
            logger.debug(f"响应状态码: {response.status_code}")
            logger.debug(f"响应内容: {response.text[:1000] if len(response.text) > 1000 else response.text}")
            
            result = response.json()
            
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                logger.debug(f"API返回内容长度: {len(content)}")
                
                try:
                    if '```json' in content:
                        content = content.split('```json')[1].split('```')[0]
                    elif '```' in content:
                        content = content.split('```')[1].split('```')[0]
                    
                    parsed = json.loads(content.strip())
                    return parsed
                    
                except json.JSONDecodeError as je:
                    logger.error(f"JSON解析错误: {str(je)}")
                    logger.error(f"尝试解析的内容: {content[:500]}")
                    return {
                        '原始分析': content,
                        '主题': '请查看原始分析',
                        '情感分析': {},
                        '主要观点': {},
                        '争议点': [],
                        '关键信息': {},
                        '结论': ''
                    }
            else:
                error_msg = result.get('error', {}).get('message', '未知错误')
                error_code = result.get('error', {}).get('code', 'N/A')
                logger.error(f"API返回格式错误 - 错误码: {error_code}, 错误信息: {error_msg}")
                logger.error(f"完整响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                raise Exception(f"API返回格式错误 [错误码: {error_code}]: {error_msg}")
                
        except requests.exceptions.Timeout:
            logger.error("API请求超时 (30秒)")
            raise Exception("API请求超时，请检查网络连接或稍后重试")
        except requests.exceptions.ConnectionError as ce:
            logger.error(f"网络连接错误: {str(ce)}")
            raise Exception(f"网络连接失败: {str(ce)}")
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求异常: {str(e)}")
            raise Exception(f"API请求失败: {str(e)}")
        except json.JSONDecodeError as je:
            logger.error(f"响应JSON解析失败: {str(je)}")
            logger.error(f"原始响应文本: {response.text[:500]}")
            raise Exception(f"API响应格式错误: {str(je)}")
    
    def _format_conversation(self, speaker1_text, speaker2_text):
        """格式化对话内容"""
        conversation = []
        
        # 处理输入（可能是列表或字符串）
        if isinstance(speaker1_text, list):
            s1_text = ' '.join([item.get('text', '') if isinstance(item, dict) else str(item) 
                               for item in speaker1_text])
        else:
            s1_text = str(speaker1_text)
            
        if isinstance(speaker2_text, list):
            s2_text = ' '.join([item.get('text', '') if isinstance(item, dict) else str(item) 
                               for item in speaker2_text])
        else:
            s2_text = str(speaker2_text)
        
        conversation.append(f"【说话人1】：{s1_text}")
        conversation.append(f"【说话人2】：{s2_text}")
        
        return '\n\n'.join(conversation)
    
    def extract_keywords(self, text):
        """提取关键词"""
        prompt = f"请从以下文本中提取5-10个关键词：\n\n{text}"
        
        try:
            url = f"{self.base_url}/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "MiniMax-Text-01",
                "messages": [
                    {"role": "system", "content": "你是一个关键词提取专家。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.5,
                "max_tokens": 100
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            result = response.json()
            
            if 'choices' in result and len(result['choices']) > 0:
                keywords = result['choices'][0]['message']['content']
                return keywords.split('、') if '、' in keywords else keywords.split(',')
            
            return []
            
        except Exception as e:
            return []
    
    def summarize(self, text):
        """生成摘要"""
        prompt = f"请为以下文本生成一个简洁的摘要（100字以内）：\n\n{text}"
        
        try:
            url = f"{self.base_url}/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "MiniMax-Text-01",
                "messages": [
                    {"role": "system", "content": "你是一个文本摘要专家，擅长生成简洁准确的摘要。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.5,
                "max_tokens": 150
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            result = response.json()
            
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content']
            
            return "摘要生成失败"
            
        except Exception as e:
            return f"摘要生成失败: {str(e)}"
    
    def generate_customer_tags(self, analysis):
        """
        根据分析结果自动生成客户标签
        
        Args:
            analysis: AI分析结果字典
            
        Returns:
            list: 标签列表
        """
        tags = []
        
        if not analysis:
            return tags
        
        rating = analysis.get('客户评级', {})
        stage = analysis.get('购房阶段', {})
        concerns = analysis.get('核心关注点', {})
        
        intention = rating.get('购房意向强度', '')
        if intention == '高':
            tags.append('高意向客户')
        elif intention == '中':
            tags.append('中意向客户')
        elif intention == '低':
            tags.append('低意向客户')
        
        grade = rating.get('综合等级', '')
        if grade == 'A类':
            tags.append('A类优质客户')
        
        first_concern = concerns.get('第一关注', {})
        second_concern = concerns.get('第二关注', {})
        third_concern = concerns.get('第三关注', {})
        other_concerns = concerns.get('其他关注', [])
        
        all_concerns = []
        if first_concern.get('因素'):
            all_concerns.append(first_concern['因素'])
        if second_concern.get('因素'):
            all_concerns.append(second_concern['因素'])
        if third_concern.get('因素'):
            all_concerns.append(third_concern['因素'])
        all_concerns.extend(other_concerns)
        
        all_concerns_text = ' '.join(all_concerns)
        if '学区' in all_concerns_text or '教育' in all_concerns_text:
            tags.append('学区关注')
        if '交通' in all_concerns_text:
            tags.append('交通关注')
        
        current_stage = stage.get('当前阶段', '')
        if '改善' in current_stage:
            tags.append('改善型需求')
        elif '刚需' in current_stage or '首次' in current_stage:
            tags.append('刚需客户')
        elif '决策' in current_stage:
            tags.append('决策期客户')
        
        return tags
