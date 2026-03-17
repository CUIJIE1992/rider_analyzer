# 优化骑手电瓶车租赁意向分析 Spec

## Why
当前系统虽然标题和主要功能是骑手意向智能分析系统，但在代码中仍存在一些购房相关的文案残留（如PDF生成器中的"购房电话分析报告"、"房产销售洞察"等），需要将所有文案统一修改为电瓶车租赁意向相关，确保产品定位一致。

## What Changes
- 修改PDF生成器中的标题和文案，将购房相关改为电瓶车租赁相关
- 修改文本输入区域的示例文本，从楼盘咨询改为电瓶车租赁咨询
- 修改AI分析提示词中可能存在的购房相关表述
- 统一所有页面的副标题和描述文案

## Impact
- 受影响文件：
  - services/pdf_generator.py - PDF报告标题和文案
  - templates/index.html - 文本输入示例
  - services/ai_analyzer.py - 提示词和角色描述

## ADDED Requirements
### Requirement: 文案一致性
系统所有文案必须围绕"电瓶车租赁"和"骑手"主题，不得出现购房、房产、楼盘等相关词汇。

#### Scenario: PDF报告
- **WHEN** 用户导出PDF报告
- **THEN** 报告标题应为"骑手电瓶车租赁分析报告"，副标题应为"AI驱动的电瓶车租赁业务洞察与骑手跟进策略"

#### Scenario: 文本输入示例
- **WHEN** 用户在首页查看文本输入区域
- **THEN** 示例文本应展示电瓶车租赁咨询对话，而非楼盘咨询

#### Scenario: AI分析结果
- **WHEN** AI分析结果显示在页面上
- **THEN** 所有标签、标题、描述都应使用电瓶车租赁业务相关术语

## MODIFIED Requirements
无

## REMOVED Requirements
无
