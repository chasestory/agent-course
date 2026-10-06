# Agent Course

> *Nobody asks for your certificate. They ask "what did you ship?"*

An offline desktop app that teaches practical agent engineering in short weekly modules. Each module has a short lesson, curated video and doc links that open in your browser, and a quiz with instant feedback. Progress is saved locally.

**52 modules in 3 tracks:**

| Track | Modules | What it covers |
|---|---|---|
| **Track 0: Math Foundations** (M1–M4) | 4 | Vectors and matrices, probability, derivatives, gradients |
| **Track A: Foundations** (A1–A18) | 18 | How LLMs work (tokens, transformers, embeddings, sampling, prefill/decode, local inference), building AI apps, prompting, RAG vs. agents, fine-tuning, hallucination, multimodal, evals, labeling, safety, working in AI |
| **Track B: Ship Agents** (B1–B30) | 30 | Shipping, evals, MCP, tools, memory, model selection and routing, cost, caching, durability, schemas, sandboxing, prompt injection, secrets/PII, approvals, tracing, debugging, CI gates, canaries, fallbacks, streaming, fine-tuning, prompt versioning, metrics, README, demo, postmortems |

All modules are unlocked, so you can go in any order. Suggested pace: one or two modules a week, and apply each one to something you're building.

## Run it (Windows)

Requires Rust (already installed on this machine at `%USERPROFILE%\.cargo\bin`). No Node or internet needed to run it; links open in your browser when you're online.

```powershell
cd $env:USERPROFILE\Documents\agent-course
.\run.ps1            # builds (first time ~1 min) and launches
```

Or manually:

```powershell
cargo run --release
# or after building:
.\target\release\agent-course.exe
```

To make a portable copy (exe + editable content + README in `dist\`):

```powershell
.\build.ps1
.\dist\agent-course.exe
```

Double-click `dist\agent-course.exe` from Explorer any time. You can pin it to Start or the taskbar.

If PowerShell refuses to run the scripts, use `powershell -ExecutionPolicy Bypass -File .\run.ps1` (or `build.ps1`).

Command-line flags:

```powershell
agent-course.exe --check                 # validate content, print counts and warnings, exit (non-zero on problems)
agent-course.exe --open b-mcp-server     # open straight to a module by id
cargo test --release                     # unit tests: scoring/completion rule + content integrity
```

## How it works

- **Home:** overall progress (X/52), a **Continue** button for the next incomplete module, and every track with per-module status (Not started / Best % / Complete).
- **Module page:** lesson → "Watch & read" links (click to open in your default browser) → quiz. Left sidebar shows every module with a status dot for quick navigation. Previous/Next buttons at the top and bottom.
- **Quiz:** click an answer to lock it in. You immediately see correct/incorrect plus an explanation. When all questions are answered you get your score.

### Completion rule

**A module is marked complete when one quiz attempt scores at least 70%.** Your best score is kept, and you can retake any quiz at any time. A later lower score never un-completes a module. (The threshold is `PASS_PCT` in `src/progress.rs`.)

### Where progress is stored

`%APPDATA%\agent-course\progress.json` (for example `C:\Users\powmi\AppData\Roaming\agent-course\progress.json`). It's plain JSON keyed by module id, so reordering or renaming modules keeps your progress as long as ids stay the same. To reset, use **Reset all progress…** at the bottom of the home screen, or delete the file. Override the location with the `AGENT_COURSE_PROGRESS` env var.

## Editing content

Content is data, one JSON file per track:

```
content/
  track-0-math.json
  track-a-foundations.json
  track-b-ship-agents.json
```

Each module looks like this:

```json
{
  "id": "b-mcp-server",
  "title": "Build an MCP server from scratch",
  "summary": "One-line summary shown on the home screen.",
  "lesson": ["## Section heading", "Paragraph text with **bold** and `code`.", "- bullet", "1. numbered"],
  "links": [{ "kind": "video", "title": "…", "url": "https://…" },
            { "kind": "doc",   "title": "…", "url": "https://…" }],
  "quiz": [{ "q": "Question?", "choices": ["A", "B", "C"], "answer": 1, "explain": "Why B is right and why the others aren't." }]
}
```

- `lesson` is markdown (an array of lines, or a single string). Supported: `##`/`###` headings, paragraphs, `-` bullets, `1.` lists, `>` quotes, fenced code blocks, inline `**bold**` and `` `code` ``.
- `answer` is the zero-based index into `choices`.
- To add a track, drop a new `track-*.json` in `content/` (set `"order"` to position it) and add it to the `EMBEDDED` list in `src/content.rs` if you want it baked into the exe.

**Live editing without rebuilding:** at startup the app loads `content\` next to the exe (the `dist\` layout), or `content\` in the current directory (`cargo run` from the repo). If neither exists, it uses the copy embedded at build time. The home screen footer shows which source it loaded, plus any JSON errors.

**Generator scripts (optional):** `tools/*.py` hold the same content as Python (nicer multi-line strings) and regenerate the JSON with `python track_0.py`, `python track_a.py`, `python track_b.py` from `tools/`. They also shuffle answer positions deterministically so the correct answer isn't always in the same slot. If you edit the JSON by hand, either keep editing JSON or port the change to the `.py` too, because re-running a generator overwrites its JSON file.

## Links policy

Every link was checked to resolve (HTTP 200) on 2026-10-05, and every YouTube link was checked to be a real video. Where no clearly good video existed, the module links to official docs instead (Anthropic, OpenAI, MCP, OWASP, Hugging Face, and others) rather than guessing.

## Project layout

```
agent-course/
  Cargo.toml          eframe/egui 0.31 (same stack as sysdash), serde, open
  src/main.rs         window setup
  src/app.rs          UI: home, module page, quiz, theme
  src/content.rs      content loading (disk override or embedded)
  src/progress.rs     progress JSON + completion rule
  src/markdown.rs     small markdown renderer for lessons
  content/*.json      the curriculum
  tools/*.py          optional content generators
  run.ps1 / build.ps1 convenience scripts
```

Stack choice: Node/npm aren't installed on this machine, so this uses the brief's Option B: a native Rust **eframe/egui** app, matching `sysdash`.
