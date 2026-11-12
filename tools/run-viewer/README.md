# HBG Run Viewer

A single-file, static browser viewer for hackingBuddyGPT per-run JSONL logs
(`logs/log-*.jsonl`). No server, no build step, no install, no upload — the file
is parsed entirely in your browser.

## Use

1. Open `index.html` in any modern browser (double-click, or `file://`).
2. Click **Open log** or drag a `log-*.jsonl` file onto the page.

QA can point it at their own run outputs the same way — just hand them
`index.html`.

## What it shows

- **Step timeline** — one entry per loop iteration (`round N`), in order.
- **Per-step detail** — the prompt sent, the model's answer, the tool called
  with its arguments, and the tool output.
- **Phases** — each step is labelled `recon` / `vuln-id` / `suggestion` /
  `exploit` and colour-coded (blue / amber / grey / red). Read from the engine's
  `hackingbuddygpt.phase` span attribute; if a log predates that field the viewer
  leaves the phase as `unknown`.
- **Approval gates** — human-in-the-loop events (`requested` / `approved` /
  `denied`, from `hackingbuddygpt.approval`) are shown as colour tags on the step.
- **Exploit / root** — the step that reached root (run state `got root`) is
  tagged `ROOT` in red.
- **Search / filter** — free-text across prompt/answer/command/output, plus
  filters by phase, by tool, and toggles for approval-only / exploit-only.
- **Report view + Print** — a clean linear layout for a final report; `Print`
  opens the browser print dialog (Save as PDF) with app chrome hidden.
- **Export JSON** — download the parsed (and currently filtered) run.
- **Malformed logs** — unparseable or truncated lines are skipped and counted in
  a banner; the rest of the run still loads.

## Schema

The log is one OpenTelemetry/GenAI span per line. Parsing mirrors the rules in
`src/hackingBuddyGPT/analysis/log_model.py` (spans de-duplicated by id, linked by
`parent_span_id`, steps = `round N` spans). See that module and
`src/hackingBuddyGPT/utils/log_storage.py` for the attribute keys.

### Known limitation

For the simple-text strategies, the engine logs the prompt as an unrendered
`mako.template.Template` object repr rather than the rendered prompt text, so the
"prompt sent" field shows a note instead of the actual prompt. This is an engine
logging issue, not a viewer one; fixing it means rendering the template before
logging in `call_response`.
