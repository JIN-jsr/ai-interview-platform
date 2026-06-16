# AI Mock Interview and Ability Improvement Platform

AI Mock Interview and Ability Improvement Platform is a Streamlit-based mock technical interview system for computer science students. It supports resume-driven candidate profiling, RAG-based knowledge retrieval, LLM-generated interview questions, contextual follow-up questions, answer analysis, and a five-dimension scoring report with downloadable results.

## Features

- Resume text input and TXT / PDF / DOCX upload
- Structured resume parsing with local backup logic
- Candidate profile and interview focus generation
- RAG-based knowledge retrieval from a local JSON knowledge base
- LLM-generated interview questions grounded in profile and RAG context
- Contextual follow-up questions during the interview
- Answer analysis with expected-point coverage
- Five-dimension scoring report
- JSON and Markdown report downloads
- Backup question generation when the LLM API is disabled, times out, or returns invalid output

## Architecture

```text
Streamlit UI
  ->
Resume Parser
  ->
Profile Generator
  ->
RAG Retriever
  ->
LLM Interviewer
  ->
Answer Analyzer
  ->
Evaluator
  ->
Final Report
```

## Scoring Dimensions

| Dimension | Weight |
|---|---:|
| Basic knowledge mastery | 25% |
| Project understanding depth | 25% |
| Answer logic | 20% |
| Expression completeness | 15% |
| Job matching | 15% |

## Quick Start

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Run the self-check:

```bash
python scripts/self_check.py
```

Expected result:

```text
=== Self check passed ===
```

## LLM Configuration

Copy the example environment file:

```bash
copy .env.example .env
```

Edit `.env` and fill in your own API key:

```text
LLM_API_KEY=your_real_api_key_here
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
MODEL_NAME=qwen3.7-plus
USE_LLM=true
```

For backup-mode testing:

```text
USE_LLM=false
```

Do not put real API keys in `.env.example`, README, screenshots, or commits.

## Demo Guide

Use the prepared walkthrough:

[demo/demo_walkthrough.md](demo/demo_walkthrough.md)

Demo sample files:

- [demo/sample_resume_ai_app.txt](demo/sample_resume_ai_app.txt)
- [demo/sample_resume_backend.txt](demo/sample_resume_backend.txt)
- [demo/sample_answers_ai_app.md](demo/sample_answers_ai_app.md)

## Project Structure

```text
ai_interview_platform_day1/
├── app.py
├── requirements.txt
├── README.md
├── .env.example
├── data/
│   ├── knowledge_base.json
│   └── sample_resume.txt
├── demo/
│   ├── sample_resume_ai_app.txt
│   ├── sample_resume_backend.txt
│   ├── sample_answers_ai_app.md
│   └── demo_walkthrough.md
├── src/
│   ├── llm_client.py
│   ├── llm_interviewer.py
│   ├── resume_file_loader.py
│   ├── resume_parser.py
│   ├── profile_generator.py
│   ├── rag_retriever.py
│   ├── interviewer.py
│   ├── answer_analyzer.py
│   └── evaluator.py
├── scripts/
│   └── self_check.py
├── docs/
│   ├── PROJECT_CONTEXT.md
│   ├── OPTIMIZATION_PLAN.md
│   ├── llm_config_guide.md
│   ├── rag_build_guide.md
│   ├── demo_script.md
│   ├── test_checklist.md
│   └── final_submission_checklist.md
└── outputs/
    ├── logs/
    └── reports/
```

## Suggested Demo Flow

1. Start the app with `streamlit run app.py`.
2. Check the sidebar status panel and LLM configuration.
3. Load a sample resume from the sidebar.
4. Parse the resume and generate the candidate profile.
5. Show RAG retrieval results.
6. Start the mock interview and show question metadata.
7. Answer 3-4 questions using the sample answers.
8. Generate the final scoring report.
9. Download JSON or Markdown reports.

## Safety Note

`.env` should never be committed. It may contain real API keys and local configuration. Keep `.env.example` generic and safe for GitHub.
