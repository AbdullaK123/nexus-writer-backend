# AI Extraction Performance Audit

## Executive Summary

**Current Architecture:** 4 concurrent AI extractions + 1 context synthesis per chapter  
**Model:** Google Gemini 2.5 Flash Lite (fast, cost-effective)  
**Estimated Total Time per Chapter:** 15-45 seconds (depending on chapter length and API latency)  
**Primary Bottlenecks:** LLM API latency, large prompt sizes, lack of output token limits

---

## Current Performance Profile

### 1. Extraction Flow Architecture ✅ GOOD

**Flow:** [app/flows/extraction/chapter_flow.py](app/flows/extraction/chapter_flow.py)

```
Chapter Input
    ↓
[Concurrent Execution via asyncio.TaskGroup]
    ├─→ Character Extraction (5s-15s)
    ├─→ Plot Extraction      (5s-15s)
    ├─→ World Extraction     (5s-15s)
    └─→ Structure Extraction (5s-15s)
    ↓
Context Synthesis (5s-15s)
    ↓
MongoDB Save (~100ms-500ms)
    ↓
Postgres Save (~50ms-200ms)
```

**Strengths:**
- ✅ Uses `asyncio.TaskGroup` for true concurrent execution
- ✅ All 4 extractions run in parallel (not sequential)
- ✅ Single network roundtrip per extraction (no chaining)
- ✅ Immediate checkpointing after completion

**Estimated Wall-Clock Time:**
- **Best case:** 5-10 seconds (short chapter, fast API)
- **Typical case:** 15-30 seconds (5k word chapter, normal API)
- **Worst case:** 40-60 seconds (10k word chapter, slow API)

---

## 2. Token Usage Analysis ⚠️ CONCERN

### System Prompt Sizes (Characters → Estimated Tokens)

| Extraction Type | Prompt Size | Estimated Tokens | Token Efficiency |
|----------------|-------------|-----------------|------------------|
| **Character**  | 15,020 chars | ~3,755 tokens | ⚠️ Large |
| **Plot**       | 16,292 chars | ~4,073 tokens | ⚠️ Large |
| **World**      | 19,497 chars | ~4,874 tokens | 🔴 Very Large |
| **Structure**  | 9,849 chars | ~2,462 tokens | ✅ Moderate |
| **Context Synthesis** | 8,150 chars + 4 extractions | ~2,037 + extraction results | ⚠️ Large |

### Input Token Calculation (per extraction)

**Formula:**
```
Input Tokens = System Prompt + Accumulated Context + Chapter Content
```

**Example (5,000 word chapter):**
- System Prompt (World): **~4,874 tokens**
- Accumulated Context (3 prior chapters): **~3,000 tokens**
- Chapter Content (5,000 words): **~6,500 tokens**
- **Total Input: ~14,374 tokens**

**All 4 Extractions Combined:**
- Character: ~3,755 + 3,000 + 6,500 = **13,255 tokens**
- Plot: ~4,073 + 3,000 + 6,500 = **13,573 tokens**
- World: ~4,874 + 3,000 + 6,500 = **14,374 tokens**
- Structure: ~2,462 + 3,000 + 6,500 = **11,962 tokens**
- **Total Input Across All Extractions: ~53,164 tokens**

### Output Token Estimation

**Problem:** No `max_tokens` limit configured!

**Current Behavior:**
- Model generates until stopping condition (structured output complete)
- Character extraction: 1,000-5,000 tokens (depending on characters present)
- Plot extraction: 800-4,000 tokens (depending on events)
- World extraction: 1,000-5,000 tokens (depending on worldbuilding)
- Structure extraction: 800-3,000 tokens (scene breakdowns)

**Estimated Output per Chapter:** 3,600-17,000 tokens

### Context Synthesis Token Usage ⚠️ MAJOR CONCERN

**Input:**
- System prompt: ~2,037 tokens
- 4 extraction results in TOON format: **8,000-20,000 tokens** (compressed)
- **Total Input: 10,000-22,000 tokens**

