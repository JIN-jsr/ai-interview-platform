# Day 2 Notes

## 完成内容

- 新增 TXT / PDF / DOCX 简历上传读取
- 新增 prompts.py，用于简历结构化解析 Prompt
- 新增 OpenAI-compatible LLM 调用封装
- 新增 parse_resume()，支持 LLM 解析与本地规则解析 fallback
- 解析结果统一输出为 JSON
- 用户画像生成模块改为基于结构化简历结果
- 页面显示 LLM 状态、结构化解析结果、用户画像与面试重点

## 当前策略

- 如果 .env 中 USE_LLM=true 且 API Key 有效，则调用大模型解析简历。
- 如果没有配置 API 或 API 调用失败，则自动切换到本地规则解析。
- 这样可以保证演示稳定，不会因为 API 问题导致系统不可运行。

## 下一步

- Day 3：扩展 knowledge_base.json 至 60-100 条
- 实现基于简历技术栈的 RAG 检索
- 让面试官根据检索到的知识条目生成基础知识问题
