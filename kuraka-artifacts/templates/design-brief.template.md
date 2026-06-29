<!--
  Design brief template — output of the Discovery / Tinkuy flow
  (see skills/facilitate-discovery.md). The orchestrator writes the filled
  version to the CONSUMER PROJECT at:
      docs/discovery/design-brief-{slug}.md
  Keep it <= 250 LOC. This is the fuzzy front-end deliverable that FEEDS
  po-analyst (existing project) or inti/arki (greenfield) — it does NOT
  replace the REQ. Scope here is explicitly tentative; po-analyst owns the
  real scope gate. Delete this comment in the filled version.
-->

# {Project / feature name} — Design Brief

## One-liner
{10–20 words capturing the core of the idea}

## Domain & core value
- **Domain**: {accounting / logistics / health / ...}
- **Who uses it**: {persona, 1 sentence}
- **Core value**: {what they can do that they can't today}

## The council
| Expert (slug) | Lens | Why this voice |
|---|---|---|
| {contador} | {accounting correctness} | {…} |
| {admin-finanzas} | {business process} | {…} |
| … | … | … |

Rounds run: {n}. Convergence reached: {yes / partial — see open questions}.

## Domain bases (agreed)
Entities, processes, and business rules surfaced by the council and
accepted by the user. Tag externally-governed rules.

### Entities (draft)
- **{Entity}**: {purpose, key attributes, relationships}
- …

### Processes / flows
1. {flow}: {brief}
2. …

### Business rules
- {rule the system MUST respect}
- ⚠️ VALIDAR con experto humano — {regulatory/fiscal/standard rule that
  needs a real domain expert to confirm before it drives the build}

## Tentative scope (NOT the final REQ)
**In (tentative)**
- {…}

**Out / deferred (tentative)**
- {…}

## Conflicts & decisions
| Topic | Expert positions | User decision | Decided by |
|---|---|---|---|
| {…} | {A says X / B says Y} | {chosen} | {user, verbatim} |

## Glossary seed
For `.claude/project/glossary.md`.
- **{term}**: {definition}
- …

## Open questions
1. {for the user / po-analyst / a human domain expert}
2. …

## Risks
- {risk} — {impact / mitigation note}
- ⚠️ VALIDAR con experto humano — {…}

## Promoted experts
Experts kept as permanent project agents (`.claude/project/agents/`), if
any. Requires a Claude Code restart to register.
- `{slug}` — {lens; when later phases should invoke it}
- (none) {if the user chose to keep the council ephemeral}

## Next step
- Existing / mid-project → `/kuraka` → Phase 1 `po-analyst` reads this brief.
- Greenfield → `inti` then `arki`, both reading this brief.

## Confidence: HIGH / MEDIUM / LOW