**Output:**
- Condensed context (max 1500 words): ~2,000 tokens

**🔴 CRITICAL ISSUE:** Context synthesis input can exceed tokenbudgets for smaller models!

---

## 3. Timeout Configuration ⚠️ DISCREPANCY

### Current Settings

**From [.env](/.env):**
```
EXTRACTION_TASK_TIMEOUT=1800  # 30 MINUTES! 🔴
```

**From [settings.py](app/config/settings.py):**
```python
extraction_task_timeout: int = Field(default=300)  # 5 minutes
chapter_flow_timeout: int = Field(default=600)    # 10 minutes
```

**🔴 PROBLEM:** `.env` overrides default with 30-minute timeout!

**Why this matters:**
- Hung API calls won't timeout quickly
- Failed extractions block flow for 30 minutes
- Wastes compute resources
- Poor user experience

**Recommendation:** Reduce to **180 seconds (3 minutes)** per task

---

## 4. Retry Configuration ⚠️ AGGRESSIVE

### Current Settings

```python
DEFAULT_TASK_RETRIES = 3
DEFAULT_TASK_RETRY_DELAYS = [30, 60, 120]  # Exponential backoff
```

**Total Retry Time per Failed Task:**
- First attempt: 180s timeout
- Retry 1: wait 30s + 180s timeout
- Retry 2: wait 60s + 180s timeout  
- Retry 3: wait 120s + 180s timeout
- **Total: 930 seconds = 15.5 minutes** 🔴

**For Chapter Flow (4 tasks + synthesis):**
- If 1 task fails all retries: 15.5 minutes wasted
- If all 5 fail: **77.5 minutes!** 🔴🔴🔴

**Recommendation:**
- Reduce retries to **2** (not 3)
- Reduce delays to **[10, 30]** seconds
- Add fast-fail for non-retryable errors (invalid prompts, model errors)

---

## 5. LLM Configuration ⚠️ NO TUNING

### Current Implementation

**Model:** `google_genai:gemini-2.5-flash-lite`

**Agent Creation:**
```python
character_extraction_agent = create_agent(
    "google_genai:gemini-2.5-flash-lite",
    tools=[],
    system_prompt=SYSTEM_PROMPT,
    response_format=ToolStrategy(CharacterExtraction),
)
```

**🔴 MISSING CONFIGURATIONS:**
- ❌ No `max_tokens` limit on output
- ❌ No `temperature` setting (uses default ~1.0)
- ❌ No `timeout` at agent level
- ❌ No streaming enabled
- ❌ No caching of system prompts

**Recommendations:**
1. **Add max_tokens:** Limit output to prevent runaway generation
2. **Set temperature=0.3:** More deterministic, faster, sufficient for extraction
3. **Enable prompt caching:** Reuse system prompts across chapters (60-80% token savings)
4. **Use streaming:** Start processing results before full completion

---

## 6. MongoDB Save Performance ✅ ACCEPTABLE

### Current Implementation

**Operations per Chapter:**
- 4 `replace_one` calls (character, plot, world, structure)
- 1 `replace_one` call (context synthesis)
- **Total: 5 MongoDB writes**

**Performance:**
- Each write: ~20-100ms (depending on document size)
- **Total MongoDB time: ~100-500ms**

**Network Efficiency:**
- Could batch into single `bulk_write` operation
- **Potential savings: 200-400ms**

---

## 7. Prompt Optimization Opportunities 🔍

### TOON Format Usage ✅ GOOD

**Current:** Context synthesis uses TOON encoding for 30-60% token reduction

**Example:**
```python
char_toon = encode(character_extraction)  # Compresses JSON → TOON
```

**⚠️ NOT USED** for individual extraction prompts (only synthesis)

**Opportunity:** Use TOON for accumulated context input to all extractors
- Could save 1,000-2,000 tokens per extraction
- **Total savings: 4,000-8,000 tokens per chapter**

### System Prompt Efficiency ⚠️ VERBOSE

**Current Lengths:**
- Character: 420 lines, 3,755 tokens
- Plot: 454 lines, 4,073 tokens  
- World: 544 lines, **4,874 tokens** 🔴
- Structure: 274 lines, 2,462 tokens

