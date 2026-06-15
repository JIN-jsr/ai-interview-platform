# 测试清单

## 环境测试

- [ ] `pip install -r requirements.txt` 成功
- [ ] `streamlit run app.py` 成功
- [ ] 浏览器能打开本地页面
- [ ] `.env.example` 存在
- [ ] `.env` 未提交到 GitHub

## 简历解析测试

- [ ] 直接粘贴简历可以解析
- [ ] TXT 文件可以读取
- [ ] DOCX 文件可以读取
- [ ] 普通文字版 PDF 可以读取
- [ ] 解析结果包含 skills 和 projects
- [ ] 用户画像与面试重点可以生成

## RAG 测试

- [ ] 知识库统计显示 80 条
- [ ] 搜索 `Python MySQL Redis 后端` 有结果
- [ ] 搜索 `数据库 事务 索引` 有结果
- [ ] 简历解析后能推荐 RAG 问题

## 面试测试

- [ ] 可以开始面试
- [ ] 可以连续回答多轮
- [ ] 项目回答中提到 Redis / MySQL 后能触发追问
- [ ] RAG 基础题回答不完整时能继续追问
- [ ] 面试记录页面有记录

## 评分报告测试

- [ ] 完成几轮面试后可以生成正式评分报告
- [ ] 总分和等级显示正常
- [ ] 五维度评分显示正常
- [ ] 每个维度有评分依据
- [ ] 可以下载 JSON 报告
- [ ] 可以下载 Markdown 报告

## LLM 测试

- [ ] `.env` 中 USE_LLM=true
- [ ] API Key 已填写
- [ ] Base URL 已填写
- [ ] Model Name 已填写
- [ ] 页面 LLM 状态显示已启用
- [ ] “测试 LLM 连接”成功
- [ ] LLM 解析简历时 `_parser` 显示 `llm`
