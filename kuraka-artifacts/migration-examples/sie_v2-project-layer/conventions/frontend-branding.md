# Frontend branding — sie_v2 (Guai Platform)

Brand colors and visual identity. Loaded by `frontend-developer` and
`code-reviewer` when reviewing frontend changes.

## Brand colors

| Token | Hex | Use |
|---|---|---|
| Primary | `#CCFF00` | CTAs, primary actions, brand emphasis |
| Background | `#0A0A0A` | App background, dark mode default |
| Accent | `#B7FF1E` | Highlights, hover/active states |

Use these via Tailwind theme tokens (`bg-brand-primary`, `text-brand-bg`,
`border-brand-accent`) configured in `tailwind.config.js`. Do not
inline the hex values in components.

## Anti-patterns

- Inline `style="background-color: #CCFF00"` — bypasses the theme.
- Using close-but-not-exact shades (`#CCFF22`, `#0F0F0F`) — defeats the
  brand consistency. The theme has 3 colors; new colors require approval
  and a token addition.
- Using brand colors for error/warning/success states — those have their
  own semantic tokens (`text-error`, `bg-warning`, etc.).

## Where it's enforced

- `frontend-developer` agent during implementation.
- `code-reviewer` during Phase 5 (flags inline hex usage as IMPORTANT
  finding).

## Related

- `tailwind.config.js` at the project root — single source of truth for
  the token names that resolve to these hex values.