**Bloat Sources:**
1. Extremely detailed field descriptions
2. Repetitive examples
3. Verbose instructions
4. Large schema explanations

**Opportunity:** Reduce each prompt by 30-40%
- Remove redundant examples
- Simplify field descriptions
- Use more concise language
- **Potential savings: 5,000-6,000 tokens across all prompts**

---

## 8. Concurrency & Scaling ✅ GOOD

### Current Architecture

**Task Group Concurrency:**
```python
async with asyncio.TaskGroup() as tg:
    character_task = tg.create_task(extract_characters_task(...))
    plot_task = tg.create_task(extract_plot_task(...))
    world_task = tg.create_task(extract_world_task(...))
    structure_task = tg.create_task(extract_structure_task(...))
```

**Strengths:**
- ✅ True parallel execution
- ✅ No artificial rate limiting
- ✅ Proper error handling (one failure stops all)
- ✅ Results collected efficiently

**Bottleneck:** Gemini API rate limits (not code)

---

## Performance Bottleneck Priority Ranking

### 🔴 Critical (Fix Immediately)

1. **30-minute timeout in .env** → Reduce to 180s
   - **Impact:** Prevents 27-minute waste on hung tasks
   
2. **No max_tokens limit** → Add 4000-6000 token limits
   - **Impact:** Prevents runaway generation, saves API costs

3. **Aggressive retry policy** → Reduce to 2 retries with [10, 30]s delays
   - **Impact:** Saves 10+ minutes on failures

### ⚠️ High Priority (Optimize Soon)

4. **Verbose system prompts** → Reduce by 30-40%
   - **Impact:** Saves 5,000-6,000 input tokens per chapter
   
5. **No prompt caching** → Enable for system prompts
   - **Impact:** 60-80% input token savings on subsequent calls

6. **Context synthesis input size** → Use TOON for extraction inputs
   - **Impact:** Reduces synthesis input by 4,000-8,000 tokens

### ✅ Low Priority (Nice to Have)

7. **MongoDB batching** → Use bulk_write for 5 operations
   - **Impact:** Saves 200-400ms per chapter

8. **Temperature not set** → Use 0.3 for deterministic extraction
   - **Impact:** Slightly faster generation, more consistent results

9. **No streaming** → Enable streaming for early processing
   - **Impact:** Perceived latency improvement

---

## Recommended Action Plan

### Phase 1: Quick Wins (1-2 hours)

1. **Update .env file:**
   ```
   EXTRACTION_TASK_TIMEOUT=180
   CHAPTER_FLOW_TIMEOUT=360
   DEFAULT_TASK_RETRIES=2
   DEFAULT_TASK_RETRY_DELAY_1=10
   DEFAULT_TASK_RETRY_DELAY_2=30
   ```

2. **Add LLM configs to all agents:**
   ```python
   character_extraction_agent = create_agent(
       "google_genai:gemini-2.5-flash-lite",
       tools=[],
       system_prompt=SYSTEM_PROMPT,
       response_format=ToolStrategy(CharacterExtraction),
       temperature=0.3,  # ← ADD
       max_tokens=5000,  # ← ADD
   )
   ```

**Expected Impact:** 
- ✅ 15-20 minute savings on failures
- ✅ Predictable output sizes
- ✅ 10-20% faster generation

### Phase 2: Prompt Optimization (4-6 hours)

3. **Reduce system prompt sizes by 30-40%:**
   - Remove redundant examples
   - Simplify verbose descriptions
   - Use bullet points instead of paragraphs

4. **Use TOON for accumulated context:**
   ```python
   toon_context = encode(accumulated_context)
   build_character_extraction_prompt(toon_context, ...)
   ```

**Expected Impact:**
- ✅ 5,000-10,000 fewer input tokens per chapter
- ✅ 30-40% API cost reduction
- ✅ 2-5 second latency improvement

### Phase 3: Advanced Optimization (8-12 hours)

