# Fitted models

Model binaries are written here by `lf-mda lock` and are **not committed**: they are
rebuilt deterministically from the raw data, the protocol and the seed.

- `P_*.cbm`, `E_*.cbm`: CatBoost models for information scenarios P and E.
- `P_*.joblib`, `E_*.joblib`: baselines and logistic pipelines (imputer, scaler, encoder
  and model in one object, all fitted on training rows only).
- `model_digests.json`: SHA-256 of each file from the locked run (committed).

Each scenario P model is trained on development target years 2016-2022; scenario E
models on 2016-2021. The Platt recalibration coefficients are in
`reports/evaluation/development/calibrators.json`.

These models predict a reported administrative status that has not been verified by
programme experts. They are research artifacts, not decision tools.
