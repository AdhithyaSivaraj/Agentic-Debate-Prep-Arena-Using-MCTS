# Project Issues, Root Causes, and Resolution Log
## "Agentic Debate Arena: Logic-Verified Argument Coaching"

This document records all technical challenges, root causes, and engineering resolutions encountered during the implementation of the Agentic Debate Arena.

---

## Executive Summary: Schedule Alignment & Status

- **Plan Alignment**: **100% On Plan (0% deviation)**.
- **Current Phase**: **Phase 9 (Live Local Execution & Maintenance)**.
- **Completed Phases**:
  - **Phase 0**: Project Scaffolding (40 stub files created).
  - **Phase 1**: Propositional Resolution Engine (`resolution.py` — 36 unit tests).
  - **Phase 2**: Monte Carlo Tree Search (`mcts.py` — 47 unit tests).
  - **Phase 3**: KnowledgeBase (TELL/ASK) & Semantic Retrieval (`knowledge_base.py`, `retrieval.py` — 52 unit tests).
  - **Phase 4**: OpenAI-Compatible Tool Schemas & Dispatcher (`tool_schemas.py`, `tool_executor.py`, `fact_generation.py` — 77 unit tests).
  - **Phase 5**: FastAPI Routes & Agent Integration (`routes_debate.py`, `main.py`, `gemini_agent.py`, `nemotron_agent.py`).
  - **Phase 6**: End-to-End Backend Integration (`test_e2e_backend.py` — 219 total backend tests passing).
  - **Phase 7**: React Frontend Component Scaffolding (`TopicSetup`, `DebateArena`, `AgentPanel`, `ClaimCard`, `ContradictionAlert`, `MCTSTracePanel`, `TranscriptLog`).
  - **Phase 8**: Frontend Styling, Animation & Visual Polish Pass (Cognitive Arena theme).

---

## Detailed Log of Issues & Technical Solutions

### Issue 1: Python Import Resolution (`ModuleNotFoundError: No module named 'api'`)
- **Symptom**: Running `python -m uvicorn app.main:app` or `./run_app.sh` threw `ModuleNotFoundError: No module named 'api'`.
- **Root Cause**: When executing from the `backend/` directory, Python's import system looked for `backend/api/` rather than adding `backend/app/` to `sys.path`.
- **Resolution**:
  1. Updated `backend/app/main.py` to add `sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))` at the top of the file.
  2. Updated `run_app.sh` to include `--app-dir "$BACKEND_DIR/app"` in the `uvicorn` invocation and set `PYTHONPATH="$BACKEND_DIR/app:$PYTHONPATH"`.

---

### Issue 2: Gemini API Rate Limits & Free Tier Quotas (`429 Quota Exceeded`)
- **Symptom**: Terminal output logged `Fact generation API call failed: 429 You exceeded your current quota... model: gemini-2.0-flash`.
- **Root Cause**: Rapid testing hit Google AI Studio's free tier requests-per-minute limit for `gemini-2.0-flash`.
- **Resolution**:
  - Engineered an automated, offline fallback fact generator (`_generate_fallback_facts()`) and offline fallback agent loop (`_run_agentic_loop()`).
  - Ensured that if live API calls fail or hit rate limits, the system seamlessly transitions to local algorithms so `/start-debate` and `/next-turn` always return `200 OK` / `201 Created`.

---

### Issue 3: OpenRouter Nemotron Endpoint Model Slug Mismatch (`404 Not Found`)
- **Symptom**: Terminal logged `Nemotron OpenRouter API call failed (Error code: 404 - No endpoints found for nvidia/llama-3.1-nemotron-ultra-253b-v1)`.
- **Root Cause**: OpenRouter updated or deprecated specific model slug strings on their free/public endpoints.
- **Resolution**:
  - Handled OpenRouter API exceptions gracefully in `nemotron_agent.py` to trigger the local MCTS fallback loop instead of crashing the server.
  - Updated `config.py` to use `nvidia/llama-3.1-nemotron-70b-instruct`.

---

### Issue 4: Gemini SDK Function Call Protobuf Object Type Mismatch
- **Symptom**: `_run_gemini_api_loop` threw `Gemini API call failed ('object')`.
- **Root Cause**: Passing a raw Python dictionary `{"parts": [...]}` to `chat.send_message()` when returning function execution results caused `google.generativeai` to raise a type error.
- **Resolution**:
  - Formatted tool execution output using standard Protobuf structures:
    ```python
    tool_proto = genai.protos.Part(
        function_response=genai.protos.FunctionResponse(
            name=fn_name,
            response=tool_res.output,
        )
    )
    response = chat.send_message(tool_proto)
    ```

---

### Issue 5: Recursive String Nesting Doll Loop in Offline Fallback
- **Symptom**: Over multiple turns, claims grew exponentially longer:
  `As Proposer, I assert: Directly refute 'As Opponent, I counter: Critique 'As Proposer, I assert: ...'`
- **Root Cause**: The offline candidate template performed literal string interpolation of the opponent's previous claim inside single quotes (`f"Directly refute '{opponent_last_claim}'"`), causing recursive text nesting on each turn.
- **Resolution**:
  - Created `_clean_opponent_summary()` in `gemini_agent.py` and `nemotron_agent.py`.
  - Stripped header prefixes (`As Proposer, I assert:`, `As Opponent, I counter:`) and truncated opponent claim references to max 50 characters, ensuring claim text remains concise, clear, and fixed in length across 50+ turns.

---

### Issue 6: Port Binding Collisions on Restart (`Errno 98 Address Already in Use`)
- **Symptom**: Re-running `./run_app.sh` failed with `[Errno 98] Address already in use`.
- **Root Cause**: Previous instances of `uvicorn` (port 8000) or `vite` (port 5173) remained active in the background.
- **Resolution**:
  - Added automatic port clearing (`fuser -k 8000/tcp 5173/tcp >/dev/null 2>&1`) to `run_app.sh` prior to starting servers, guaranteeing clean startups.

---

## Verification & Test Health

- **Backend Pytest Suite**: **219 / 219 tests passing**.
- **Frontend Production Build**: **`npm run build` succeeds in 1.05s with 0 errors**.
- **Execution Script**: `./run_app.sh` launches both servers cleanly.
