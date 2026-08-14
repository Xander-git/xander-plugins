---
name: present-solutions
description: >-
  Present multiple candidate solutions to a problem or open question, each with
  background, tradeoffs (accuracy, implementation cost, complexity, technical debt,
  plus domain-specific axes), failure modes, and a reasoned recommendation. Use this
  skill whenever the user is weighing design choices, comparing approaches, or
  brainstorming, even if they do not explicitly ask for options, including analysis
  pipeline design, software architecture and API design, algorithm selection, data
  modeling, tooling and dependency choices, or any "how should I build or approach X"
  question where genuine alternatives exist with non-trivial tradeoffs. Do NOT use for
  single-answer factual questions, lookups, or tasks with one obviously correct approach.
---

# Present Solutions

Help the user reason about a decision by laying out the real alternatives, the tradeoffs between them, and a recommendation grounded in their context. The goal is a decision aid, not a menu. The user should come away knowing which option fits *their* situation and under what conditions a different option would win.

## When this applies (and when it does not)

Use this when the question has genuine alternatives whose tradeoffs are non-trivial: pipeline design, software/API design, algorithm choice, data modeling, tooling or dependency selection, "how should I approach X."

Do not force this structure onto questions with one correct answer, simple factual lookups, or choices where the alternatives are not meaningfully different. If you find yourself padding to reach a second option, that is the signal to stop and just give the direct answer. State plainly that there is effectively one sound approach and why.

## Context inference and when to ask

Default to inferring context rather than interrogating the user. Infer from the conversation, the codebase, and reasonable domain priors. The dimensions that usually drive a recommendation:

- One-off / throwaway vs. maintained / production
- Expected lifetime and how often it will be rerun or changed
- Team size and the skill profile of who maintains it
- Reversibility: is this a cheap-to-change decision or a sticky one (schema, public API, dependency lock-in)
- Scale and performance envelope (data size, latency, recompute cost)

State each material assumption inline in one sentence, so the user can correct it cheaply. Example: "Assuming this is a maintained library rather than a one-off script, I weight technical debt heavily; if it is throwaway, option B becomes more attractive."

Before asking the user anything, apply this test: **would a different answer change *which* solution you recommend, not just how you caveat it?**

- If no: do not ask. Infer and state the assumption inline.
- If yes, and the work genuinely cannot proceed without it: batch all such questions into a single short round. Never drip-feed questions across turns. Ask the minimum that unblocks the recommendation.
- If yes, but the work can proceed: do not block. Present the recommendation as a branch ("if the data fits in memory, recommend A; if it does not, recommend B") and name the branch point explicitly.

This biases slightly toward inference. That is deliberate: an inline assumption is cheap for the user to correct, whereas an unwanted question round is friction already spent. For brainstorming, keep momentum.

## How many solutions

Present 2 to 4 substantive options. Two strong options beat four where two are filler. Quality of distinctness matters more than count: each option should represent a genuinely different approach, not a parameter tweak of another.

**Always include a baseline option**: the simplest thing that could plausibly work (the boring choice, the standard-library approach, "do nothing different," the off-the-shelf tool). This anchors the tradeoff comparison and counteracts the bias toward over-engineering. If a more sophisticated option does not clearly beat the baseline for the user's context, say so.

## What to cover per solution

Cover these dimensions for each option. Use flexible prose, not a rigid template. Depth should vary with how much each option matters: do not pad a weak option to match a strong one, and do not bury the leading option in equal-weight detail. Required coverage:

1. **What it is and background.** Name the approach and explain it concretely. Where useful, note its provenance: the standard technique it descends from, the library or paper that established it, why it exists. Distinguish established practice from newer or contested approaches (see Epistemic discipline below).

2. **Tradeoffs across the core axes:**
   - **Accuracy / correctness / quality of result**
   - **Implementation cost** (effort to build the first working version)
   - **Complexity** (cognitive load to understand and reason about)
   - **Technical debt** (ongoing maintenance burden, coupling, how it ages)

   Present these as tradeoffs against each other, not absolute virtues. The weighting of these axes depends on context, so tie them back to the assumptions you stated. Technical debt is near-irrelevant for a throwaway script and dominant for a shared library.

