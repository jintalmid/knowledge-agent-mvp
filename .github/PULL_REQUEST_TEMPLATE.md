## Summary

Describe what changed.

## Module(s)

List affected modules, for example `M07 Agent Runner Service`.

## Validation

- [ ] `python -m compileall backend/app`
- [ ] `npm run build` from `frontend`
- [ ] Manual API/page test if applicable

## LLM / Agent Impact

- [ ] No LLM behavior changed
- [ ] LLM prompts changed and logs still go through unified LLM Service
- [ ] Tool behavior changed and Tool Registry docs were updated
- [ ] Agent Runner behavior changed and module docs were updated

## Security Checklist

- [ ] No secrets committed
- [ ] `.env`, SQLite databases, uploads, and local build output are not committed
- [ ] File access and sandbox behavior remain restricted
- [ ] User-provided file content is handled through existing parsing/tool boundaries

## Documentation

- [ ] README updated if needed
- [ ] Module docs updated if needed
