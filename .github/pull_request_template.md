## What problem does this solve?

Link the issue or RFC if applicable. Describe the actual change and its user-visible result.

## Scope and evidence

Explain relevant design choices, technical sources, and any limitations. Include screenshots for visual changes or reproducible steps and licensed fixtures for behavior changes. Clearly label proposed behavior that is not implemented.

## Validation

List the exact commands you ran and their results. State checks you could not run and why.

```text
python tools/check_docs.py
python tools/build_site.py --output work/site
```

## AI disclosure

```text
AI assistance: none / assisted / agent-authored
Provider and model/version: exact identifier, or unknown
Scope of assistance:
Accountable contributor or proposed maintainer sponsor: @handle
Human review performed, or pending:
```

For AI-authored code and architecture, the owner's quality bar is GPT-6.1 Sol, Astra, Claude Opus 5.5 level, or equivalent/higher. See [the policy](https://github.com/Ramses13th/B-CAD/blob/main/docs/ai-contributions.md). This is an owner-defined requirement, not a verified model ranking. Human maintainer review is required before merge.

## Contributor checklist

- [ ] This is a focused change, with an issue or RFC for substantial design decisions.
- [ ] I distinguish the current blueprint from implemented functionality and do not claim unrun checks passed.
- [ ] Documentation matches the actual change.
- [ ] I have the right to contribute the included material under GPL-3.0-or-later and preserved required attribution and license notices.
- [ ] I removed secrets, personal information, and proprietary models from the change and evidence.
- [ ] I read the contribution guide and Code of Conduct.
