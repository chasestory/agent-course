from common import M, write
V = "video"; D = "doc"
modules = [

M("m-vectors-matrices", "Vectors and matrices (dot product, tensors and reshape)",
  "The data structures every model is made of, explained with arrows and grids instead of proofs.",
  """
  ## Vectors: a list of numbers, or an arrow
  A vector like `[3, 4]` is both a list of numbers and an arrow pointing 3 right and 4 up. Its **length** is √(3² + 4²) = 5. In AI, a vector usually describes one thing: a word's embedding (768 numbers), a pixel's colors (3 numbers), a user's features.

  ## The dot product: "how much do these point the same way?"
  Multiply matching entries and add: `[1, 2] · [3, 4] = 1×3 + 2×4 = 11`.
  - Big positive: the arrows point in a similar direction.
  - Zero: they're at right angles (unrelated).
  - Negative: they point in opposite directions.
  **Cosine similarity** is the dot product of the two vectors after scaling each to length 1. That's literally how semantic search compares embeddings, and how attention scores queries against keys.

  ## Matrices: a grid that transforms vectors
  A matrix is a grid of numbers. Multiplying a matrix by a vector **transforms** it: rotate, stretch, project into a different number of dimensions. A neural-network layer is mostly "multiply by a weight matrix, add a bias". Shape rule: an (m × n) matrix times an n-long vector gives an m-long vector. The inner sizes must match.

  ## Tensors and reshape
  A **tensor** is just an n-dimensional array:
  - 0-D: a single number. 1-D: a vector. 2-D: a matrix.
  - 3-D example: a batch of token embeddings, shape `(batch=8, tokens=512, dims=768)`.
  **Reshape** changes how the same numbers are grouped without changing them. A (2 × 6) tensor can become (3 × 4) or (12,) because all have 12 numbers. Most shape bugs in ML code are someone's mental picture of the grid not matching the real one, so print `.shape` often.
  """,
  [(V, "3Blue1Brown: Vectors (Essence of linear algebra, ch. 1)", "https://www.youtube.com/watch?v=fNk_zzaMoSs"),
   (V, "3Blue1Brown: Dot products and duality", "https://www.youtube.com/watch?v=LyGKycYT2v0"),
   (D, "PyTorch tutorial: Tensors", "https://docs.pytorch.org/tutorials/beginner/basics/tensorqs_tutorial.html")],
  [("What is [2, 0] · [0, 5]?",
    ["10", "0", "7", "25"], 1,
    "2×0 + 0×5 = 0. A dot product of zero means the vectors are perpendicular: they share no direction."),
   ("Two embedding vectors have a large positive dot product (after normalizing). What does that suggest?",
    ["They point in similar directions, so the texts are likely similar in meaning", "They are unrelated", "They are opposites", "One of them is broken"], 0,
    "Normalized dot product = cosine similarity. Close to 1 means similar direction, which for embeddings means similar meaning."),
   ("A (3 × 4) matrix multiplies a vector. What length must the vector be, and what length comes out?",
    ["Length 3 in, length 4 out", "Length 4 in, length 3 out", "Any length in, length 12 out", "Length 12 in, length 1 out"], 1,
    "(m × n) times an n-vector gives an m-vector. The inner sizes (4) must match; the output has 3 entries."),
   ("A tensor has shape (2, 6). Which reshape is impossible?",
    ["(3, 4)", "(12,)", "(4, 4)", "(6, 2)"], 2,
    "Reshape keeps the same 12 numbers. (4, 4) needs 16, so it can't work. The others all hold 12."),
  ]),

M("m-probability", "Probability basics (distributions, expectation, Bayes lightly)",
  "LLMs output probabilities, and evals are statistics. Here's the intuition you need.",
  """
  ## Distributions: where the probability goes
  A **probability distribution** spreads 100% of belief across possible outcomes. A fair die gives 1/6 to each face. An LLM's output at each step is a distribution over ~100k tokens, for example "Paris" 92%, "the" 3%, everything else sharing the rest. **Softmax** is the function that turns the model's raw scores into such a distribution: all positive, summing to 1.

  ## Expectation: the long-run average
  The **expected value** is each outcome times its probability, added up. A bet that wins $10 with 20% chance and $0 otherwise is worth 0.2 × 10 = $2 on average. In practice:
  - Expected cost per task = Σ (probability of each path × its cost). An agent that retries 30% of the time costs more than its happy path suggests.
  - A **training loss** is an average over many examples: you minimize the expected error.

  ## Sample size and noise
  An eval of 20 cases where you score 17/20 (85%) could easily be 75% or 95% on another 20 cases. Small evals are noisy. Before celebrating a 3-point gain, ask whether you have enough cases to tell it apart from luck. More cases means less noise.

  ## Bayes, lightly: updating on evidence
  Bayes' rule says how to update a belief when you see evidence. The key intuition is **base rates matter**. If only 1% of emails are fraud and your detector flags 10% of normal emails by mistake, most flagged emails are still **not** fraud. Same for LLM judges and classifiers: always ask how common the thing really is.
  """,
  [(V, "3Blue1Brown: Bayes theorem, the geometry of changing beliefs", "https://www.youtube.com/watch?v=HZGCoVF3YvM"),
   (D, "Seeing Theory: a visual introduction to probability and statistics", "https://seeing-theory.brown.edu/")],
  [("An LLM's softmax output over the vocabulary must...",
    ["Have all values positive and sum to 1", "Have exactly one value equal to 1", "Contain negative values for unlikely tokens", "Sum to the vocabulary size"], 0,
    "Softmax produces a probability distribution: non-negative and summing to 1. Usually no single token gets exactly 1."),
   ("An agent call costs $0.01. 30% of runs need one retry (another $0.01). What's the expected cost per run?",
    ["$0.010", "$0.013", "$0.020", "$0.030"], 1,
    "0.01 + 0.3 × 0.01 = 0.013. Expected value weights each path by its probability."),
   ("Your prompt change scores 18/20 vs. the old 17/20. What's the honest conclusion?",
    ["The new prompt is definitely better", "The difference is within noise for 20 cases; test on more cases", "The old prompt is better", "Evals don't work"], 1,
    "With 20 cases, a one-case difference is easily luck. Bigger eval sets shrink this noise."),
   ("1% of transactions are fraud. A detector flags 90% of fraud but also 10% of normal transactions. Are most flagged transactions fraud?",
    ["Yes, about 90% of them", "No, most flagged ones are normal because fraud is rare", "Exactly half are fraud", "There's no way to tell"], 1,
    "Out of 1000: ~9 real fraud flagged, ~99 normal flagged. Base rates dominate, so only ~8% of flags are real fraud."),
  ]),

M("m-derivatives", "Derivatives (slope and chain rule intuition)",
  "How a small nudge to an input changes the output. That one idea is what makes learning possible.",
  """
  ## A derivative is a slope
  The derivative of a function at a point answers: **if I nudge the input a tiny bit, how much does the output change, and in which direction?**
  - For f(x) = x², at x = 3 the derivative is 6: nudge x up by 0.01 and f goes up by about 0.06.
  - Positive derivative: the output goes up as the input increases. Negative: it goes down. Zero: you're at a flat spot (often a minimum or maximum).
  Picture zooming into a curve until it looks like a straight line. The derivative is that line's slope.

  ## A few you'll see
  - f(x) = c (constant): slope 0.
  - f(x) = a·x: slope a.
  - f(x) = x²: slope 2x.
  - ReLU(x) = max(0, x): slope 0 for negative x, 1 for positive x. That's why "dead" ReLUs stop learning: zero slope means zero signal.

  ## The chain rule: slopes multiply through a pipeline
  If y depends on u, and u depends on x, then **(how y changes with x) = (how y changes with u) × (how u changes with x)**. Think of gears: if gear A turns B twice as fast, and B turns C three times as fast, then A turns C six times as fast.

  ## Why this matters for AI
  A neural network is a long chain of simple functions. **Backpropagation** is the chain rule applied layer by layer, backwards, to find how every weight affects the final loss. And if many slopes in the chain are tiny, multiplying them makes the signal vanish. That's the "vanishing gradient" problem that residual connections help fix.
  """,
  [(V, "3Blue1Brown: The essence of calculus", "https://www.youtube.com/watch?v=WUvTyaaNkzM"),
   (V, "3Blue1Brown: Visualizing the chain rule and product rule", "https://www.youtube.com/watch?v=YG15m2VwSjA"),
   (D, "Math is Fun: Introduction to Derivatives", "https://www.mathsisfun.com/calculus/derivatives-introduction.html")],
  [("f(x) = x². What's the derivative at x = 3?",
    ["3", "6", "9", "0"], 1,
    "The derivative of x² is 2x, so 2 × 3 = 6. A tiny nudge of 0.01 raises f by about 0.06."),
   ("A function's derivative at some point is negative. If you increase the input slightly, the output...",
    ["Increases", "Decreases", "Stays exactly the same", "Becomes undefined"], 1,
    "A negative slope means the output goes down as the input goes up."),
   ("y = 3u and u = 2x. By the chain rule, how much does y change per unit change in x?",
    ["5", "6", "1.5", "9"], 1,
    "Slopes multiply through the chain: 3 × 2 = 6. Like gears."),
   ("Why does the chain rule matter for training neural networks?",
    ["It makes models smaller", "Backpropagation uses it to compute how each weight affects the loss through all the layers", "It picks the learning rate", "It tokenizes text"], 1,
    "A network is a chain of functions; backprop is the chain rule applied backwards through it."),
  ]),

M("m-gradients", "Gradients (gradient descent, why loss goes downhill)",
  "Training a model is walking downhill on a landscape of error, one small step at a time.",
  """
  ## From one slope to many: the gradient
  With many inputs (a model has billions of weights), you get one slope per input. Bundled together, that's the **gradient**: a vector that points in the direction where the output **increases fastest**. Its size says how steep it is.

  ## The loss landscape
  Picture a hilly landscape. Your position is the current setting of all the weights; the height is the **loss** (how wrong the model is). Training means finding a low valley.

  ## Gradient descent: step downhill
  1. Compute the loss on a batch of examples.
  2. Compute the gradient (via backpropagation).
  3. Move every weight a small step in the **opposite** direction of the gradient: `w = w - learning_rate × gradient`.
  4. Repeat millions of times.
  It goes downhill because the gradient points uphill, and you step against it.

  ## The learning rate
  - **Too small:** painfully slow progress.
  - **Too large:** you overshoot the valley and bounce around, or diverge (the loss explodes).
  - Real training uses tricks like momentum and Adam, plus warmup and decay schedules, but the core idea is the same.

  ## Stochastic and mini-batch
  Computing the gradient over the whole dataset is too expensive, so each step uses a random **mini-batch**. The steps are noisy but cheap, and the noise even helps escape bad spots. When you see a loss curve trending down with wiggles, that's what you're looking at.
  """,
  [(V, "3Blue1Brown: Gradient descent, how neural networks learn", "https://www.youtube.com/watch?v=IHZwWFHWa-w"),
   (D, "CS231n notes: Optimization and gradient descent", "https://cs231n.github.io/optimization-1/"),
   (D, "Distill: Why Momentum Really Works (interactive)", "https://distill.pub/2017/momentum/")],
  [("The gradient of the loss points in which direction?",
    ["Steepest decrease of the loss", "Steepest increase of the loss", "Toward zero always", "A random direction"], 1,
    "The gradient points uphill. That's why gradient descent subtracts it."),
   ("What's the gradient descent update?",
    ["w = w + learning_rate × gradient", "w = w − learning_rate × gradient", "w = gradient", "w = w × gradient"], 1,
    "Step against the gradient to go downhill on the loss."),
   ("The training loss jumps around wildly and then explodes to infinity. Most likely cause?",
    ["Learning rate too small", "Learning rate too large", "Too much data", "The tokenizer"], 1,
    "Too-large steps overshoot the valley and can diverge. Lower the learning rate."),
   ("Why use mini-batches instead of the full dataset for each step?",
    ["Mini-batches give exact gradients", "They're much cheaper per step, and the noise is acceptable or even helpful", "Full-dataset gradients are always wrong", "Mini-batches need no backpropagation"], 1,
    "Mini-batch gradients are noisy estimates, but cheap enough to take many more steps."),
  ]),
]

track = {
    "id": "M",
    "title": "Track 0 — Math Foundations",
    "subtitle": "Just enough math to read the rest: vectors, probability, derivatives, gradients. Visual intuition, not proofs.",
    "order": 0,
    "modules": modules,
}
write("../content/track-0-math.json", track)
