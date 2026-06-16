\# PROJECT\_CONTEXT.md



\## 1. Project Background



This project is for the 2026 Leeds Technology Month AI Mock Interview and Ability Improvement Software Development Competition.



The required system should support:



\* Resume input or upload

\* Resume understanding

\* Candidate profile generation

\* Text-based mock interview

\* RAG-based basic knowledge questions

\* Project experience deep-dive

\* Interview scoring and feedback

\* Local running or demo

\* GitHub submission

\* Design document

\* Demo video within 8 minutes



The project is currently built as a Streamlit MVP because the timeline is short and the competition values a complete working loop.



\## 2. Current Closed Loop



The system has already completed the following closed loop:



Resume input or upload

→ resume parsing

→ structured resume JSON

→ candidate profile and interview focus

→ RAG knowledge retrieval

→ continuous interview

→ project deep-dive

→ answer analysis

→ final five-dimension scoring report

→ report download



This closed loop must not be broken.



\## 3. Development Timeline Summary



\### Day 1



Created the initial Streamlit project scaffold.



Completed:



\* `app.py`

\* basic UI

\* resume input text area

\* candidate profile placeholder

\* mock interview tab

\* scoring report placeholder

\* basic project folder structure

\* README

\* `.env.example`

\* `.gitignore`



\### Day 2



Added structured resume parsing.



Completed:



\* TXT / PDF / DOCX resume upload

\* direct resume text input

\* `resume\_file\_loader.py`

\* `resume\_parser.py`

\* `prompts.py`

\* LLM parsing support

\* local heuristic fallback parser

\* structured JSON resume output

\* candidate profile generation based on parsed resume



Important: if LLM fails, the system automatically falls back to local parsing.



\### Day 3



Added RAG knowledge base and retrieval.



Completed:



\* expanded `data/knowledge\_base.json` to 80 entries

\* covered Python, Java, data structures, databases, Redis, networks, OS, software engineering, AI/RAG

\* added `rag\_retriever.py`

\* added RAG search page

\* matched RAG questions based on candidate profile

\* connected RAG questions to mock interview



Current retrieval method: local keyword retrieval.



\### Day 4



Added contextual interview follow-up and answer analysis.



Completed:



\* `answer\_analyzer.py`

\* records every question and answer

\* detects technical keywords

\* calculates temporary answer quality

\* supports project follow-up based on answer keywords

\* supports RAG follow-up based on missing points

\* added interview records and analysis page

\* supports downloading interview records as JSON



\### Day 5



Added formal scoring report.



Completed:



\* `evaluator.py`

\* final report generation

\* five scoring dimensions:



&#x20; \* Basic knowledge mastery: 25%

&#x20; \* Project understanding depth: 25%

&#x20; \* Answer logic: 20%

&#x20; \* Expression completeness: 15%

&#x20; \* Job matching: 15%

\* total score

\* level

\* evidence

\* strengths

\* problems

\* recommendations

\* JSON and Markdown report download



\### Day 6



Added documentation, self-check, and LLM configuration support.



Completed:



\* updated `.env.example`

\* added LLM connection test

\* added `scripts/self\_check.py`

\* added:



&#x20; \* `docs/llm\_config\_guide.md`

&#x20; \* `docs/rag\_build\_guide.md`

&#x20; \* `docs/design\_document\_draft.md`

&#x20; \* `docs/demo\_script.md`

&#x20; \* `docs/test\_checklist.md`

\* added project self-check page in Streamlit



\### Day 7



Finalized submission version.



Completed:



\* fixed LLM prompt formatting bug in `resume\_parser.py`

\* updated README

\* generated formal design document

\* added final submission checklist

\* prepared final project package



\## 4. Current LLM Status



The project uses an OpenAI-compatible API wrapper in:



```text

src/llm\_client.py

```



The `.env` file should contain:



```text

LLM\_API\_KEY=real\_api\_key\_here

LLM\_BASE\_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

MODEL\_NAME=qwen3.7-plus

USE\_LLM=true

```



Alternative endpoint for Singapore or international account:



```text

LLM\_BASE\_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1

```



Recommended model:



\* Development and stable demo: `qwen3.7-plus`

\* Strongest final effect if stable: `qwen3.7-max`

\* Fallback: `qwen-plus`



Important:



\* Do not commit `.env`.

\* `.env.example` is safe to commit.

\* If LLM fails, fallback must still work.



\## 5. Current Problem and Next Optimization



The project works, but the interview questions are still somewhat rigid.



Current question flow:



Profile keywords

→ RAG retrieval

→ template question generation



Target optimized flow:



Candidate profile



\* recent conversation history

\* RAG retrieval results

&#x20; → LLM generates natural interview question

&#x20; → system stores question metadata

&#x20; → user answers

&#x20; → system analyzes answer

&#x20; → LLM or rule system generates follow-up



Important principle:



RAG decides what knowledge should be asked.

LLM decides how to ask naturally.



\## 6. Current RAG Status



Current knowledge base:



```text

data/knowledge\_base.json

```



Current size:



```text

80 entries

```



It is enough for MVP and competition minimum requirement, but small for realistic interviews.



Future target:



```text

200–300 high-quality entries

```



Recommended future categories:



\* Python

\* Java

\* Data structures and algorithms

\* MySQL

\* Redis

\* Computer networks

\* Operating systems

\* Backend development

\* Frontend basics

\* Software engineering

\* Git and testing

\* AI / RAG / LLM applications

\* Project scenario questions

\* Debugging questions

\* System design basics



\## 7. Current Architecture



Main files:



```text

app.py

src/llm\_client.py

src/prompts.py

src/resume\_file\_loader.py

src/resume\_parser.py

src/profile\_generator.py

src/rag\_retriever.py

src/interviewer.py

src/answer\_analyzer.py

src/evaluator.py

data/knowledge\_base.json

scripts/self\_check.py

```



Do not remove these files.



\## 8. Current Testing Commands



Run the app:



```bash

streamlit run app.py

```



Run self-check:



```bash

python scripts/self\_check.py

```



Install dependencies:



```bash

pip install -r requirements.txt

```



\## 9. Git Rules



Before major changes:



```bash

git status

```



For each optimization, use a separate commit.



Suggested commit messages:



```text

Add LLM-based interview question generation

Improve RAG knowledge schema

Expand RAG knowledge base

Polish Streamlit UI

Improve final report wording

Update README and demo documentation

```



Never commit:



```text

.env

\_\_pycache\_\_/

\*.pyc

```



\## 10. Recommended Next Task



The next task should be:



Add LLM + RAG collaborative interview question generation.



Expected new file:



```text

src/llm\_interviewer.py

```



Expected modified files:



```text

src/interviewer.py

src/prompts.py

app.py

```



Expected behavior:



1\. RAG retrieves relevant knowledge entries.

2\. LLM receives candidate profile, recent messages, and RAG entries.

3\. LLM returns structured JSON:



&#x20;  \* question

&#x20;  \* question\_type

&#x20;  \* knowledge\_id

&#x20;  \* expected\_points

&#x20;  \* reason

4\. The app displays the generated natural question.

5\. The app stores metadata for answer analysis and scoring.

6\. If LLM fails, the old rule-based question generation is used as fallback.



