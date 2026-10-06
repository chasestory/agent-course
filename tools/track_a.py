from common import M, write

V = "video"; D = "doc"
modules = [

M("a-llm-basics", "LLM basics: tokens, next-token prediction, context window",
  "What a large language model actually does, in one sentence: predict the next token, over and over.",
  """
  ## The one-sentence model
  An LLM is a function that takes a sequence of **tokens** and outputs a probability distribution over the next token. Generation is just a loop: pick a token from that distribution, append it, run again. Everything else (chat, tools, "reasoning") is built on that loop.

  ## Pretraining vs. post-training
  - **Pretraining:** predict the next token on a huge pile of text. This is where knowledge and fluency come from.
  - **Post-training:** instruction tuning and preference training (RLHF and similar) turn a text-completer into an assistant that follows instructions, refuses some requests, and uses tools.
  - The model has no live access to the world. Anything after its training cutoff, or private to you, must be put in the prompt (or fetched with tools).

  ## The context window is the model's entire working memory
  The **context window** is the max number of tokens (input + output) per call. The model is stateless between calls: a "conversation" is your app re-sending the history every turn. Practical consequences:
  - Long chats cost more each turn because you re-send everything.
  - If a fact isn't in the context (or the weights), the model doesn't know it.
  - Bigger windows help, but stuffing them full can still bury the important part. Curate context; don't dump it.

  ## Try this
  Paste a paragraph into a tokenizer viewer and count tokens vs. words. Then ask a model about something that happened last week and watch it either refuse or confidently make something up. That gap is why tools and retrieval exist.
  """,
  [(V, "3Blue1Brown: Large Language Models explained briefly", "https://www.youtube.com/watch?v=LPZh9BOjkQs"),
   (V, "Andrej Karpathy: [1hr Talk] Intro to Large Language Models", "https://www.youtube.com/watch?v=zjkBMFhNj_g"),
   (D, "Anthropic docs: Context windows", "https://platform.claude.com/docs/en/build-with-claude/context-windows")],
  [("At its core, what does an LLM compute on each forward pass?",
    ["A full answer, planned in advance", "A probability distribution over the next token", "A database lookup of the closest stored answer", "A parse tree of the user's question"], 1,
    "The model outputs next-token probabilities; full answers emerge from repeating that step. It doesn't retrieve stored answers or plan the whole reply up front as a separate artifact."),
   ("A chat model 'remembers' what you said three turns ago mainly because...",
    ["It updates its weights after each message", "The app re-sends the conversation history inside the context window", "It stores a per-user memory vector on the provider's servers", "Transformers have built-in long-term memory"], 1,
    "Models are stateless per call. The app re-sends history (or a summary). Weights don't change during chat; any 'memory feature' is an app layer that also ends up injecting text into context."),
   ("True or false: if a model's context window is 200k tokens, you can always paste 200k tokens of documents and get an answer.",
    ["True", "False"], 1,
    "False. The window covers input AND output, so you must leave room for the reply. And even when it fits, burying the key fact in a huge context can hurt quality and costs more."),
   ("Where does an assistant's ability to follow instructions and refuse harmful requests mostly come from?",
    ["Pretraining on raw internet text", "Post-training (instruction tuning, preference training)", "The tokenizer", "The context window size"], 1,
    "Pretraining gives knowledge and fluency; post-training shapes behavior: following instructions, format, refusals, tool use."),
  ]),

M("a-tokens", "Tokens and tokenization (BPE, why length ≠ words)",
  "Models read tokens, not words or characters. That affects cost, limits, and some weird failures.",
  """
  ## What a token is
  A tokenizer splits text into chunks from a fixed vocabulary (often 100k–200k entries). Common words are a single token; rare words, names, code, and non-English text get split into several. A rough rule for English: **about 3/4 of a word per token**, so 1,000 tokens is about 750 words. Use the real tokenizer for anything that matters.

  ## How BPE builds the vocabulary
  **Byte Pair Encoding** starts from bytes (or characters) and keeps merging the most frequent adjacent pair into a new token until the vocabulary is full. Frequent strings become single tokens; everything else stays representable as smaller pieces, so no input is ever "unknown".

  ## Why you should care
  - **Cost and limits** are counted in tokens. The same message can cost very different amounts in English, Japanese, or minified JSON.
  - **Character-level tasks are hard.** Counting letters, reversing strings, or exact spelling trip models up because they never see individual characters.
  - **Whitespace and formatting matter.** " hello" and "hello" are different tokens, and verbose JSON keys burn tokens on every call.
  - Different model families use **different tokenizers**, so token counts don't transfer between providers.

  ## Try this
  Open a tokenizer viewer and compare: a sentence of English, the same sentence in another language, a UUID, and a block of indented code. Note which one is most "expensive" per character.
  """,
  [(V, "Andrej Karpathy: Let's build the GPT Tokenizer", "https://www.youtube.com/watch?v=zduSFxRajkE"),
   (D, "Hugging Face LLM Course: Byte-Pair Encoding tokenization", "https://huggingface.co/learn/llm-course/chapter6/5"),
   (D, "Tiktokenizer (interactive token viewer)", "https://tiktokenizer.vercel.app/")],
  [("Roughly how many English words are in 1,000 tokens?",
    ["About 250", "About 750", "Exactly 1,000", "About 4,000"], 1,
    "A common rule of thumb for English is ~0.75 words per token. It varies by text and tokenizer, so measure when it matters."),
   ("Why do LLMs often fail at 'how many r's are in strawberry'-style questions?",
    ["They are bad at math in general", "They see tokens, not individual characters", "The question is ambiguous", "Their context window is too small"], 1,
    "A word may be one or a few tokens, so the model never directly sees the letters. Character-level questions are a blind spot that comes from tokenization."),
   ("In BPE, how are new vocabulary entries created?",
    ["By merging the most frequent adjacent pair of existing tokens, repeatedly", "By splitting text on spaces only", "By assigning one token per dictionary word", "By random sampling of substrings"], 0,
    "BPE greedily merges frequent pairs until the vocab size is reached. Splitting on spaces or dictionary words wouldn't handle new words, code, or other languages."),
   ("True or false: a 10,000-token prompt for one provider's model will be about 10,000 tokens for every other provider too.",
    ["True", "False"], 1,
    "False. Tokenizers differ across model families, so counts (and costs) differ. Always count with the target model's tokenizer."),
  ]),

M("a-neural-networks", "Neural networks: layers, weights, training vs. inference",
  "The minimum mental model of what's inside: weighted sums, nonlinearities, and gradient descent.",
  """
  ## Layers and weights
  A neural network is layers of simple units. Each unit computes a **weighted sum** of its inputs, adds a bias, and applies a **nonlinearity** (like ReLU). Stack many layers and the network can represent very complex functions. The **weights** (parameters) are just numbers; a "7B model" has about 7 billion of them.

  ## Training: adjust weights to reduce a loss
  1. Run inputs forward to get a prediction.
  2. Compute a **loss** (how wrong it was). For LLMs: how much probability it gave the true next token.
  3. **Backpropagation** computes how each weight affected the loss (the gradient).
  4. **Gradient descent** nudges every weight a little in the direction that lowers the loss.
  5. Repeat over trillions of tokens. This is the expensive part: huge GPU clusters for weeks.

  ## Inference: weights frozen, just run forward
  Inference is only the forward pass with fixed weights. It's much cheaper per token than training, but you do it on every request, forever. That's why inference cost and latency dominate product economics.

  ## Why this matters for builders
  - Prompting and retrieval change the **input**, never the weights.
  - Fine-tuning is just more training on your data: it changes the weights.
  - "The model learned from my chat" is false unless someone actually trains on it later.
  """,
  [(V, "3Blue1Brown: But what is a neural network?", "https://www.youtube.com/watch?v=aircAruvnKk"),
   (V, "3Blue1Brown: Gradient descent, how neural networks learn", "https://www.youtube.com/watch?v=IHZwWFHWa-w"),
   (D, "Andrej Karpathy: A Recipe for Training Neural Networks", "https://karpathy.github.io/2019/04/25/recipe/")],
  [("What changes during inference?",
    ["The weights", "Only the inputs and activations; the weights are frozen", "The loss function", "The number of layers"], 1,
    "Inference is a forward pass with fixed weights. Training is what changes weights."),
   ("What does backpropagation compute?",
    ["The final answer", "How much each weight contributed to the loss (gradients)", "The tokenizer vocabulary", "The best prompt"], 1,
    "Backprop computes gradients; gradient descent then uses them to update weights."),
   ("Why does a network need nonlinear activation functions?",
    ["To make it run faster", "Without them, stacked layers collapse into one linear function", "To reduce memory", "To normalize the tokens"], 1,
    "A stack of purely linear layers is still linear. Nonlinearities let depth add expressive power."),
   ("True or false: adding retrieved documents to a prompt changes the model's weights.",
    ["True", "False"], 1,
    "False. Retrieval and prompting only change the input. Only training/fine-tuning changes weights."),
  ]),

M("a-transformers", "Transformers and attention (self-attention, why it scales)",
  "How every token looks at every other token, and why that architecture took over.",
  """
  ## The problem attention solves
  Meaning depends on context: "bank" near "river" vs. near "loan". Older models (RNNs) passed context along one step at a time, which was slow to train and forgot distant words. **Self-attention** lets every token look directly at every other token in one step.

  ## Self-attention in plain terms
  Each token is turned into three vectors:
  - **Query:** what am I looking for?
  - **Key:** what do I contain?
  - **Value:** what do I pass along if someone attends to me?
  Each token scores its query against all keys, turns the scores into weights (softmax), and takes a weighted mix of the values. Many **heads** do this in parallel to capture different relationships. In decoder LLMs a **causal mask** stops tokens from looking at future tokens.

  ## A transformer block
  Attention (tokens share information) followed by an MLP (each token processed on its own), with residual connections and normalization. Stack dozens of blocks and you have a GPT-style model.

  ## Why it scales
  - Training is **parallel across the whole sequence**, a perfect fit for GPUs.
  - Quality improves predictably with more parameters, data, and compute.
  - The catch: attention cost grows with the **square** of sequence length, which is why long contexts are expensive and why there's so much work on efficient attention and KV caching.
  """,
  [(V, "3Blue1Brown: Attention in transformers, step-by-step", "https://www.youtube.com/watch?v=eMlx5fFNoYc"),
   (D, "Jay Alammar: The Illustrated Transformer", "https://jalammar.github.io/illustrated-transformer/"),
   (D, "Transformer Explainer (interactive)", "https://poloclub.github.io/transformer-explainer/")],
  [("In self-attention, what decides how much token A pays attention to token B?",
    ["Their distance in the text only", "The match between A's query and B's key", "Alphabetical order", "B's value vector alone"], 1,
    "Attention weights come from query-key similarity (then softmax). Values are what gets mixed in, not what decides the weights."),
   ("Why does a decoder-only LLM use a causal mask?",
    ["To speed up tokenization", "So tokens can't see future tokens it's trying to predict", "To reduce the vocabulary", "To enable multiple heads"], 1,
    "When training on next-token prediction, letting a position see the future would be cheating. The mask blocks it."),
   ("Main reason transformers trained much faster than RNNs at scale?",
    ["Fewer parameters", "They process all positions of a sequence in parallel", "They don't need GPUs", "They use smaller vocabularies"], 1,
    "RNNs are sequential per step; transformers compute attention for all positions at once, which suits GPUs."),
   ("How does naive self-attention cost grow with sequence length n?",
    ["Linearly (n)", "Quadratically (n²)", "Logarithmically", "It's constant"], 1,
    "Every token attends to every other token: n×n scores. That's why long context is costly."),
  ]),

M("a-embeddings", "Embeddings and similarity (vectors, cosine, semantic search)",
  "Turn text into vectors so 'similar meaning' becomes 'nearby in space'.",
  """
  ## What an embedding is
  An embedding model maps a piece of text to a fixed-length vector (say 768 or 1536 numbers). It's trained so that texts with similar meaning end up **close together**. "How do I reset my password?" and "forgot login credentials" land near each other even with no shared words.

  ## Measuring similarity
  - **Cosine similarity:** the angle between vectors; 1 means the same direction. The default for most text embeddings.
  - **Dot product:** same ranking as cosine when vectors are normalized (many providers normalize).
  - Similarity is **relative**. A score of 0.8 means nothing on its own; compare candidates and set thresholds from your own data.

  ## Semantic search in four steps
  1. Chunk your documents (paragraphs or sections, not whole PDFs).
  2. Embed every chunk once and store vectors plus the original text.
  3. At query time, embed the query and find the nearest chunks (a vector index or plain numpy for small sets).
  4. Hand the top chunks to the LLM or the user.

  ## Gotchas
  - Embeddings are bad at **exact matches** (SKUs, error codes, names). Combine with keyword search (BM25): **hybrid search**.
  - Query and documents must use the **same embedding model**. Switching models means re-embedding everything.
  - Chunking quality often matters more than which vector database you pick.
  """,
  [(D, "OpenAI docs: Vector embeddings", "https://developers.openai.com/api/docs/guides/embeddings"),
   (D, "Jay Alammar: The Illustrated Word2vec", "https://jalammar.github.io/illustrated-word2vec/"),
   (D, "Sentence Transformers documentation", "https://sbert.net/")],
  [("What property makes embeddings useful for search?",
    ["They compress text losslessly", "Texts with similar meaning map to nearby vectors", "They count keywords", "They encrypt the text"], 1,
    "Embeddings are trained so semantic similarity becomes geometric closeness. They're lossy and aren't keyword counts."),
   ("A user searches for error code 'E-4021' and semantic search returns vaguely related docs. Best fix?",
    ["Use a bigger LLM", "Add keyword/BM25 search (hybrid search)", "Increase the embedding dimensions", "Lower the temperature"], 1,
    "Exact tokens like codes and SKUs are where embeddings are weak. Hybrid search combines lexical precision with semantic recall."),
   ("You switch to a new embedding model for queries but keep old document vectors. What happens?",
    ["Nothing; vectors are universal", "Search quality breaks because the vector spaces don't match", "It gets faster", "Only the scores shift slightly"], 1,
    "Different models produce incompatible spaces. Re-embed the corpus when you change models."),
   ("True or false: a cosine similarity of 0.82 always means 'relevant'.",
    ["True", "False"], 1,
    "False. Score scales differ by model and domain. Calibrate thresholds on labeled examples from your data."),
  ]),

M("a-sampling", "Sampling and decoding: temperature, top-p, determinism",
  "Why the same prompt gives different answers, and which knobs actually matter.",
  """
  ## From probabilities to text
  The model gives a probability for every possible next token. A **decoding strategy** picks one:
  - **Greedy:** always take the most likely token. Repeatable, but can be bland or loop.
  - **Sampling:** draw randomly according to the probabilities. More varied.

  ## The knobs
  - **Temperature** reshapes the distribution. Low (0–0.3) is sharper and more predictable; high (0.8+) is flatter and more creative, with more mistakes.
  - **Top-p (nucleus):** only sample from the smallest set of tokens whose probabilities add up to p (e.g., 0.9). Cuts off the weird tail.
  - **Top-k:** only sample from the k most likely tokens.
  - **Max tokens** caps output length (and cost). **Stop sequences** end generation early.
  Rule of thumb: tune temperature *or* top-p, not both at once. Some newer reasoning models fix or ignore these settings, so check the docs.

  ## Determinism is not guaranteed
  Even at temperature 0, hosted APIs can return slightly different outputs (batching, hardware, model updates). Design for it:
  - For extraction and classification: low temperature **plus** schema validation.
  - For tests: assert on properties (valid JSON, contains the right ID), not exact strings.
  - Pin model versions so behavior doesn't drift silently.
  """,
  [(D, "Hugging Face: How to generate text (decoding methods)", "https://huggingface.co/blog/how-to-generate"),
   (D, "Hugging Face Transformers: Generation strategies", "https://huggingface.co/docs/transformers/main/en/generation_strategies")],
  [("You need consistent JSON field extraction. Which setting is the sensible starting point?",
    ["Temperature 1.2", "Low temperature (around 0–0.2) plus schema validation", "Top-k = 1000", "No max tokens"], 1,
    "Extraction wants predictability. Low temperature reduces variation; validation catches what still goes wrong."),
   ("What does top-p = 0.9 do?",
    ["Picks the top 90 tokens", "Samples only from the smallest set of tokens whose probabilities sum to 0.9", "Sets temperature to 0.9", "Limits output to 90% of max tokens"], 1,
    "Nucleus sampling trims the low-probability tail by cumulative probability, not a fixed count (that's top-k)."),
   ("True or false: temperature 0 on a hosted API guarantees byte-identical output forever.",
    ["True", "False"], 1,
    "False. Infrastructure nondeterminism and model updates can change outputs. Test properties, pin versions."),
   ("Higher temperature generally...",
    ["Makes outputs more random and diverse", "Makes the model smarter", "Reduces cost", "Increases the context window"], 0,
    "Temperature flattens the distribution, so less likely tokens get picked more often. It doesn't add capability or change cost per token."),
  ]),

M("a-prefill-decode", "Prefill vs. decode (TTFT, tokens/sec, KV cache)",
  "The two phases of every LLM call, and which one your latency problem lives in.",
  """
  ## Two phases
  - **Prefill:** the model processes your whole prompt in parallel and builds internal state. This mostly determines **time to first token (TTFT)**. Long prompts mean longer prefill.
  - **Decode:** the model generates output **one token at a time**, each step depending on the last. This sets **tokens per second** and total generation time. Long outputs mean long decode.
  Prefill is compute-bound (lots of parallel math). Decode is usually memory-bandwidth-bound (reading all the weights for every single token).

  ## KV cache intuition
  During decode, each new token needs attention over all previous tokens. Recomputing their keys and values every step would be wasteful, so the server **caches the keys and values (KV cache)**. It costs GPU memory proportional to context length × batch size, which is why long contexts limit how many users a GPU can serve at once.

  ## Prompt caching builds on this
  Providers can reuse the prefill work for an identical **prompt prefix** across requests. Put stable content (system prompt, tool definitions, big docs) first and variable content last to get cache hits: lower TTFT and cheaper input tokens.

  ## Reading latency numbers
  - Slow to start, fast once going: a prefill problem. Shrink or cache the prompt.
  - Starts fast, takes forever: a decode problem. Ask for shorter outputs, use a faster model, stream.
  - Total latency ≈ TTFT + (output tokens ÷ tokens per second).
  """,
  [(D, "NVIDIA: Mastering LLM Techniques: Inference Optimization", "https://developer.nvidia.com/blog/mastering-llm-techniques-inference-optimization/"),
   (D, "Hugging Face Transformers: Cache strategies (KV cache)", "https://huggingface.co/docs/transformers/main/en/kv_cache"),
   (D, "OpenAI docs: Latency optimization", "https://developers.openai.com/api/docs/guides/latency-optimization")],
  [("Your app has a 30k-token system prompt and short answers. Users complain it 'takes a while to start'. Which phase is the bottleneck?",
    ["Decode", "Prefill", "Tokenization", "Network DNS"], 1,
    "Long input with short output means TTFT is dominated by prefill. Shorten the prompt or use prompt caching."),
   ("What does the KV cache store?",
    ["Previous user sessions", "Keys and values for tokens already processed, so they aren't recomputed each decode step", "The model weights", "Final answers for reuse"], 1,
    "It caches attention keys/values within a generation. Response caching (reusing answers) is a different, app-level idea."),
   ("Why is decode typically slower per token than prefill?",
    ["Decode uses a different model", "Decode is sequential, one token at a time, and memory-bandwidth-bound", "Prefill skips attention", "Decode runs on CPU"], 1,
    "Prefill parallelizes across all prompt tokens; decode must generate tokens one after another."),
   ("To maximize prompt-cache hits, you should place...",
    ["Variable user input first, static instructions last", "Static content (system prompt, tools, docs) first, variable input last", "Everything in random order", "Tools at the very end"], 1,
    "Caches match on an identical prefix. Anything variable early in the prompt breaks the prefix for everything after it."),
   ("Total response time is roughly...",
    ["TTFT + output tokens ÷ tokens per second", "Input tokens × temperature", "Context window ÷ batch size", "Always constant"], 0,
    "A simple, useful model: time to first token plus generation time."),
  ]),

M("a-local-inference", "Local inference (llama.cpp, Ollama, GGUF, GPU vs. CPU)",
  "Running open-weight models on your own machine: what fits, what it costs, when it's worth it.",
  """
  ## The stack
  - **llama.cpp:** a fast C/C++ inference engine that runs on CPU, NVIDIA (CUDA), Apple Silicon (Metal), and more.
  - **GGUF:** the single-file model format llama.cpp uses. It bundles weights, tokenizer, and metadata, usually **quantized**.
  - **Ollama / LM Studio:** friendly wrappers. `ollama run <model>` downloads and serves a model with an OpenAI-compatible local API.

  ## Quantization, or why a 7B model fits on a laptop
  Weights are stored at fewer bits (e.g., 4-bit instead of 16-bit). Rough memory math: **parameters × bits ÷ 8**, plus overhead for the KV cache. A 7B model at 4-bit is about 4–5 GB; at 16-bit it's about 14 GB. Lower bits are smaller and faster, with some quality loss; Q4–Q5 variants are a common sweet spot.

  ## GPU vs. CPU
  - Decode speed is limited by **memory bandwidth**, so GPU VRAM (very high bandwidth) beats system RAM by a lot.
  - If the model fits entirely in VRAM, it's fast. If layers spill to CPU RAM, it slows down sharply.
  - CPU-only works for small models and batch jobs, just slowly.

  ## When local makes sense
  - Privacy or offline needs, high-volume simple tasks, development and testing, cost control.
  - Not when you need frontier-level reasoning. Local models trail the top hosted ones, so **evaluate on your task** before switching.
  """,
  [(D, "llama.cpp on GitHub", "https://github.com/ggml-org/llama.cpp"),
   (D, "Ollama documentation", "https://docs.ollama.com/"),
   (D, "Hugging Face: GGUF format", "https://huggingface.co/docs/hub/gguf")],
  [("Roughly how much memory do the weights of a 7B-parameter model need at 4-bit quantization?",
    ["About 0.5 GB", "About 3.5–5 GB", "About 28 GB", "About 70 GB"], 1,
    "7B × 4 bits ÷ 8 ≈ 3.5 GB, plus overhead and KV cache, so ~4–5 GB. At 16-bit it'd be ~14 GB."),
   ("Why does local decode speed depend so much on whether the model fits in GPU VRAM?",
    ["VRAM has much higher memory bandwidth, and decode is bandwidth-bound", "CPUs can't do math", "GGUF only works on GPUs", "VRAM stores the tokenizer"], 0,
    "Each token requires reading the weights. High-bandwidth VRAM makes that fast; spilling to system RAM bottlenecks it."),
   ("What is GGUF?",
    ["A GPU driver", "A single-file model format used by llama.cpp, often quantized", "A cloud inference service", "A prompt template language"], 1,
    "GGUF packages weights plus metadata for llama.cpp-based tools like Ollama and LM Studio."),
   ("True or false: a local 8B model will match the best hosted frontier model on hard reasoning tasks.",
    ["True", "False"], 1,
    "Generally false. Small local models are great for many tasks, but you should measure on your own evals instead of assuming."),
  ]),

M("a-building-apps", "Building AI apps: client → API → model → tools loop",
  "The architecture behind almost every AI product, from chatbots to coding agents.",
  """
  ## The basic request
  Your **client** (UI, CLI, cron job) calls **your backend**, which calls the **model API** with: a system prompt, the message history, optional tool definitions, and settings. Keep API keys on the backend, never in the client.

  ## The tool loop (this is what makes it an "agent")
  1. Send messages plus tool schemas (name, description, JSON parameters).
  2. The model either answers, or returns a **tool call**: `{name, arguments}`.
  3. **Your code** validates the arguments and executes the tool (API call, DB query, file read).
  4. Append the tool result to the messages and call the model again.
  5. Repeat until the model gives a final answer or you hit a step/budget limit.
  The model never runs anything itself. Your code is the executor, so your code is where permissions, validation, and logging live.

  ```
  while steps < MAX_STEPS:
      resp = model(messages, tools)
      if resp.tool_calls:
          for call in resp.tool_calls:
              result = run_tool_safely(call)
              messages.append(tool_result(call, result))
      else:
          return resp.text
  ```

  ## Production must-haves from day one
  - Step limits and timeouts, so a confused loop can't run forever.
  - Logging of every model call and tool call.
  - Streaming for anything user-facing.
  - Retries with backoff for rate limits and transient errors.
  """,
  [(D, "Anthropic docs: Tool use with Claude", "https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview"),
   (D, "OpenAI docs: Function calling", "https://developers.openai.com/api/docs/guides/function-calling"),
   (V, "Barry Zhang (Anthropic): How We Build Effective Agents", "https://www.youtube.com/watch?v=D7_ipDqhtwk")],
  [("When a model 'calls a tool', who actually executes it?",
    ["The model provider's servers, automatically", "Your application code", "The user's browser", "The tokenizer"], 1,
    "For standard function calling, the model only emits a structured request. Your code decides whether and how to run it (provider-hosted tools are the exception, and you opt into them)."),
   ("Why must you put a step limit on an agent loop?",
    ["To make the model smarter", "To prevent runaway loops that burn time and money", "Because APIs require it", "To enable streaming"], 1,
    "Models can get stuck repeating tool calls. A max-steps or budget guard is basic safety."),
   ("Where should the model API key live in a web app?",
    ["In the frontend JavaScript", "On your backend server", "In the system prompt", "In a URL parameter"], 1,
    "Anything in the client can be extracted. Keep keys server-side."),
   ("After executing a tool, what does the loop do next?",
    ["Return the tool result directly to the user", "Append the tool result to the messages and call the model again", "Restart the conversation", "Fine-tune the model"], 1,
    "The model needs to see the result to decide the next step or write the final answer."),
  ]),

M("a-prompting", "Prompting that holds up (instructions, few-shot, failure modes)",
  "Prompts that survive real inputs, not just the demo example.",
  """
  ## Be explicit, like briefing a smart new hire
  - State the **task, audience, and output format** directly. Don't hint.
  - Give **context and reasons** ("answers are read aloud, so avoid lists"). Models generalize better from the why.
  - Separate instructions from data with clear delimiters (XML-style tags or headings) so input text isn't mistaken for instructions.
  - Say what to do when information is missing: "If the document doesn't say, answer `unknown`."

  ## Few-shot examples
  Show 2–5 examples of input → ideal output. Make them **diverse** (cover edge cases), or the model will copy surface features of a single example. Examples often beat long descriptions for format and tone.

  ## Common failure modes
  - **Prompt overfitting:** it works on your three test inputs and breaks on real ones. Fix: test on a real eval set.
  - **Contradictory instructions** accumulate as you patch bugs. Periodically rewrite from scratch.
  - **Format drift** in long outputs. Fix: structured outputs and schemas.
  - **Negative instructions** ("don't mention X") can backfire. Say what to do instead.
  - **Hidden assumptions:** the model can't read your mind about edge cases or business rules.

  ## The real workflow
  Write the prompt, run it on 20–50 real examples, read the failures, adjust, re-run. Prompting is iterative engineering, not wordsmithing.
  """,
  [(D, "Anthropic docs: Prompting best practices", "https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices#be-clear-and-direct"),
   (D, "OpenAI docs: Prompt engineering", "https://developers.openai.com/api/docs/guides/prompt-engineering"),
   (V, "Anthropic: AI prompt engineering: A deep dive", "https://www.youtube.com/watch?v=T9aRN5JkmL8")],
  [("Your prompt has one example, and every output copies that example's length and phrasing. Best fix?",
    ["Remove all examples", "Add several diverse examples covering different cases", "Raise the temperature to 1.5", "Write the example in all caps"], 1,
    "A single example becomes a template. Diverse examples show what varies and what stays fixed."),
   ("Why wrap user-provided documents in clear delimiters (e.g., <document> tags)?",
    ["It reduces token cost", "It helps the model separate instructions from data", "It's required by every API", "It encrypts the content"], 1,
    "Clear boundaries reduce confusion between your instructions and the content. It helps, but it is not a complete defense against prompt injection."),
   ("Best way to know if a prompt change is an improvement?",
    ["It reads better", "Run it on a representative eval set and compare results", "Ask the model if it's better", "Check that it's longer"], 1,
    "Prompt quality is empirical. Measure on real examples before and after."),
   ("Which instruction is likely to work better?",
    ["\"Don't use markdown.\"", "\"Write in plain flowing paragraphs, because this is shown in an SMS.\"", "\"NEVER EVER use markdown!!!\"", "\"Markdown bad.\""], 1,
    "Positive, specific instructions with a reason beat shouted negatives."),
  ]),

M("a-retrieval-agents", "Retrieval and agents (RAG vs. tool-using agents, when each)",
  "Two ways to get the right information into the context window, and how to choose.",
  """
  ## RAG: retrieve, then generate
  **Retrieval-Augmented Generation:** search your knowledge base (embeddings, keywords, or both), put the top results into the prompt, and have the model answer from them.
  - Great for: Q&A over docs, policies, support articles.
  - Predictable: one retrieval, one generation. Easy to cache, evaluate, and debug.
  - Weak when the question needs multiple hops, live data, or actions.

  ## Agents: the model decides what to fetch
  Give the model tools (search, SQL, APIs) and let it loop: search, read, search again, act.
  - Great for: multi-step research, tasks needing live systems, taking actions.
  - Costs: more calls, more latency, more variance, harder to evaluate.

  ## How to choose
  - Start with the **simplest thing**: one well-built retrieval step often beats an agent.
  - Use an agent when you **can't predict the steps in advance**.
  - Many good systems are hybrids: an agent whose main tool is a high-quality search.

  ## Retrieval quality is most of the battle
  If the right chunk isn't retrieved, the best model can't answer. Measure retrieval separately (did the gold passage show up in the top-k?), then measure the answers. Tricks like hybrid search, re-ranking, and adding document context to chunks often help more than prompt tweaks.
  """,
  [(D, "Anthropic: Contextual Retrieval", "https://www.anthropic.com/engineering/contextual-retrieval"),
   (D, "Anthropic: Building effective agents", "https://www.anthropic.com/engineering/building-effective-agents"),
   (D, "OpenAI docs: Retrieval", "https://developers.openai.com/api/docs/guides/retrieval")],
  [("A support bot answers questions from a fixed set of help articles. Best first architecture?",
    ["A fully autonomous multi-agent system", "Simple RAG: retrieve relevant articles, then answer", "Fine-tune on the articles", "No retrieval, just a long system prompt with everything"], 1,
    "Single-hop Q&A over a known corpus is RAG's sweet spot: cheaper, faster, easier to evaluate than an agent."),
   ("When is a tool-using agent the better choice?",
    ["When steps are fixed and known", "When the needed steps can't be predicted and may require multiple lookups or actions", "When latency must be minimal", "When you have no tools"], 1,
    "Agents earn their extra cost when the path is dynamic."),
   ("Your RAG answers are wrong. What should you check first?",
    ["Whether the right passages were retrieved at all", "The model's temperature", "The font of the documents", "Whether to switch vector databases"], 0,
    "If retrieval misses, generation can't recover. Measure retrieval hit rate before anything else."),
   ("True or false: RAG changes the model's weights with your documents.",
    ["True", "False"], 1,
    "False. RAG only adds retrieved text to the prompt at query time."),
  ]),

M("a-ft-rag-tools", "Fine-tuning vs. RAG vs. tools (when each wins)",
  "Knowledge, behavior, and actions are different problems with different fixes.",
  """
  ## Match the fix to the problem
  - **Missing or changing knowledge** (your docs, today's prices): use **RAG**. Update the index, not the model.
  - **Live data or actions** (check order status, create a ticket): use **tools**.
  - **Consistent behavior, format, or style** the model won't reliably follow from instructions, or making a **small model do a narrow task** a big one does well: **fine-tune**.

  ## Always try prompting first
  Before fine-tuning, push prompting plus few-shot examples on an eval set. Many "we need fine-tuning" problems are really unclear instructions or missing context.

  ## Fine-tuning realities
  - Needs a few hundred to thousands of high-quality examples, and evals to prove it helped.
  - Bad for teaching facts: knowledge learned this way is hard to update and still gets hallucinated.
  - Locks you to a base model; you re-tune when you upgrade.
  - Big win: **distillation**. Train a cheap model on a strong model's best outputs for your narrow task.

  ## They combine
  A production system might use a fine-tuned small model (format and tone) + RAG (facts) + tools (actions). The question is never "which one" in general; it's "which problem am I solving right now".
  """,
  [(V, "OpenAI DevDay: A Survey of Techniques for Maximizing LLM Performance", "https://www.youtube.com/watch?v=ahnGLM-RC1Y"),
   (D, "OpenAI docs: Optimizing LLM accuracy", "https://developers.openai.com/api/docs/guides/optimizing-llm-accuracy")],
  [("Your product prices change daily and the model must quote current prices. Best approach?",
    ["Fine-tune weekly", "RAG or a pricing tool that fetches current data", "A longer system prompt written once", "Raise the temperature"], 1,
    "Changing facts belong in retrieval or tools. Fine-tuning freezes knowledge at training time."),
   ("When is fine-tuning most clearly worth it?",
    ["To teach the model your company wiki", "To make a smaller model reliably perform a narrow task or format", "Before you've tried prompting", "To give the model internet access"], 1,
    "Fine-tuning shines for behavior and format, and for distillation into cheaper models, not for knowledge injection."),
   ("What should you do before deciding to fine-tune?",
    ["Collect 1 million examples", "Exhaust prompting and few-shot examples, measured on an eval set", "Switch providers", "Delete your RAG system"], 1,
    "Prompting is cheaper and faster to iterate. Fine-tune only once evals show prompting has plateaued."),
   ("A model needs to create Jira tickets. That's a job for...",
    ["Fine-tuning", "RAG", "Tools/function calling", "A bigger context window"], 2,
    "Taking actions in external systems needs tools."),
  ]),

M("a-hallucination", "Hallucination and grounding",
  "Why models confidently make things up, and the practical ways to reduce it.",
  """
  ## Why it happens
  Models are trained to produce plausible continuations, and training and evaluation often reward guessing over saying "I don't know". So when the model lacks the fact, it can still produce a fluent, confident, wrong answer: invented citations, APIs, numbers, or quotes.

  ## Grounding techniques that actually work
  - **Provide the source:** put the relevant documents in context and instruct the model to answer **only** from them.
  - **Allow "I don't know":** explicitly permit and reward abstaining ("If the answer isn't in the documents, say so").
  - **Quote first:** have the model extract the supporting quotes before answering; claims without quotes get dropped.
  - **Citations:** require references to specific passages, then check them programmatically.
  - **Verify with tools:** for code, run it; for facts, look them up; for math, calculate.

  ## Measure it
  - Build eval cases where the correct answer is "not in the docs" and check the model abstains.
  - Spot-check citations: does the cited passage actually support the claim?
  - Track the hallucination rate over time like any other quality metric.
  """,
  [(D, "Anthropic docs: Reduce hallucinations", "https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations"),
   (D, "Paper: Why Language Models Hallucinate (2025)", "https://arxiv.org/abs/2509.04664"),
   (D, "Lilian Weng: Extrinsic Hallucinations in LLMs", "https://lilianweng.github.io/posts/2024-07-07-hallucination/")],
  [("Which instruction most directly reduces made-up answers in a document Q&A bot?",
    ["\"Be creative.\"", "\"Answer only from the provided documents; if the answer isn't there, say you don't know.\"", "\"Answer as fast as possible.\"", "\"Use a confident tone.\""], 1,
    "Grounding plus explicit permission to abstain targets the root cause: guessing when information is missing."),
   ("What's a good eval case for hallucination?",
    ["A question whose answer is clearly in the docs", "A question whose answer is NOT in the docs; the correct behavior is to abstain", "A greeting", "A very long document"], 1,
    "You need negative cases to see whether the model invents answers."),
   ("True or false: a fluent, confident answer is strong evidence it's correct.",
    ["True", "False"], 1,
    "False. Models are just as fluent when they're wrong. Confidence of tone isn't calibration."),
   ("For generated code, the most reliable 'grounding' check is...",
    ["Asking the model if it's sure", "Running it (tests, compiler, linter)", "Making the prompt longer", "Lowering top-p"], 1,
    "Execution is ground truth. Models self-assessing correctness is much weaker."),
  ]),

M("a-multimodal", "Multimodal basics (vision and audio as tokens)",
  "How models 'see' images and 'hear' audio, at the level you need to build with them.",
  """
  ## Everything becomes tokens
  - **Images:** split into patches (e.g., 16×16 pixels). Each patch becomes a vector, like a word token. Vision Transformers showed that standard transformers work well on these patches.
  - **Audio:** converted to a spectrogram or discrete audio tokens, then processed the same way.
  - The model attends across text and image/audio tokens together, which is why it can answer "what's wrong in this screenshot?"

  ## Practical implications
  - **Images cost tokens**, often hundreds to over a thousand per image depending on resolution. Resize before sending.
  - **Resolution matters:** tiny text in a huge screenshot may be downscaled into mush. Crop to the relevant region.
  - Models are good at: describing scenes, reading clear text and charts, UI screenshots, document understanding.
  - Still weaker at: precise counting, exact spatial positions, small details, and reading dense tables perfectly. Verify critical extractions.

  ## Audio and voice
  Options range from a pipeline (speech-to-text, then LLM, then text-to-speech) to native speech-to-speech models. Pipelines are easier to debug and log; native models have lower latency and keep tone and emotion.

  ## Shared ideas behind it
  CLIP-style training learns a shared space for images and text by matching captions to pictures. That idea powers image search and grounds a lot of multimodal work.
  """,
  [(D, "Anthropic docs: Vision", "https://platform.claude.com/docs/en/build-with-claude/vision"),
   (D, "OpenAI docs: Images and vision", "https://developers.openai.com/api/docs/guides/images-vision"),
   (D, "Paper: An Image is Worth 16x16 Words (Vision Transformer)", "https://arxiv.org/abs/2010.11929")],
  [("How does a typical vision-language model turn an image into model input?",
    ["OCR only", "It splits the image into patches and turns each patch into a token-like vector", "It converts the image to a filename", "It describes the image with a separate captioning model only"], 1,
    "Patches become embeddings processed alongside text tokens. OCR or captioning pipelines exist, but native VLMs work on patches."),
   ("The model misreads small text in a full 4K screenshot. Best first fix?",
    ["Use a higher temperature", "Crop to the relevant region (or zoom in) before sending", "Send it as a ZIP", "Ask it to try harder"], 1,
    "Images are often downscaled. Cropping keeps the important pixels at usable resolution and saves tokens."),
   ("True or false: sending images is free compared to text.",
    ["True", "False"], 1,
    "False. Images consume many tokens. Resize and crop to control cost."),
   ("Main advantage of a speech-to-text → LLM → text-to-speech pipeline over native speech-to-speech?",
    ["Lower latency", "Easier to debug, log, and swap components", "Better at preserving tone", "No transcription needed"], 1,
    "Pipelines give you inspectable text at each step. Native models tend to win on latency and expressiveness."),
  ]),

M("a-eval-basics", "Evaluation basics (golden sets, graded outputs, evals before prompts)",
  "If you can't measure it, every prompt change is a guess.",
  """
  ## What an eval is
  An eval is a dataset of inputs + a way to **grade** outputs + a score you track over time. It turns "seems better" into "went from 72% to 85% on 120 cases".

  ## Golden sets
  - Start with **20–50 real examples** (from logs, users, or realistic drafts), including hard and edge cases.
  - For each, write what "good" means: an exact answer, required facts, or a rubric.
  - Grow it continuously: every bug report becomes a new case.

  ## Three ways to grade
  - **Code checks:** exact match, regex, valid JSON, required field present, tests pass. Cheap, reliable; use wherever possible.
  - **LLM-as-judge:** a model grades against a specific rubric ("Does the answer cite the refund policy? yes/no"). Good for fuzzy criteria, but validate it against human labels.
  - **Human review:** the gold standard, expensive. Use it to calibrate the other two and to read failures.

  ## Why evals come before prompts
  Writing the eval first forces you to define success. Then every prompt, model, or retrieval change gets measured instead of judged by vibes, and you catch regressions immediately.

  ## The habit that matters most
  **Read your outputs.** Look at 20 failures, group them by cause, and fix the biggest group. Error analysis beats any metric dashboard.
  """,
  [(D, "Hamel Husain: Your AI Product Needs Evals", "https://hamel.dev/blog/posts/evals/"),
   (D, "Anthropic docs: Define success criteria and build evaluations", "https://platform.claude.com/docs/en/test-and-evaluate/develop-tests"),
   (V, "Hamel Husain: LLM Evals: Common Mistakes", "https://www.youtube.com/watch?v=GL0XhAj5LPE")],
  [("Which grading method should you prefer when it can capture the requirement?",
    ["LLM-as-judge for everything", "Code-based checks (exact match, schema, tests)", "Asking users to rate every output", "Reading outputs and deciding by feel"], 1,
    "Deterministic checks are cheap, fast, and reliable. Use judges and humans for what code can't check."),
   ("What's a good size for a first eval set?",
    ["1 example", "20–50 real, varied examples that grow over time", "Exactly 10,000", "None until launch"], 1,
    "Start small and real, then grow from production failures. Don't wait for a perfect giant dataset."),
   ("Before trusting an LLM-as-judge, you should...",
    ["Make it use a higher temperature", "Check its agreement with human labels on a sample", "Use the same model that generated the output, unchecked", "Remove the rubric"], 1,
    "Judges have biases and errors. Measure agreement with humans before relying on them."),
   ("A prompt tweak 'feels better' on three examples. What's the right next step?",
    ["Ship it", "Run the full eval set and compare to the baseline", "Rewrite the eval to match", "Ask the model to grade itself"], 1,
    "Three examples is anecdote. Compare on the full set to catch regressions elsewhere."),
  ]),

M("a-data-labeling", "Data and labeling for evals (golden sets, inter-annotator agreement)",
  "Your eval is only as good as its labels. How to make labels you can trust.",
  """
  ## Where good eval data comes from
  - **Production logs** (with PII scrubbed): the real distribution, including weird inputs.
  - **User feedback:** thumbs-down, corrections, support tickets.
  - **Targeted synthetic cases:** generated to cover gaps (rare intents, adversarial inputs). Review them by hand; synthetic data drifts toward the easy and generic.
  - Keep a **held-out set** you don't tune prompts against, so you can detect overfitting.

  ## Write labeling guidelines
  Ambiguity in labels becomes noise in scores. Guidelines should define each label with examples, cover edge cases, and say what to do when unsure. Prefer **binary or small-scale judgments** ("pass/fail on: cites policy") over 1–10 scores; they're more consistent.

  ## Inter-annotator agreement
  Have two people label the same 50 items independently and compare.
  - Low agreement means the **task or guidelines are unclear**, not that the labelers are bad.
  - **Cohen's kappa** measures agreement beyond chance (around 0.6+ is decent for subjective tasks).
  - Discuss disagreements, update the guidelines, repeat. This also tells you the ceiling for any automated judge.

  ## Criteria drift
  As you read more outputs, your idea of "good" sharpens. That's normal. Update the rubric and re-label older items so scores stay comparable.
  """,
  [(D, "Hamel Husain: A Field Guide to Rapidly Improving AI Products", "https://hamel.dev/blog/posts/field-guide/"),
   (D, "Paper: Who Validates the Validators? (criteria drift and LLM judges)", "https://arxiv.org/abs/2404.12272"),
   (D, "Wikipedia: Cohen's kappa", "https://en.wikipedia.org/wiki/Cohen%27s_kappa")],
  [("Two annotators agree on only 55% of labels for a binary task. Most likely root cause?",
    ["The annotators are careless", "The task definition or guidelines are ambiguous", "The model is bad", "You need more annotators immediately"], 1,
    "Low agreement usually means the criteria aren't clear. Fix the guidelines with examples, then re-measure."),
   ("Why does Cohen's kappa exist instead of just percent agreement?",
    ["It's easier to compute", "It corrects for agreement that would happen by chance", "It works only for LLMs", "It measures model accuracy"], 1,
    "With skewed labels, raters can agree a lot by chance. Kappa adjusts for that."),
   ("Why keep a held-out eval set?",
    ["To save storage", "To detect overfitting your prompts to the examples you tune on", "Because APIs require it", "To train the model"], 1,
    "If you iterate against the same cases, you can overfit. A held-out set gives an honest check."),
   ("Which rubric style tends to give more consistent labels?",
    ["1–10 overall quality score", "Specific binary checks (pass/fail per criterion)", "Free-text vibes", "Emoji ratings"], 1,
    "Binary, specific criteria are easier to apply consistently and easier to automate."),
  ]),

M("a-safety-misuse", "Safety and misuse (jailbreaks, dual-use, product responsibility)",
  "What can go wrong when real people use your AI product, and what's your job to prevent.",
  """
  ## Threats to know
  - **Jailbreaks:** users try to get the model to ignore its guidelines (role-play, long many-example prompts, encoding tricks).
  - **Prompt injection:** malicious instructions hidden in content the model reads (web pages, emails, docs). Covered deeply in Track B.
  - **Dual-use:** the same capability that helps (chemistry tutoring, security research, persuasive writing) can harm in other hands.
  - **Excessive agency:** an agent with too many permissions does damage when it's wrong or manipulated.

  ## Your product is your responsibility
  The model provider's safety training is a baseline, not your whole safety story. You choose the tools, data access, and audience. Practical layers:
  - Scope the product narrowly. A support bot doesn't need to write malware.
  - **Input/output screening** for clearly disallowed content, often with a cheap classifier model.
  - **Least privilege** for tools; human approval for consequential actions.
  - **Rate limits, abuse monitoring, and logging** so you can see and stop misuse.
  - Clear usage terms and a way for users to report problems.

  ## Think in risks, not vibes
  Ask: who could misuse this, what's the worst realistic outcome, and how would we know? Frameworks like the NIST AI RMF give structure; red-teaming your own product (try to break it) gives evidence.
  """,
  [(D, "Anthropic docs: Mitigate jailbreaks and prompt injections", "https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/mitigate-jailbreaks"),
   (D, "OWASP Top 10 for LLM Applications", "https://genai.owasp.org/llm-top-10/"),
   (D, "NIST AI Risk Management Framework", "https://www.nist.gov/itl/ai-risk-management-framework")],
  [("True or false: if the model provider has safety training, your app doesn't need its own safeguards.",
    ["True", "False"], 1,
    "False. Your tools, data, and users create risks the provider can't see. Layer your own controls."),
   ("Which control limits damage most when an agent is manipulated?",
    ["A friendlier system prompt", "Least-privilege tool permissions plus human approval for risky actions", "A larger model", "Higher temperature"], 1,
    "Assume the model can be tricked; limit what a tricked model can do."),
   ("What's 'dual-use' capability?",
    ["A model that runs on two GPUs", "A capability that can be used for both beneficial and harmful purposes", "Two models in one product", "A tool with two parameters"], 1,
    "Many useful capabilities are dual-use; product scope and safeguards decide how they're exposed."),
   ("A cheap way to screen user inputs for clearly disallowed requests is...",
    ["Ignore them", "A lightweight classifier/moderation pass before the main model", "Fine-tuning the main model every day", "Doubling the context window"], 1,
    "A small, fast screening model adds a safety layer at low cost and latency."),
  ]),

M("a-working-in-ai", "Working in AI day-to-day (reading papers lightly, shipping, measuring)",
  "Habits that compound: stay current without drowning, ship small, measure everything.",
  """
  ## Reading papers without drowning
  - Read the **abstract, figures, and conclusion first**. Only go deeper if it's relevant to something you're building.
  - Ask three questions: what problem, what's the key idea, what's the evidence (and on what benchmark)?
  - Be skeptical of benchmark gains. Does it hold on **your** task? Run a quick test instead of trusting the leaderboard.
  - Curated feeds (Hugging Face Daily Papers, trusted practitioner blogs) beat raw arXiv firehoses.

  ## Ship small, ship often
  - A working ugly demo beats a perfect plan. Get something in front of a real user in days.
  - Keep a **baseline** (even a simple non-LLM rule) so you know if the AI adds value.
  - Write down what you tried and what happened. Short notes become your best docs and blog posts.

  ## Measure everything
  - Quality (eval scores), cost per task, latency (p50/p95), and usage. You can't improve what you don't track.
  - Look at real outputs every week. Dashboards hide the weird failures.

  ## Staying current, sanely
  Models and APIs change monthly. Build **abstractions and evals** so swapping a model is a one-day experiment, not a rewrite. Then new releases become an opportunity instead of a fire drill.
  """,
  [(D, "Hugging Face Daily Papers", "https://huggingface.co/papers"),
   (D, "Applied LLMs: What We Learned from a Year of Building with LLMs", "https://applied-llms.org/"),
   (V, "Andrej Karpathy: Software Is Changing (Again)", "https://www.youtube.com/watch?v=LCEmiRjPEtQ")],
  [("A new paper claims +8% on a popular benchmark. What's the practical move before adopting the technique?",
    ["Adopt it immediately", "Test it on your own eval set for your task", "Wait for a second paper", "Ignore all papers"], 1,
    "Benchmarks may not reflect your data. A quick test on your own evals decides."),
   ("Efficient first pass through a paper?",
    ["Read every proof in order", "Abstract, figures, conclusion; then decide whether to go deeper", "Only read the references", "Skip to the appendix"], 1,
    "Triage first. Most papers don't need a full read for practical work."),
   ("Why keep a simple non-LLM baseline?",
    ["It's required by law", "To prove the AI actually adds value over something simpler", "To slow down the project", "Because LLMs can't be measured"], 1,
    "If a regex or rule matches the LLM's quality, ship the cheaper thing."),
   ("What makes switching to a newly released model a one-day experiment?",
    ["Hard-coding the model everywhere", "A model abstraction layer plus an eval suite", "Waiting six months", "Using the biggest model always"], 1,
    "Abstractions let you swap; evals tell you if the swap is better."),
  ]),
]

track = {
    "id": "A",
    "title": "Track A — Foundations",
    "subtitle": "How models work and how AI apps are built. Do these first if any term in Track B feels fuzzy.",
    "order": 1,
    "modules": modules,
}
write("../content/track-a-foundations.json", track)