3. **Axes beyond the core four.** The four core axes are a floor, not the full set. The decision often turns on an axis specific to this problem that no generic list names (for example a dependency boundary, a phasing or sequencing constraint, a coupling seam, a migration path). Derive the axes that actually discriminate between these options from the problem itself, not only from a menu. Two moves matter:
   - **Discover the deciding axis even when it was not asked about.** If the options are differentiated mainly by something the user did not raise, name it and make it central. The most useful comparison axis is frequently one neither the question nor any checklist mentioned.
   - **Report non-differentiating axes honestly.** If a core axis (often the one the user emphasized) is effectively identical across all options, say so plainly and explain why, rather than manufacturing a distinction to fill the slot. "On accuracy these are identical because both call the same underlying machinery; the decision turns on X instead" is a complete and valuable finding.

   The lists below are starting hints to prompt thinking, not an exhaustive set. Pull from them only what fits, and add what they miss:
   - *Algorithms*: time and space complexity, numerical stability, behavior on degenerate or adversarial input, constant factors vs. asymptotics.
   - *Pipelines / data engineering*: reproducibility, idempotency, recompute cost, observability, failure recovery, schema evolution.
   - *Software / API design*: coupling, testability, extensibility, blast radius of change, public-surface commitment, dependency boundaries, phasing or sequencing constraints.

4. **Failure modes.** How does this break in practice, not just in theory? Edge cases, degenerate inputs, scaling cliffs, the conditions under which it quietly produces wrong results. This is often more decision-relevant than the static tradeoff axes.

5. **Reversibility.** Flag whether choosing this is cheap to undo or sticky. Irreversible choices (data schema, public API, hard dependency) warrant more caution than reversible ones and change how confident any recommendation should be.

## The recommendation

End with a clear recommendation. Do not hedge into uselessness, but ground it:

- **If the axis the user emphasized does not decide it, say so first.** When the user framed the question around one axis (accuracy, speed, cost) and that axis turns out not to discriminate between the options, lead with that finding before pivoting to the axes that actually drive the decision. Correcting the framing is more useful than answering the question as posed.
- **State which option and why**, referencing the user's inferred context and the assumptions you made.
- **Tag your confidence** using the epistemic tiers below. A recommendation can be an established best practice, a defensible judgment call, or genuinely speculative. Say which. Do not state a judgment call as if it were settled fact.
- **State what would change the recommendation.** Name the conditions under which a different option wins. This makes the recommendation falsifiable and lets the user check it against facts you could not infer. If you used a branch (above), this is where the branch points live.
- **Account for reversibility.** A confident recommendation is cheaper to make for a reversible decision. For a sticky one, lean toward the option that preserves optionality unless the evidence is strong.

## Epistemic discipline

Match language to the strength of the claim:

- **Established**: state directly.
- **Emerging consensus**: "evidence suggests."
- **Contested**: present both sides.
- **Speculative**: "one possibility is."

Distinguish correlation from causation and "no evidence found" from "evidence of absence." When you make an empirical performance or correctness claim that the decision hinges on (e.g. "approach A is faster on large inputs"), say whether that is established knowledge, benchmark-dependent, or your reasoning. If a claim is based on general reasoning rather than a known source, flag it as such rather than implying authority. Do not fabricate citations or benchmark numbers; if a number matters and you do not have it, say what would need to be measured.

## Formatting

Flexible prose with the required coverage above. Use a compact comparison table only when it genuinely aids scanning across options on shared axes; otherwise prose. Avoid em dashes. Favor depth over breadth.

## Worked shape (illustrative, not a fixed template)

> **Problem framing + assumptions.** One or two sentences restating the decision and the context you are assuming, with material assumptions inline.
>
> **Option 1 (baseline): [name].** What it is and where it comes from. Tradeoffs across the core axes plus relevant domain axes. Failure modes. Reversibility.
>
> **Option 2: [name].** Same coverage, depth proportional to how much it matters.
>
> **Option 3: [name].** (Only if genuinely distinct and worth the user's attention.)
>
> **Recommendation.** Which one, why, for this context. Confidence tier. What would change it. Reversibility note.

Keep the framing tight and spend the words on the options and the recommendation.
