\# AGENTS.md



\## Project Name



AI 模拟面试与能力提升平台



\## Project Goal



This project is a Streamlit-based AI mock interview platform for computer science students. The core workflow is:



Resume input / upload

→ structured resume parsing

→ candidate profile generation

→ RAG knowledge retrieval

→ continuous mock interview

→ project deep-dive questions

→ answer analysis

→ five-dimension scoring report



The project is for a university software development competition. Stability, explainability, and demo quality are more important than unnecessary complexity.



\## Current Tech Stack



\* Python

\* Streamlit

\* JSON knowledge base

\* OpenAI-compatible LLM API

\* Aliyun Bailian / DashScope-compatible Qwen model

\* pdfplumber for PDF resume reading

\* python-docx for DOCX resume reading

\* python-dotenv for local API key management

\* requests for LLM API calls



\## Important Files



\* `app.py`: main Streamlit application

\* `src/resume\_parser.py`: resume parsing logic

\* `src/llm\_client.py`: LLM API wrapper

\* `src/rag\_retriever.py`: local RAG retrieval logic

\* `src/interviewer.py`: interview flow and follow-up logic

\* `src/answer\_analyzer.py`: answer analysis logic

\* `src/evaluator.py`: final five-dimension scoring report

\* `data/knowledge\_base.json`: RAG knowledge base

\* `docs/PROJECT\_CONTEXT.md`: full project background and history

\* `docs/OPTIMIZATION\_PLAN.md`: future optimization plan

\* `scripts/self\_check.py`: project self-check script



\## Non-Negotiable Rules



1\. Do not delete or break the existing working closed loop.

2\. Do not remove fallback logic. The app must still run even if LLM fails.

3\. Do not hard-code API keys.

4\. Do not commit `.env`.

5\. Keep `.env.example` safe and generic.

6\. Keep the project runnable with:



```bash

streamlit run app.py

```



7\. After modifying code, run:



```bash

python scripts/self\_check.py

```



8\. Keep changes small and explainable.

9\. Do not rewrite the whole project unless explicitly asked.

10\. Prefer improving existing modules instead of creating unnecessary new architecture.



\## LLM Usage Direction



The LLM should not only parse resumes. The target optimization is:



Resume + candidate profile + RAG results + conversation history

→ LLM generates natural interview questions and follow-up questions.



RAG should provide the factual basis.

LLM should make the language natural and context-aware.



Do not let the LLM freely invent interview content without RAG or profile grounding.



\## RAG Direction



The current knowledge base has 80 entries. It is enough for MVP, but future optimization should expand it to 200–300 high-quality entries.



Future entries should include fields such as:



\* `id`

\* `category`

\* `tags`

\* `difficulty`

\* `question\_type`

\* `question`

\* `answer`

\* `expected\_points`

\* `bad\_answer\_signals`

\* `follow\_up`

\* `related\_project\_scenarios`

\* `source`



\## Scoring Direction



The final score must follow these dimensions:



\* Basic knowledge mastery: 25%

\* Project understanding depth: 25%

\* Answer logic: 20%

\* Expression completeness: 15%

\* Job matching: 15%



Rules can calculate the score, and LLM may polish the feedback text.

Do not let the LLM randomly decide scores without structured evidence.



\## Development Style



When making changes:



1\. Read `docs/PROJECT\_CONTEXT.md` first.

2\. Identify the exact files to modify.

3\. Make minimal necessary changes.

4\. Preserve working functionality.

5\. Run self-check.

6\. Explain what changed and how to test it.



\## Current Priority



The next major optimization is:



LLM + RAG collaborative interview question generation.



Specifically:



\* Use RAG to retrieve relevant knowledge entries.

\* Send candidate profile, recent conversation history, and retrieved RAG entries to LLM.

\* Let LLM generate a natural interview question.

\* Store `knowledge\_id`, `question\_type`, `expected\_points`, and `reference\_answer`.

\* Keep fallback template-based question generation if LLM fails.



