# Model tiers (update as models change)

Time-sensitive — kept out of the skill body so the procedure doesn't rot.

| Role | Tier | Current model | Effort default |
|---|---|---|---|
| **Judgment** — Keystone, Seam, all review/verify/simplify gates | frontier | Opus 5 (`claude-opus-5`) | high |
| **Application** — Sweep, Leaf | mid-tier | Sonnet 5 (`claude-sonnet-5`) | medium |
| Trivial/cheap (rarely — only pure-mechanical, non-consistency-critical) | small | Haiku 4.5 (`claude-haiku-4-5-20251001`) | low |

Rules:
- Default to the session model; deviate deliberately.
- Never review or verify with a weaker model than implemented.
- Consistency-critical sweeps stay on the frontier model (or add a frontier verify pass).

Latest family (as of Aug 2026): the Claude 5 line — Fable 5 (`claude-fable-5`),
Opus 5 (`claude-opus-5`), Sonnet 5 (`claude-sonnet-5`) — plus Haiku 4.5. When
building anything model-facing, default to the latest/most capable Claude models
and refresh this table.
