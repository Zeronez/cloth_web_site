# CI Notes

- `production.yml` sets `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24=true` at the workflow level so GitHub-hosted JavaScript actions run on Node 24 while we keep the current action versions unchanged.
- This is a compatibility measure for the Node 20 deprecation warning, not a broader CI behavior change.