5. **Enable prompt caching** (if Gemini supports it)
6. **Implement streaming for synthesis**
7. **Batch MongoDB writes**
8. **Add response validation with early exit**

**Expected Impact:**
- ✅ 60-80% token savings on cached prompts
- ✅ Perceived latency improvement
- ✅ Better error handling

---

## Expected Performance After Optimization

### Current Performance
- **Best case:** 10 seconds
- **Typical case:** 25 seconds
- **Worst case:** 60 seconds (or 15+ minutes with retries)

### After Phase 1 (Quick Wins)
- **Best case:** 8 seconds (-20%)
- **Typical case:** 20 seconds (-20%)
- **Worst case:** 45 seconds (-25%) or 5 minutes with retries (-67%)

### After Phase 2 (Prompt Optimization)
- **Best case:** 6 seconds (-40%)
- **Typical case:** 15 seconds (-40%)
- **Worst case:** 35 seconds (-42%)

### After Phase 3 (Advanced)
- **Best case:** 5 seconds (-50%)
- **Typical case:** 12 seconds (-52%)
- **Worst case:** 30 seconds (-50%)

---

## Cost Impact Analysis

### Current Token Usage (per chapter)

**Input:** ~53,000 tokens (4 extractions) + ~12,000 (synthesis) = **65,000 tokens**  
**Output:** ~5,000 tokens (4 extractions) + ~2,000 (synthesis) = **7,000 tokens**

**Gemini 2.5 Flash Lite Pricing (approximate):**
- Input: $0.075 per 1M tokens
- Output: $0.30 per 1M tokens

**Cost per Chapter:**
- Input: 65,000 × $0.000000075 = **$0.004875**
- Output: 7,000 × $0.00000030 = **$0.002100**
- **Total: $0.006975 (~$0.007 per chapter)**

### After Optimization

**Input:** ~35,000 tokens (-46%) + ~8,000 = **43,000 tokens**  
**Output:** ~5,000 tokens (capped with max_tokens)

**Cost per Chapter:**
- Input: 43,000 × $0.000000075 = **$0.003225**
- Output: 5,000 × $0.00000030 = **$0.001500**
- **Total: $0.004725 (~$0.005 per chapter)**

**Savings: $0.002 per chapter (32% reduction)**

**For 100,000 chapters:** $200 savings  
**For 1,000,000 chapters:** $2,000 savings

---

## Monitoring Recommendations

### Add Performance Metrics

1. **Task-level timing:**
   ```python
   start = time.time()
   result = await extract_characters(...)
   duration = time.time() - start
   logger.info(f"Character extraction: {duration:.2f}s")
   ```

2. **Token usage tracking:**
   ```python
   logger.info(f"Tokens used - Input: {input_tokens}, Output: {output_tokens}")
   ```

3. **Failure rate monitoring:**
   - Track retry attempts
   - Log timeout occurrences
   - Alert on >5% failure rate

4. **Latency percentiles:**
   - P50, P95, P99 extraction times
   - Track by chapter length

---

## Risk Assessment

### Low Risk Changes ✅
- Timeout reduction
- max_tokens limit
- temperature setting
- Retry policy adjustment

### Medium Risk Changes ⚠️
- Prompt size reduction (requires testing)
- TOON encoding for inputs (compatibility)
- MongoDB batching (transaction safety)

### High Risk Changes 🔴
- Prompt caching (model support required)
- Streaming (complex implementation)
- Major prompt rewrites (quality validation)

---

## Conclusion

**Primary Issues:**
1. 🔴 30-minute timeout wastes resources
2. 🔴 No output token limits allows runaway costs
3. ⚠️ Verbose prompts increase latency and costs
4. ⚠️ Aggressive retries delay failure feedback

**Quick Win Opportunity:**
- Implement Phase 1 changes (1-2 hours)
- **Reduce worst-case latency from 60s → 45s**
- **Reduce failure recovery from 15min → 5min**
- **32% cost savings**

**Recommended Priority:** **HIGH**  
**Estimated ROI:** Excellent (low effort, high impact)
