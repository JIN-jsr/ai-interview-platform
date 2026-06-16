# Final Submission Checklist

## GitHub Repository

- [ ] GitHub repository is updated.
- [ ] `.env` is not committed.
- [ ] `.env.example` exists and contains no real API keys.
- [ ] README is complete and professional.
- [ ] `requirements.txt` is included.
- [ ] `app.py` can run the Streamlit app.
- [ ] `src/` core modules are included.
- [ ] `data/knowledge_base.json` exists and passes schema checks.
- [ ] `demo/demo_walkthrough.md` exists.
- [ ] Demo sample resumes and answers exist.
- [ ] Design document exists in `docs/`.

## Runtime Checks

- [ ] App can run with `streamlit run app.py`.
- [ ] `python scripts/self_check.py` passes.
- [ ] LLM connection can be tested from the Streamlit app.
- [ ] Fallback mode works when `USE_LLM=false`.
- [ ] Resume parsing works with text input.
- [ ] Demo sample resume can be loaded from the sidebar.
- [ ] Candidate profile is generated after parsing.
- [ ] RAG retrieval returns relevant entries.
- [ ] Interview page shows question metadata.
- [ ] Interview records include answers and analysis.
- [ ] Final report can be generated.
- [ ] JSON and Markdown download buttons work.

## Demo Video

- [ ] Demo video is under 8 minutes.
- [ ] Demo starts from project launch.
- [ ] Sidebar status panel is shown.
- [ ] LLM status is shown.
- [ ] Sample resume loading is shown.
- [ ] Resume parsing and profile generation are shown.
- [ ] RAG retrieval is shown.
- [ ] Mock interview shows `generated_by`, difficulty, `knowledge_id`, `expected_points`, and reason.
- [ ] 3-4 answers are demonstrated.
- [ ] Final scoring report is generated.
- [ ] Report download is shown.

## Submission Materials

- [ ] GitHub repository URL.
- [ ] Project design document.
- [ ] Demo video.
- [ ] Any required competition form or description.

## Safety

- [ ] Real API keys are not present in README, docs, screenshots, or committed files.
- [ ] `.env` remains ignored by `.gitignore`.
- [ ] Fallback logic is not removed.
- [ ] Scoring weights are unchanged.
