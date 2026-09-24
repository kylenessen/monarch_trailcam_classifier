# Contributing

Please open an issue describing the expected behavior, what happened, the application version and operating system. Include a small reproducible example when possible. Keep unpublished photographs and personal information out of issue attachments.

Use Node.js 22 for application development. From `electron-app`, run `npm ci` and `npm run test:e2e -- --workers=1`. From the repository root, run `uv run --no-project python -m unittest discover -s tools -p 'test_*.py'` for the annotation preparation checks. The macOS workflow runs both sets of checks.

Do not edit the archived JSON files or their checksums to make an application test pass. Tests should use temporary copies. The `docs` directory is the historical protocol shared with the research team and is intentionally preserved. Current user instructions belong in GETTING_STARTED.md.
