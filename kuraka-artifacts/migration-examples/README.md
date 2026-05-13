# Migration Examples

This directory holds **concrete instantiations** of the project specialization
layer for real projects. Their purpose is twofold:

1. **Reference**: show what a populated `<project>/.claude/project/` looks
   like, so a new consumer can see (not just read about) the structure.
2. **Migration source**: the sie_v2 example is the actual content that the
   sie_v2 team copies into their project as the Fase 3 refactor extracts
   sie_v2-specific knowledge out of the framework agents.

## Layout

```
kuraka-artifacts/migration-examples/
├── README.md                          # this file
└── sie_v2-project-layer/              # for the sie_v2 project (drives Fase 3.5)
    ├── README.md
    ├── conventions/
    ├── review-checks/
    ├── lessons-learned/
    ├── glossary.md
    └── agents/
```

## How sie_v2 consumes its example

When the sie_v2 team is ready to migrate, they run something like:

```bash
cp -r <kuraka-vault>/kuraka-artifacts/migration-examples/sie_v2-project-layer/. \
      <sie_v2-repo>/.claude/project/
```

After that, the sie_v2 project layer is populated and the refactored agents
can load it at invocation. The migration is irreversible from the framework
side; on the consumer side, the team owns and curates the project layer
going forward.

## Adding more examples

A future contributor with a non-sie_v2 project can add their own example
here as documentation. Suggested layout: `{project-name}-project-layer/`.
