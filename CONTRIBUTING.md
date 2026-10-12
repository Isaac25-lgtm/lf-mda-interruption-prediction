# Contributing

This is a research repository. Changes are welcome if they keep the study honest.

## Ground rules

1. **No invented data or results.** Synthetic data may appear only in `tests/` and in
   the dashboard's labelled demonstration mode.
2. **The protocol is frozen.** `config/protocol.yaml` may change only through a dated
   entry in its `amendments` list and in `docs/DECISIONS.md`, with the reason. A change
   made after seeing locked-test results must be labelled exploratory.
3. **No new predictor without a manifest entry.** Add it to `config/features.yaml` with
   its source, lag and missing-data rule. The as-of tests must still pass.
4. **No new model without a hypothesis.** The model set is deliberately small.
5. **Raw data never go into Git.** Neither do secrets, boundary polygons or model binaries.

## Workflow

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
```

Use small commits with a prefix (`build:`, `data:`, `model:`, `dashboard:`, `docs:`,
`test:`). Open a pull request against `main`; CI must pass. Do not force-push.

## Reporting a problem

Open an issue describing what you ran, what you expected and what happened. If you
think a label, a split or a predictor leaks information, say which file and line; that
kind of report is the most valuable one.
