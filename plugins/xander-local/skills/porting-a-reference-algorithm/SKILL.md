---
name: porting-a-reference-algorithm
description: A checkable procedure for transcribing an external algorithm (a paper, or a reference implementation) into a codebase. Use whenever matching code to an outside source — before making any claim about what that source does. Covers assembling references, citing file:line, diffing not inspecting, pinning behaviour with a golden fixture plus behavioural controls, mutation-testing the suite, and recording every deviation.
---

# Porting a reference algorithm

A port is **transcription under an oracle**. Where you have a reference, match it. Where
references disagree, the deliverable is a *recorded decision*, not a "fix."

This is a procedure, not advice, because the failures it prevents **cluster**: the same
class of error tends to recur — often inside the very commit that recorded the lesson about
it. "Be faithful" and "be careful" are unactionable. Each step below has an **observable
output**, so you can check whether you actually did it.

## The procedure

1. **ASSEMBLE every reference implementation locally, first.**
   Fetch each source (paper text, every reference implementation) into a `refs/` directory
   *before* making any claim about them.
   → Output: a `refs/` dir with each source on disk. Not "I recall the paper says."

2. **CITE `file:line` for every claim about what a reference does.**
   "The reference uses X" is a category error the moment more than one implementation
   exists — and **the runnable one is not the authoritative one.** The reference that
   happens to be pip-installable is often the one carrying transcription bugs the original
   author never had.
   → Output: every factual claim about the source carries a `path:line` citation.

3. **DIFF against the source line-by-line; do not inspect-and-summarize.**
   Micro-deviations — a dropped zero, a reassociated division, an edge placed at `data.min()`
   instead of `0` — hide from inspection and from a register that says "nothing else." They
   surface only under a literal line-by-line comparison.
   → Output: a diff (or a per-line reconciliation), not a prose summary.

4. **PIN behaviour with BOTH a golden fixture AND behavioural controls.**
   They answer different questions. A golden fixture answers "is it *this* algorithm?"; a
   behavioural control answers "does it behave like this *kind* of algorithm?" A bug can be
   invisible to one and caught only by the other.
   - Store **every** output in the fixture, not just the headline one — a fixture that omits
     an output is blind to every bug in it.
   - The fixture pins **transcription, not correctness** — doubly so when the reference itself
     ships no tests. Correctness comes from the behavioural controls and from independent
     derivations.
   → Output: a committed fixture covering all outputs, plus behavioural tests.

5. **PROVE the fixture is load-bearing.**
   Reintroduce the exact bug the fixture is meant to catch and confirm it fails. A fixture that
   cannot fail proves nothing.
   → Output: a recorded before/after showing the guard fires.

6. **MUTATION-TEST the suite.**
   Inject each plausible bug; a surviving mutant is a hole. This is the only honest answer to
   "could a test pass while the code is wrong?" — you cannot see it by reading the tests.
   Verify each mutant is the **single** intended change: if you mutate two things at once, the
   errors can cancel and the mutant falsely "passes."
   → Output: a mutant × test matrix; every mutant killed by at least one test.

7. **ONE deviation register row per deviation, however numerically small.**
   A 1-ulp reassociation is still a shortcut and still earns a row. Faithfulness is about the
   **logic**, not the size of the error. Categorise each: forced / contract-required /
   capability-we-added / defect.
   → Output: a row (with evidence) for every place the code departs from the reference.

8. **Where you must deviate, copy the reference's PRINCIPLE, correctly instantiated — never
   its bank-specific CONSTANTS transplanted onto a different setup.**
   A noise-extrapolation law derived for one filter bank is wrong on another even when copied
   verbatim; the *principle* ("scale by relative bandwidth") is what transfers.

## Anti-patterns, each from a real failure

- Generalising "the reference does X" from the one implementation you happened to install.
  Three such claims can all be wrong, and all die to a single `grep`/`curl` of a file that
  was one fetch away the whole time.
- Treating a genuine fork between two references as a bug to fix. Record which you chose and
  why; prefer the author's latest word, but write down the fork.
- A behavioural suite mistaken for a correctness net: it can pass while the code computes the
  wrong thing. Keep the fixture too.
- A tolerance loose enough to "carry" an assertion (`±0.5` on a value off by `0.17`) — the
  anchor does no work. And the opposite: bit-exact `== 0.0` on reassociated float math gives
  false failures. Derive the bound from a mechanism.

## Artifact

Step 4's fixture and the executable check that re-derives the load-bearing numeric claims are
durable artifacts, not scratch. If the project defines a home for them (e.g. a
`logic_validation_scripts/` convention), put them there so they stay runnable and are not lost
across a long change; otherwise co-locate them with the spec/plan they back and commit them.
