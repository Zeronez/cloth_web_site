$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$backendDir = $repoRoot

docker run --rm `
  -v "${backendDir}:/app" `
  -w /app `
  python:3.12-slim `
  sh -lc "python -m pip install --no-cache-dir pip-tools && pip-compile --strip-extras --resolver=backtracking --output-file requirements.txt requirements.in && pip-compile --strip-extras --resolver=backtracking --output-file requirements-dev.txt requirements-dev.in"
