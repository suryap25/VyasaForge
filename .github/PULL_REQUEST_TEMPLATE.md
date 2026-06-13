## Summary

Describe the change and why it is needed.

## Scope

- [ ] Code
- [ ] Prompts
- [ ] Config
- [ ] Documentation
- [ ] CI / packaging

## Validation

Commands run:

```text
python -m compileall src
python -m src.cli --help
python -m src.cli doctor
```

## Safety Checklist

- [ ] No API keys, prompts with secrets, or generated private content committed
- [ ] Generated artifacts are excluded
- [ ] Provider-specific logic remains inside provider/gateway layers
- [ ] Prompt changes include clear input/output contracts
- [ ] Documentation updated when user-facing behavior changed

## Notes for Maintainers

Call out migration notes, follow-up work, or areas needing extra review.
