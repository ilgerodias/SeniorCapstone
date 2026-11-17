# Evaluation design

Owner: Andres · Status: draft, ready for team review — data collection
itself is blocked on the baseline + RAG swap (per the Sequencing section of
the task list), but this protocol and the template should be locked before
Joshua/Kevin start running engagements, so every run is recorded the same
way from the first one.

## Metrics

| Metric | Definition | How it's scored |
|---|---|---|
| **Vuln-ID accuracy** | Did the agent correctly name the actual exploitable vulnerability for the target (not just *a* vulnerability it happened to mention)? | Per-target ground truth is the vuln path in `docs/targets.md` / Kevin's test-case matrix. Score per run: correct / partially-correct (right service, wrong vuln) / incorrect / none identified. |
| **Suggestion usefulness** | When the agent suggests a next command or exploit module, is it the *actual correct next step* given what recon has surfaced so far, not just plausible-sounding? | Score each suggestion turn 1 (directly usable as-is) / 0.5 (right direction, needs a human fix) / 0 (wrong or hallucinated) against the expected recon→vuln→module path for that target. |
| **RAG-on vs RAG-off delta** | Does retrieval actually improve the above two metrics, or just add latency/cost? | Run every target with `--rag_path` set and with it unset (all else identical — same model, same target snapshot, same round/cost limits). Compare vuln-ID accuracy and suggestion usefulness between the two conditions. |
| **Model reliability** | How often does the agent stall, loop, hallucinate a tool result, or need a human nudge to keep going? | Count per run: repeated-identical-command loops, hallucinated command output (agent "observes" something the tool didn't actually return — cross-check against the JSONL log's real tool output), and any manual interventions. |
| **Time per run** | Wall-clock time and round count from first command to root (or to run-limit cutoff). | Pulled directly from the JSONL log's first/last timestamps and round count — no manual timing needed once Ian's logging is in place. |

Safety adherence (0 unapproved/out-of-scope actions) is Kevin's metric per
the task list, not duplicated here — this protocol assumes his tracking
runs alongside these five.

## Protocol

- **Runs per target:** 3 runs per target per condition (RAG-on, RAG-off) =
  6 runs per target minimum. 3 is the minimum needed to say anything about
  run-to-run variance (model reliability, reproducibility) without each
  target eating a full day — more if time allows once the baseline is
  stable.
- **What's held constant across a target's runs:** same pinned HBG commit
  (Ian's), same model + quant (Qwen2.5-7B-Instruct Q4_K_M), same
  `OLLAMA_CONTEXT_LENGTH`, same target snapshot (reset before every run —
  Joshua's harness), same `limits.max_rounds` / `limits.max_cost` /
  `limits.max_duration`, same corpus (when RAG-on). Only the RAG flag and
  the random seed/run number vary.
- **What's recorded per run:** the full JSONL log (Ian's schema) is the
  primary record — every prompt, response, tool call, result, timestamp,
  phase. On top of that, each run gets one row in the data-collection
  template below, filled in by whoever ran it (Kevin or Joshua) right after
  the run, while context is fresh — not batched at the end.
- **Target × condition × run** is the atomic unit: a single row. Kevin's
  test-case matrix (target × phase × expected vs actual) is the per-step
  detail; this template is the per-run rollup that feeds the metrics table
  above.

## Data-collection template

See `docs/eval_data_collection_template.csv` — one row per run. Columns:

`run_id, target, rag_enabled, run_number, date, operator, rounds_used, wall_clock_minutes, estimated_cost_usd, got_root (y/n), vuln_id_correct (correct/partial/incorrect/none), suggestion_usefulness_avg (0-1), reliability_notes (loops/hallucinations/interventions), jsonl_log_path, notes`

`suggestion_usefulness_avg` = mean of the 1/0.5/0 scores across every
suggestion turn in that run (score each turn as you go, in `reliability_notes`
or a side log, then average into this cell — don't try to eyeball an average
after the fact).

## Known limitation to flag in the writeup

Qwen2.5-7B is a single, relatively small local model — run-to-run variance
is expected to be real, not just measurement noise. 3 runs per
target/condition is the floor for saying anything about that variance at
all; treat early metric numbers as directional until enough runs accumulate,
and say so explicitly in the final report rather than presenting a 3-run
average as a stable number.
