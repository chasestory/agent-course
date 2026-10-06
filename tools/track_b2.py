from common import M
V = "video"; D = "doc"
modules = [

M("b-human-approval", "Add human approval before risky actions",
  "Let the agent propose; let a human approve anything irreversible, expensive, or externally visible.",
  """
  ## Decide what counts as risky
  Classify every tool by blast radius:
  - **Auto-run:** reads, searches, drafts, sandboxed computation.
  - **Needs approval:** sending messages or emails, payments and refunds, deleting data, changing permissions, deploying, posting publicly.
  - **Never allowed:** anything outside the product's scope.
  Encode this in code (a policy table), not in the prompt. The model shouldn't be able to talk its way past it.

  ## Design the approval step
  - **Pause the workflow** at the risky call and persist its state (B11) so approval can take minutes or days.
  - Show the human **exactly** what will happen: recipient, amount, the full message, a diff. "Agent wants to do something" is useless.
  - Offer approve / edit / reject, and feed the decision back to the agent.
  - Log who approved what and when.

  ## Avoid approval fatigue
  If humans approve 200 requests a day, they'll click "yes" blindly. Reduce volume by auto-approving low-risk patterns (e.g., refunds under $20 for verified orders), batching similar requests, and tightening what the agent proposes. Track the approval rate and edit rate: lots of edits means the agent needs work.

  ## Graduate carefully
  As evals and history show reliability, you can move specific action types to auto-run with limits. Earn autonomy with data.
  """,
  [(D, "LangGraph docs: Interrupts (human-in-the-loop)", "https://docs.langchain.com/oss/python/langgraph/interrupts"),
   (D, "OWASP GenAI: LLM06 Excessive Agency", "https://genai.owasp.org/llmrisk/llm062025-excessive-agency/"),
   (D, "OpenAI Agents SDK: Guardrails", "https://openai.github.io/openai-agents-python/guardrails/")],
  [("Where should the 'this action needs approval' rule live?",
    ["In the system prompt only", "In code (a policy enforced at the tool layer)", "In the tool description", "Nowhere; trust the model"], 1,
    "Prompts can be ignored or manipulated. Enforce approval in code the model can't bypass."),
   ("What should an approval request show the human?",
    ["\"The agent wants to take an action.\"", "The exact action: recipient, amount, full content or diff", "Only the model's confidence score", "The full raw prompt"], 1,
    "Humans can only make good decisions with specific, concrete details."),
   ("Reviewers are approving 300 requests a day and rubber-stamping. Best fix?",
    ["Add more reviewers", "Auto-approve well-understood low-risk cases with limits, and batch or reduce the rest", "Remove approvals entirely", "Make the approve button bigger"], 1,
    "Approval fatigue destroys the safety value. Cut volume by risk-tiering."),
   ("True or false: a workflow waiting for approval should keep its state in memory only.",
    ["True", "False"], 1,
    "False. Approvals can take hours or days; persist state so the run survives restarts."),
  ]),

M("b-trace-everything", "Trace every model call and tool call",
  "If you can't see what the agent did, you can't fix it. Record every step as a structured trace.",
  """
  ## What a trace is
  A **trace** is the full record of one request or agent run, made of nested **spans**: each model call, tool call, retrieval, and validation step, with timing and parent/child relationships. Think of it as a call stack you can replay later.

  ## What to capture per span
  - **Model calls:** model and version, prompt (or prompt version + variables), output, token counts (input, cached, output), latency, cost, finish reason.
  - **Tool calls:** tool name, arguments, result (truncated), errors, latency.
  - **Context:** run ID, user/session ID (pseudonymous), feature, prompt version, git commit.
  Redact secrets and PII before storage (B15).

  ## Use a standard
  **OpenTelemetry** has semantic conventions for generative-AI spans, so traces can flow to many backends. LLM-focused tools (Langfuse, LangSmith, Arize Phoenix, provider dashboards) add prompt/response views, cost rollups, and eval hooks. Even a JSON-lines log with run_id and span_id is far better than nothing.

  ## Make traces useful
  - One click from a user complaint to the exact trace (show the run ID in your support tools).
  - Sample and read traces every week, not just when there's an incident.
  - Turn interesting traces into eval cases (B20).
  """,
  [(D, "OpenTelemetry: Semantic conventions for generative AI", "https://opentelemetry.io/docs/specs/semconv/gen-ai/"),
   (D, "Langfuse docs: Observability overview", "https://langfuse.com/docs/observability/overview"),
   (V, "Arize AI: How To Debug AI Agents: Tracing, Observability & Evals", "https://www.youtube.com/watch?v=nWNWrtCDqaY")],
  [("What is a span in a trace?",
    ["A billing unit", "One timed step (e.g., a model call or tool call) with parent/child links", "A type of embedding", "A UI component"], 1,
    "Traces are trees of spans; each span records one operation."),
   ("Which field is MOST important to include on model-call spans for later cost analysis?",
    ["The font used in the UI", "Token counts (input, cached, output) and model version", "The user's full credit card number", "The server's hostname only"], 1,
    "Tokens plus model let you compute cost per task. Never log sensitive data like card numbers."),
   ("Why use OpenTelemetry conventions?",
    ["They're required by all LLM providers", "Standard attributes make traces portable across observability backends", "They make models faster", "They encrypt prompts"], 1,
    "Standards avoid lock-in and let generic tools understand your spans."),
   ("True or false: you should only look at traces during incidents.",
    ["True", "False"], 1,
    "False. Regularly reading sampled traces reveals quiet failures before they become incidents."),
  ]),

M("b-debug-from-logs", "Debug a failing agent from its logs alone",
  "Reconstruct what the agent saw, what it decided, and where it went wrong, without re-running it.",
  """
  ## Why "logs alone"
  Agent failures are often not reproducible: different retrieval results, a changed API, sampling randomness. If your logs can't explain the failure, you're guessing. This skill forces good logging (B17) and disciplined reading.

  ## A debugging walkthrough
  1. **Find the run:** from the user report, get the run ID and open the trace.
  2. **Read the context the model actually saw,** not what you think the prompt is. Check system prompt version, retrieved docs, tool results, truncation.
  3. **Find the first wrong step.** The final answer is usually a symptom. Was it bad retrieval, a wrong tool choice, a bad argument, a tool error that was ignored, or a misread result?
  4. **Classify the root cause:** missing context, ambiguous instructions, bad tool design, tool or API bug, model limitation, or prompt injection.
  5. **Fix the cause, add the case to evals,** and verify the fix on the eval set.

  ## Common patterns
  - Tool returned an error, the model "smoothed over" it and answered anyway. Make errors loud and explicit.
  - Context got truncated, so the key instruction or document was silently dropped.
  - Loop: the same tool call repeated with the same arguments. Add loop detection.
  - The right doc was retrieved but buried under ten irrelevant ones.

  ## Think like the agent
  Read the exact context and ask: "With only this information, would a smart human make the same mistake?" If yes, the fix is the context or the tools, not the model.
  """,
  [(D, "Anthropic: Building effective agents", "https://www.anthropic.com/engineering/building-effective-agents"),
   (D, "Hamel Husain: A Field Guide to Rapidly Improving AI Products", "https://hamel.dev/blog/posts/field-guide/"),
   (D, "Arize Phoenix: OpenTelemetry and OpenInference tracing", "https://arize.com/docs/phoenix/tracing/concepts-tracing/otel-openinference/overview")],
  [("When debugging a bad final answer, what should you look for first?",
    ["The final answer's wording", "The first step where things went wrong (retrieval, tool choice, arguments, errors)", "The model's temperature", "The UI theme"], 1,
    "The final answer is usually a symptom. Find the earliest wrong step."),
   ("A tool returned 'ERROR: timeout' and the agent answered confidently anyway. What's the fix direction?",
    ["Hide tool errors from the model", "Make errors explicit and instruct/handle so the agent retries or reports it can't answer", "Use a bigger model", "Remove the tool"], 1,
    "Silent error-smoothing is common. Surface errors clearly and handle them in code and prompt."),
   ("Why read the exact context the model saw instead of your prompt template?",
    ["Templates are always wrong", "Retrieval, truncation, and variables can make the real context differ from what you assume", "It's shorter", "It's required by law"], 1,
    "Many bugs are in what actually got sent: missing docs, truncation, wrong prompt version."),
   ("After fixing the root cause, you should...",
    ["Close the ticket", "Add the case to your eval set and confirm the fix doesn't regress other cases", "Delete the logs", "Raise the temperature"], 1,
    "Every bug becomes a regression test."),
  ]),

M("b-grade-steps", "Grade the agent's steps, not just its final answer",
  "A right answer reached the wrong way is a future failure. Evaluate the trajectory.",
  """
  ## Why final-answer grading isn't enough
  An agent might get the right answer by luck, by calling 15 tools when 3 would do, or by taking a dangerous action along the way. Final-answer-only evals miss inefficiency, unsafe actions, and fragile reasoning.

  ## What to grade in a trajectory
  - **Tool selection:** did it call the right tool for each step?
  - **Arguments:** correct IDs, filters, and dates?
  - **Order and necessity:** did it check before acting? Any redundant or looping calls?
  - **Safety:** did it attempt anything forbidden or skip a required approval?
  - **Efficiency:** steps, tokens, and time compared to a reasonable budget.
  - **Recovery:** when a tool failed, did it handle it sensibly?

  ## How to grade
  - **Code checks on the trace:** "`get_order` called before `create_refund`", "no `send_email` without approval", "≤ 8 steps".
  - **Reference trajectories** for key cases, with tolerance (several valid orders may be fine).
  - **LLM judge over the trace** with a specific rubric for fuzzier questions ("Did the agent verify the customer's identity before discussing the order?").

  ## Balance
  Don't over-specify one exact path; agents may find valid alternatives. Grade **outcomes plus invariants** (must-do and must-never-do), not a single script.
  """,
  [(D, "Anthropic: Demystifying evals for AI agents", "https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents"),
   (D, "DeepLearning.AI short course: Evaluating AI Agents", "https://learn.deeplearning.ai/courses/evaluating-ai-agents"),
   (D, "OpenAI docs: Graders", "https://developers.openai.com/api/docs/guides/graders")],
  [("An agent gives the correct refund answer but issued the refund without checking the order exists. What does final-answer grading miss?",
    ["Nothing", "An unsafe/incorrect step in the trajectory", "The answer's tone", "Token count"], 1,
    "Trajectory grading catches skipped checks and unsafe actions even when the final answer looks fine."),
   ("Which is a good code-based trajectory check?",
    ["\"The answer sounds confident\"", "\"get_order is called before create_refund, and no send_email happens without approval\"", "\"Output is long\"", "\"Model used temperature 0\""], 1,
    "Invariants on tool order and forbidden actions are cheap, precise checks over traces."),
   ("Why avoid requiring one exact tool sequence for every case?",
    ["It's too cheap", "Agents can find multiple valid paths; over-specifying fails good runs", "Traces can't be parsed", "Tool order never matters"], 1,
    "Grade outcomes plus must-do and must-never invariants, allowing valid alternatives."),
   ("True or false: step count and token usage are legitimate things to evaluate.",
    ["True", "False"], 0,
    "True. Efficiency affects cost and latency, and runaway steps often signal confusion."),
  ]),

M("b-failures-to-tests", "Turn real user failures into test cases",
  "Production failures are your best eval data. Build the loop that captures them.",
  """
  ## The loop
  1. **Capture:** thumbs-down, user corrections, escalations, support tickets, validation failures, error spans.
  2. **Triage:** link each one to its trace; tag the failure type.
  3. **Convert:** write a test case with the input (PII scrubbed), relevant context, and the expected behavior.
  4. **Fix:** change the prompt, tools, retrieval, or code.
  5. **Verify:** the new case passes, and the rest of the suite didn't regress.

  ## Make capture easy
  - Add a one-click "report a problem" that stores the run ID.
  - Automatically flag runs with errors, retries, long loops, or low judge scores.
  - Review a sample weekly and label failure categories (open coding, then group the codes into themes).

  ## Write good test cases
  - Freeze the context that matters (retrieved docs, tool responses) with fixtures or mocks, so the test is reproducible.
  - Grade the specific behavior that broke ("must ask for the order number when it's missing"), not a whole golden answer.
  - Tag cases by category so you can see which failure types are improving.

  ## The payoff
  After a few months, your eval set reflects real usage, every past bug is guarded against, and model or prompt changes can be judged in minutes.
  """,
  [(D, "Hamel Husain: A Field Guide to Rapidly Improving AI Products", "https://hamel.dev/blog/posts/field-guide/"),
   (V, "Hamel Husain & Shreya Shankar: Why AI evals are the hottest new skill (Lenny's Podcast)", "https://www.youtube.com/watch?v=BsWxPI9UM4c"),
   (D, "Promptfoo docs: Intro", "https://www.promptfoo.dev/docs/intro/")],
  [("Why freeze tool responses and retrieved docs in a regression test?",
    ["To save storage", "So the test is reproducible and tests the agent's behavior, not changing external data", "Because tools are always wrong", "To make tests slower"], 1,
    "Fixtures isolate the behavior under test from external changes."),
   ("Best source of high-value eval cases?",
    ["Randomly generated text", "Real production failures (with PII scrubbed)", "Benchmark leaderboards", "The model's own suggestions only"], 1,
    "Real failures show exactly where your system breaks for real users."),
   ("A user reports a bad answer. What's essential to store with the report?",
    ["Their screen resolution", "The run/trace ID linking to the full context", "Nothing", "Their password"], 1,
    "The trace ID lets you see exactly what happened and build a faithful test."),
   ("True or false: once a failure is fixed, there's no need to keep its test case.",
    ["True", "False"], 1,
    "False. Keep it as a regression guard. Old bugs come back when prompts or models change."),
  ]),

M("b-block-deploys", "Block deploys when eval scores drop",
  "Make your eval suite a CI gate, so regressions can't ship quietly.",
  """
  ## Evals in CI
  Run your eval suite automatically on every pull request that touches prompts, tools, model config, or agent code. Compare against the main branch's baseline and **fail the check** if quality drops.

  ## Setting thresholds
  - **Absolute floor:** e.g., overall pass rate ≥ 90%.
  - **No-regression rule:** no more than X points below the baseline.
  - **Critical cases:** a small set (safety, money, compliance) that must always pass, 100%.
  - Account for noise: LLM outputs vary, so run flaky cases multiple times, use tolerances, or require a regression to reproduce before blocking.

  ## Practical setup
  - Keep a **fast suite** for PRs (tens to a few hundred cases, minutes) and a **full suite** nightly.
  - Cache model responses for unchanged cases where possible to save money.
  - Post a summary as a PR comment: score diff, newly failing cases, cost and latency deltas.
  - Use branch protection so the eval check is required before merge.

  ## Treat overrides seriously
  Sometimes you'll accept a regression for a bigger win. Make that an explicit, reviewed decision with a note, not someone quietly lowering the threshold.
  """,
  [(D, "Promptfoo docs: GitHub Action for LLM evals in CI", "https://www.promptfoo.dev/docs/integrations/github-action/"),
   (D, "GitHub docs: About protected branches", "https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches"),
   (D, "GitHub docs: Workflows", "https://docs.github.com/en/actions/concepts/workflows-and-actions/workflows")],
  [("Which PRs should trigger the eval suite?",
    ["Only README changes", "Changes to prompts, tools, model config, or agent code", "None; run evals monthly", "Only PRs from new contributors"], 1,
    "Anything that can change model behavior should be gated by evals."),
   ("How should you handle noise in LLM eval scores in CI?",
    ["Ignore it", "Use tolerances, repeat flaky cases, and keep a 100%-required critical set", "Set the threshold to 0%", "Disable the check when it fails"], 1,
    "Noise-aware thresholds prevent both false alarms and missed regressions."),
   ("Why split into a fast PR suite and a full nightly suite?",
    ["To hide failures", "Fast feedback on PRs at reasonable cost, with full coverage regularly", "Nightly runs are free", "PRs can't run evals"], 1,
    "Balance speed and cost against coverage."),
   ("True or false: quietly lowering the threshold to get a PR merged is fine.",
    ["True", "False"], 1,
    "False. Accepting a regression should be an explicit, reviewed decision."),
  ]),

M("b-canary-traffic", "Test new models on a slice of real traffic first",
  "Offline evals are necessary but not sufficient. Canary new models before full rollout.",
  """
  ## Why canary
  Your eval set never covers everything real users do. A new model or prompt can pass evals and still behave differently on the long tail: new formats, tone shifts, longer outputs, different tool habits, higher latency.

  ## Rollout ladder
  1. **Offline evals** pass (B21).
  2. **Shadow mode:** run the new model on real traffic in parallel, without showing users its output; compare offline.
  3. **Canary:** route a small slice (1–5%) of real traffic to the new version.
  4. **Ramp:** 10%, 25%, 50%, 100% as metrics hold.
  Keep a **one-switch rollback** (feature flag or config) at every stage.

  ## What to compare between control and canary
  - Quality signals: thumbs up/down, edit rate, escalation rate, validation failures, judge scores on sampled traces.
  - Cost per task, latency (p50/p95), error and timeout rates.
  - Segment by user type or task. Averages can hide a broken segment.

  ## Assignment hygiene
  Assign by user or session (sticky), not per request, so a user doesn't bounce between behaviors. Decide your success metrics and stop conditions **before** starting.
  """,
  [(D, "Martin Fowler: Canary Release", "https://martinfowler.com/bliki/CanaryRelease.html"),
   (D, "Google SRE Workbook: Canarying Releases", "https://sre.google/workbook/canarying-releases/"),
   (D, "Martin Fowler: Feature Toggles", "https://martinfowler.com/articles/feature-toggles.html")],
  [("A new model passes offline evals. What's the safest next step?",
    ["Switch 100% of traffic immediately", "Shadow or canary it on a small slice of real traffic with rollback ready", "Delete the old model", "Ask users to opt in by email"], 1,
    "Real traffic reveals long-tail behavior evals miss; small slices limit the blast radius."),
   ("What is shadow mode?",
    ["Dark UI theme", "Running the new version on real inputs without showing users its outputs, for comparison", "Running at night only", "Hiding logs"], 1,
    "Shadowing gives real-traffic comparisons with zero user impact."),
   ("Why assign canary traffic by user/session rather than per request?",
    ["It's cheaper", "Users get consistent behavior, and metrics aren't muddled", "Requests can't be routed", "It's required by providers"], 1,
    "Sticky assignment avoids confusing users and contaminating comparisons."),
   ("True or false: you should define success metrics and stop conditions before starting a canary.",
    ["True", "False"], 0,
    "True. Deciding afterwards invites cherry-picking."),
  ]),

M("b-provider-fallback", "Add a fallback when your model provider goes down",
  "Providers have outages, rate limits, and slowdowns. Plan for them before they happen.",
  """
  ## Failure modes to expect
  - Full outages and partial regional outages.
  - Rate limits (429), overloaded errors, sudden latency spikes.
  - Model deprecations and behavior changes.

  ## Resilience patterns
  - **Retries with exponential backoff and jitter** for transient errors. Respect `retry-after` headers; cap total attempts.
  - **Timeouts:** fail fast instead of hanging users.
  - **Fallback chain:** primary model → alternate region or deployment → different provider → smaller or local model → graceful degraded response.
  - **Circuit breaker:** after repeated failures, stop calling the failing provider for a cool-down period and go straight to the fallback.
  - **Queue non-urgent work** to run later instead of failing it.

  ## The hard part: behavioral differences
  A fallback model may format outputs differently or use tools differently. Mitigate:
  - Keep a **provider-agnostic interface** (or a gateway like LiteLLM) and per-model prompt variants.
  - Validate outputs with schemas (B12) regardless of model.
  - **Run your evals against the fallback model too,** so you know what quality you're falling back to.

  ## Practice
  Simulate an outage in staging (block the primary's API) and watch what users would see. Check provider status pages and alert on error-rate spikes.
  """,
  [(D, "Azure Architecture Center: Circuit Breaker pattern", "https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker"),
   (D, "LiteLLM docs: Reliability (retries, fallbacks)", "https://docs.litellm.ai/docs/proxy/reliability"),
   (D, "Azure Architecture Center: Retry pattern", "https://learn.microsoft.com/en-us/azure/architecture/patterns/retry")],
  [("What does a circuit breaker do?",
    ["Retries forever", "After repeated failures, temporarily stops calling the failing service and uses a fallback", "Shuts down your server", "Increases timeouts"], 1,
    "It prevents hammering a failing dependency and speeds up failover."),
   ("Why add jitter to exponential backoff?",
    ["To make retries slower for no reason", "To avoid many clients retrying in sync and overwhelming the service", "To randomize the model", "It's required by JSON"], 1,
    "Jitter spreads retries out so clients don't stampede the service at the same moment."),
   ("Biggest hidden risk of falling back to a different provider's model?",
    ["It's always cheaper", "Different output formats and tool behavior, causing downstream breakage or quality drops", "It never works", "Faster responses"], 1,
    "Validate outputs and evaluate the fallback model in advance."),
   ("True or false: you should run your eval suite on fallback models too.",
    ["True", "False"], 0,
    "True. Know the quality you'll get during an outage before you need it."),
  ]),

M("b-streaming", "Stream responses so users never wait on a spinner",
  "Show progress immediately. Perceived latency matters as much as real latency.",
  """
  ## Why stream
  A 12-second answer feels broken behind a spinner but fine if words start appearing in under a second. Streaming cuts **perceived** latency to roughly the time to first token (A7).

  ## How it works
  APIs send output incrementally, usually via **Server-Sent Events (SSE)**: a long-lived HTTP response with a series of `data:` events. Your backend relays chunks to the client (SSE or WebSockets), which renders them as they arrive.

  ## Streaming agents, not just text
  - Show **status events**: "Searching docs...", "Reading 3 results...", "Drafting reply...".
  - Stream tool-call progress and partial results where safe.
  - For structured output, stream into a buffer and validate at the end, or use partial-JSON parsing for progressive UI.

  ## Gotchas
  - **Proxies and buffering:** some proxies or serverless platforms buffer responses and break streaming. Disable buffering and test end to end.
  - **Errors mid-stream:** design a way to show "something went wrong" after partial output.
  - **Moderation and validation:** if you must check output before showing it, stream in sentence-sized chunks with checks, or accept a short delay.
  - **Cancellation:** let users stop generation, and stop paying for tokens you won't show.
  - Log the full final output and timings (TTFT, total).
  """,
  [(D, "Anthropic docs: Streaming messages", "https://platform.claude.com/docs/en/build-with-claude/streaming"),
   (D, "OpenAI docs: Streaming API responses", "https://developers.openai.com/api/docs/guides/streaming-responses"),
   (D, "MDN: Using server-sent events", "https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events")],
  [("What does streaming primarily improve?",
    ["Total tokens generated", "Perceived latency: users see output after roughly time-to-first-token", "Model accuracy", "Cost per token"], 1,
    "Streaming doesn't make generation faster overall; it makes waiting feel much shorter."),
   ("Streaming works locally but arrives all at once in production. Likely cause?",
    ["The model changed", "A proxy or platform is buffering the response", "Temperature too low", "The tokenizer"], 1,
    "Buffering proxies and some serverless setups collect the whole response first; disable buffering."),
   ("For an agent that takes 20 seconds of tool calls before answering, what improves UX most?",
    ["A bigger spinner", "Streaming status events like 'Searching docs...' as steps happen", "Hiding progress", "Making the user refresh"], 1,
    "Step-level progress keeps users informed during tool work."),
   ("True or false: you should support cancellation so users can stop a long generation.",
    ["True", "False"], 0,
    "True. It improves UX and avoids paying for unwanted tokens."),
  ]),

M("b-fine-tune-small", "Fine-tune a small model on your best outputs",
  "Distill a big model's best work on your task into a cheaper, faster small model.",
  """
  ## When it's worth it
  - The task is **narrow and stable** (classification, extraction, a specific format or tone).
  - A big model does it well, but cost or latency at your volume hurts.
  - Prompting a small model has plateaued on your evals.

  ## The distillation recipe
  1. Run the strong model on many real inputs (hundreds to thousands).
  2. **Filter to the best outputs:** passing evals, human-approved, or judge-scored. Garbage in, garbage out.
  3. Format as training examples (input → ideal output) in the provider's or library's format.
  4. Hold out a test split; fine-tune the small model (hosted fine-tuning, or LoRA/QLoRA on open weights).
  5. Evaluate the tuned model on **your eval suite**, compared to the big model and the untuned small model.

  ## Watch out for
  - **Overfitting** to training quirks; check on the held-out set and fresh traffic.
  - **Narrowing:** a tuned model can get worse at things outside the task. Keep it scoped.
  - **Data rights and privacy:** only train on data you're allowed to use; scrub PII.
  - **Maintenance:** new base models mean re-tuning; keep the pipeline scripted.

  ## Show the result
  | Model | Eval score | $/task | p95 latency |
  A good distillation keeps quality close to the big model at a fraction of the cost.
  """,
  [(D, "OpenAI docs: Supervised fine-tuning (including distillation)", "https://developers.openai.com/api/docs/guides/supervised-fine-tuning"),
   (D, "Hugging Face TRL: SFT Trainer", "https://huggingface.co/docs/trl/sft_trainer"),
   (D, "Hugging Face PEFT (LoRA and friends)", "https://huggingface.co/docs/peft/index")],
  [("What data should you fine-tune on when distilling?",
    ["Every output the big model produced, unfiltered", "Only the best outputs: eval-passing, human-approved, or high-scoring", "Random internet text", "The model's worst outputs"], 1,
    "Quality filtering is the core of good distillation. Training on mistakes teaches mistakes."),
   ("Which task is the best candidate for fine-tuning a small model?",
    ["Open-ended research on any topic", "High-volume, narrow extraction into a fixed format", "Tasks that change weekly", "Teaching the model today's news"], 1,
    "Narrow, stable, high-volume tasks get the most from distillation."),
   ("How do you know the fine-tune worked?",
    ["Training loss went down", "It matches or approaches the big model on your eval suite at lower cost", "It finished training", "It's smaller"], 1,
    "Training loss isn't task quality. Compare on your evals, including held-out data."),
   ("What is LoRA?",
    ["A tokenizer", "A parameter-efficient fine-tuning method that trains small added weight matrices", "A vector database", "A prompt format"], 1,
    "LoRA trains low-rank adapters instead of all weights, cutting memory and compute."),
  ]),

M("b-version-prompts", "Version prompts like code",
  "Prompts are production code. Review, version, test, and roll them back like code.",
  """
  ## Why
  A one-word prompt edit can change behavior for every user. If prompts live in a web dashboard with no history, or are scattered across code as string literals, you can't tell what changed when quality dropped.

  ## Practices
  - **Store prompts in the repo** as files (or a prompt registry with real version history), not ad-hoc strings scattered around.
  - **Give each prompt an ID and version;** log the version on every model call (B17).
  - **Review prompt changes in PRs** with eval results attached (B21).
  - **Template, don't concatenate:** a clear template with named variables, rendered in one place.
  - **Pin model versions** alongside prompts. Prompt + model + tools together define the behavior.
  - **Roll back** by deploying the previous version, ideally via config without a full redeploy.

  ## Changelog discipline
  For each version, note what changed, why, and the eval delta. Six months later this is how you answer "why does the prompt say that?"

  ## Experiment safely
  Run new prompt versions as canaries (B22) or A/B tests, keyed by prompt version in your traces, so you can compare real-world metrics per version.
  """,
  [(D, "Anthropic docs: Prompt engineering overview", "https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview"),
   (D, "Langfuse docs: Observability overview (incl. prompt versions in traces)", "https://langfuse.com/docs/observability/overview"),
   (D, "Semantic Versioning", "https://semver.org/")],
  [("Quality dropped yesterday. What makes this easy to diagnose?",
    ["Prompts edited live in a dashboard with no history", "Prompt versions logged on every call, plus prompt history in git", "Memory of who changed what", "Asking the model"], 1,
    "Versioned prompts plus per-call version logging let you correlate the drop with a specific change."),
   ("What together defines an LLM feature's behavior and should be versioned together?",
    ["Only the prompt", "Prompt + model version + tool definitions (and settings)", "Only the model", "The UI color"], 1,
    "Changing any of these can change behavior."),
   ("A good prompt PR includes...",
    ["Just the diff", "The diff plus eval results comparing old and new versions", "A screenshot of one output", "Nothing; prompts don't need review"], 1,
    "Eval deltas show the impact of a change beyond one example."),
   ("True or false: rolling back a prompt should be possible without rewriting it from memory.",
    ["True", "False"], 0,
    "True. Version history makes rollback a deploy or config change."),
  ]),

M("b-cost-latency-per-task", "Measure cost and latency per task",
  "Per-request metrics hide the truth. Measure what a whole task costs and how long users wait.",
  """
  ## Task, not request
  One user task (e.g., "resolve this ticket") may involve 6 model calls, 4 tool calls, and 2 retries. Per-request averages hide that. Roll metrics up to the **task (run) level** using run IDs in your traces (B17).

  ## Cost per task
  Sum over all model calls in the run:
  `input_tokens × input_price + cached_tokens × cached_price + output_tokens × output_price` (+ reasoning tokens, tool and API fees, embedding calls). Track the **distribution**, not just the mean; a few runaway runs can dominate spend.

  ## Latency per task
  - **TTFT** (or time to first visible progress) for interactive features.
  - **End-to-end** task time.
  - Report **p50 and p95** (and p99 at scale). Users remember the slow ones.
  - Break latency down by span: model vs. tools vs. retrieval vs. queueing, so you know where to optimize.

  ## Make it actionable
  - Dashboard by feature, model, and prompt version.
  - Alerts on cost-per-task spikes or p95 regressions.
  - Set **budgets** (max steps, max tokens, max dollars per run) enforced in code.
  - Report alongside quality: "$0.04/task, p95 6.1 s, 91% eval pass".
  """,
  [(D, "OpenAI docs: Latency optimization", "https://developers.openai.com/api/docs/guides/latency-optimization"),
   (D, "Google SRE Book: Monitoring Distributed Systems (latency percentiles)", "https://sre.google/sre-book/monitoring-distributed-systems/"),
   (D, "OpenTelemetry: Traces", "https://opentelemetry.io/docs/concepts/signals/traces/")],
  [("Why measure cost per task instead of per request?",
    ["It's simpler", "A task can involve many calls and retries; per-request numbers hide the real cost", "Providers bill per task", "Requests don't have costs"], 1,
    "Users experience tasks; roll up all calls in a run."),
   ("Why report p95 latency, not just the average?",
    ["Averages are illegal", "Tail latency reflects the slow experiences users notice and averages hide", "p95 is always lower", "It's cheaper to compute"], 1,
    "A good mean can hide a painful tail."),
   ("Mean cost per task is fine, but spend spiked. Likely cause to investigate?",
    ["A few runaway runs with excessive steps or tokens", "Users typing faster", "Dark mode", "Fewer requests"], 0,
    "Look at the distribution; outliers often dominate. Enforce per-run budgets."),
   ("True or false: you should enforce max steps or max dollars per run in code.",
    ["True", "False"], 0,
    "True. Budgets cap worst-case cost and catch loops."),
  ]),

M("b-readme-5min", "Write a README anyone understands in 5 minutes",
  "If people can't figure out what it does and how to run it fast, it doesn't exist.",
  """
  ## The 5-minute structure
  1. **One-line description:** what it is and who it's for.
  2. **Demo:** a screenshot, GIF, or a 60-second video link (B29).
  3. **Quickstart:** copy-paste commands from clone to running in under 5 steps.
  4. **What it does / doesn't do:** features and known limitations.
  5. **Configuration:** required env vars (names only, never values), with an `.env.example`.
  6. **How it works:** a short architecture overview (model, tools, data flow).
  7. **Evals and results:** how quality is measured and current numbers.
  8. **Troubleshooting** and how to get help or contribute.

  ## Write for the skimmer
  - Lead with outcomes, not history.
  - Short sections, real commands in code blocks, no walls of text.
  - Define jargon or link to it.
  - Test the quickstart on a clean machine (or ask a friend to). Fix every place they got stuck.

  ## For AI projects specifically
  State which models and providers it uses, rough cost per run, what data leaves the machine, and safety limits (what the agent can and can't do). That's what serious users check first.
  """,
  [(D, "Make a README", "https://www.makeareadme.com/"),
   (D, "GitHub docs: About READMEs", "https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes"),
   (D, "GitHub docs: Basic writing and formatting syntax", "https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax")],
  [("What should come first in a README?",
    ["The project's history", "A one-line description of what it is and who it's for", "The license", "A list of contributors"], 1,
    "Readers decide in seconds whether it's relevant; tell them what it is immediately."),
   ("How should a README handle API keys?",
    ["Include your real keys for convenience", "List required env var names with an .env.example; never include real values", "Tell users to email you for keys", "Hard-code them in the quickstart"], 1,
    "Document names and setup, never secrets."),
   ("Best way to validate your quickstart?",
    ["Read it once yourself", "Have someone follow it on a clean machine and fix where they get stuck", "Make it longer", "Add more badges"], 1,
    "Fresh eyes on a clean machine reveal missing steps."),
   ("For an AI agent project, which detail do serious users look for?",
    ["Font choice", "Models used, cost per run, what data leaves the machine, and what actions the agent can take", "Number of emojis", "Your favorite editor"], 1,
    "Cost, data flow, and safety boundaries are key adoption questions."),
  ]),

M("b-60s-demo", "Record a 60-second demo that shows it working",
  "A short, real demo beats a long explanation. Show the problem, the agent, the result.",
  """
  ## The 60-second script
  - **0–10 s: the problem.** "Every Monday I spend an hour triaging support tickets."
  - **10–45 s: the agent doing it, live.** Trigger, key steps (briefly visible), output.
  - **45–60 s: the result and the proof.** "Top 5 issues in 40 seconds; 92% agreement with our manual triage over 6 weeks."

  ## Make it real
  - Use **real (or realistic, scrubbed) data,** not a toy example.
  - Show it working end to end. Cutting out slow parts is fine if you say so ("sped up 4×").
  - Show one failure handled well, if possible (asks a clarifying question, flags low confidence). It builds trust.
  - No secrets or personal data on screen: check browser tabs, env vars, notifications.

  ## Production basics
  - Screen recorder: OBS, Loom, or your OS's built-in recorder. 1080p; zoom the UI so text is readable on a phone.
  - Record the voiceover separately or add captions; many viewers watch muted.
  - One take per section; trim dead air. Keep it under 60 seconds.

  ## Where it goes
  Top of your README (B28), your post about the project (B30), and anywhere you share the work. It's the single most persuasive artifact you can make.
  """,
  [(D, "OBS Studio: Quick Start Guide", "https://obsproject.com/kb/quick-start-guide"),
   (D, "Microsoft: Use Snipping Tool to capture screenshots and screen recordings", "https://support.microsoft.com/en-us/windows/apps/use-snipping-tool-to-capture-screenshots"),
   (D, "Loom (quick screen recording)", "https://www.loom.com/")],
  [("What should the first ~10 seconds of the demo show?",
    ["Your tech stack logos", "The problem being solved", "A long intro about yourself", "The code"], 1,
    "Viewers need to know why they should care before they see how."),
   ("Which makes a demo more credible?",
    ["A toy example with perfect results", "Real or realistic data, end to end, plus a measured result", "Only slides", "Hiding all agent steps"], 1,
    "Real data and numbers show it actually works."),
   ("Before recording, you should...",
    ["Open every browser tab", "Check that no secrets, keys, or personal data are visible on screen", "Turn off captions", "Make the font smaller"], 1,
    "Leaked keys or private info in demos are a common, avoidable mistake."),
   ("True or false: showing the agent gracefully handling one failure can increase trust.",
    ["True", "False"], 0,
    "True. It shows you've thought about real-world behavior, not just the happy path."),
  ]),

M("b-post-what-broke", "Post what broke and how you fixed it",
  "Public write-ups of failures build credibility faster than any certificate.",
  """
  ## Why write it up
  Anyone can claim skills. A post showing a real failure, how you diagnosed it, and the measured fix proves you can do the job. It also helps others and forces you to understand the problem fully.

  ## A blameless postmortem structure
  1. **Summary:** what broke, impact, duration, in two sentences.
  2. **Context:** what the system does (link the demo or README).
  3. **Timeline:** detection, investigation, fix.
  4. **Root cause:** the actual mechanism (e.g., "retrieval returned stale docs because the index refresh job silently failed").
  5. **Fix:** what changed, with before/after numbers.
  6. **Prevention:** the new eval case, alert, or guardrail.
  7. **Lessons:** what you'd do differently.

  ## Keep it blameless and specific
  Focus on systems and processes, not people. Include real artifacts (scrubbed): log excerpts, trace screenshots, eval tables, small code diffs. Specific numbers beat adjectives.

  ## Before publishing
  Remove secrets, customer data, internal hostnames, and anything under NDA. Get approval if it's work-related. Then post it where your peers are, and link it from your README and portfolio. Over a year, these posts become your strongest answer to "what did you ship?"
  """,
  [(D, "Google SRE Book: Postmortem Culture: Learning from Failure", "https://sre.google/sre-book/postmortem-culture/"),
   (D, "Anthropic: A postmortem of three recent issues", "https://www.anthropic.com/engineering/a-postmortem-of-three-recent-issues"),
   (D, "Simon Willison: Prompt injection explained (example of a clear write-up)", "https://simonwillison.net/2023/May/2/prompt-injection-explained/")],
  [("What does 'blameless' mean in a postmortem?",
    ["Nobody made a mistake", "Focus on system and process causes rather than blaming individuals", "Don't publish it", "Skip the root cause"], 1,
    "Blameless culture surfaces real causes because people aren't afraid to share details."),
   ("Which root-cause statement is most useful?",
    ["\"The AI was dumb.\"", "\"Retrieval returned stale docs because the nightly index refresh failed silently with no alert.\"", "\"Something went wrong.\"", "\"Bad luck.\""], 1,
    "Specific mechanisms lead to specific fixes and prevention."),
   ("What should you always remove before publishing?",
    ["The timeline", "Secrets, customer data, internal hostnames, and NDA-covered details", "The lessons learned", "The metrics"], 1,
    "Protect people and your organization. Scrub sensitive information."),
   ("True or false: a post-incident write-up should include how you'll prevent recurrence (e.g., a new eval case or alert).",
    ["True", "False"], 0,
    "True. Prevention closes the loop and shows engineering maturity."),
  ]),
]
