| analysis | approach | countries | n | events | auroc | within_country_year_auroc | capture_at_20pct | brier |
|---|---|---|---|---|---|---|---|---|
| primary: locked test 2023-2024 | Country prior rate | 20 | 705 | 130 | 0.593 | 0.5 | 0.362 | 0.177 |
| primary: locked test 2023-2024 | History rule | 20 | 705 | 130 | 0.654 | 0.497 | 0.477 | 0.177 |
| primary: locked test 2023-2024 | Logistic, programme history | 20 | 705 | 130 | 0.673 | 0.679 | 0.408 | 0.188 |
| primary: locked test 2023-2024 | CatBoost, programme history | 20 | 705 | 130 | 0.615 | 0.702 | 0.269 | 0.191 |
| incident cohort (delivered at t-1) | Country prior rate | 19 | 596 | 79 | 0.453 | 0.5 | 0.199 | 0.162 |
| incident cohort (delivered at t-1) | History rule | 19 | 596 | 79 | 0.52 | 0.398 | 0.266 | 0.163 |
| incident cohort (delivered at t-1) | Logistic, programme history | 19 | 596 | 79 | 0.589 | 0.63 | 0.342 | 0.176 |
| incident cohort (delivered at t-1) | CatBoost, programme history | 19 | 596 | 79 | 0.558 | 0.676 | 0.189 | 0.181 |
| strict cohort (<5 rounds incl. pre-2014) | Country prior rate | 14 | 481 | 94 | 0.553 | 0.5 | 0.298 | 0.182 |
| strict cohort (<5 rounds incl. pre-2014) | History rule | 14 | 481 | 94 | 0.682 | 0.645 | 0.502 | 0.179 |
| strict cohort (<5 rounds incl. pre-2014) | Logistic, programme history | 14 | 481 | 94 | 0.711 | 0.737 | 0.404 | 0.194 |
| strict cohort (<5 rounds incl. pre-2014) | CatBoost, programme history | 14 | 481 | 94 | 0.646 | 0.749 | 0.234 | 0.196 |
| broad cohort (no round restriction; model extrapolates) | Country prior rate | 24 | 1363 | 197 | 0.646 | 0.5 | 0.377 | 0.162 |
| broad cohort (no round restriction; model extrapolates) | History rule | 24 | 1363 | 197 | 0.676 | 0.57 | 0.421 | 0.162 |
| broad cohort (no round restriction; model extrapolates) | Logistic, programme history | 24 | 1363 | 197 | 0.663 | 0.558 | 0.426 | 0.172 |
| broad cohort (no round restriction; model extrapolates) | CatBoost, programme history | 24 | 1363 | 197 | 0.685 | 0.658 | 0.269 | 0.17 |
| mixed country-years only (both outcomes present) | Country prior rate | 7 | 380 | 78 | 0.544 | 0.5 | 0.261 | 0.186 |
| mixed country-years only (both outcomes present) | History rule | 7 | 380 | 78 | 0.62 | 0.497 | 0.423 | 0.186 |
| mixed country-years only (both outcomes present) | Logistic, programme history | 7 | 380 | 78 | 0.675 | 0.679 | 0.346 | 0.188 |
| mixed country-years only (both outcomes present) | CatBoost, programme history | 7 | 380 | 78 | 0.697 | 0.702 | 0.328 | 0.189 |
| excluding carried-forward country-years | Country prior rate | 20 | 705 | 130 | 0.593 | 0.5 | 0.362 | 0.177 |
| excluding carried-forward country-years | History rule | 20 | 705 | 130 | 0.654 | 0.497 | 0.477 | 0.177 |
| excluding carried-forward country-years | Logistic, programme history | 20 | 705 | 130 | 0.673 | 0.679 | 0.408 | 0.188 |
| excluding carried-forward country-years | CatBoost, programme history | 20 | 705 | 130 | 0.615 | 0.702 | 0.269 | 0.191 |
| missing labels counted as interruptions | Country prior rate | 20 | 706 | 131 | 0.593 | 0.5 | 0.359 | 0.178 |
| missing labels counted as interruptions | History rule | 20 | 706 | 131 | 0.649 | 0.496 | 0.473 | 0.177 |
| missing labels counted as interruptions | Logistic, programme history | 20 | 706 | 131 | 0.67 | 0.677 | 0.405 | 0.188 |
| missing labels counted as interruptions | CatBoost, programme history | 20 | 706 | 131 | 0.615 | 0.7 | 0.267 | 0.191 |
| missing labels counted as delivered | Country prior rate | 20 | 706 | 130 | 0.593 | 0.5 | 0.362 | 0.177 |
| missing labels counted as delivered | History rule | 20 | 706 | 130 | 0.654 | 0.497 | 0.477 | 0.177 |
| missing labels counted as delivered | Logistic, programme history | 20 | 706 | 130 | 0.673 | 0.678 | 0.408 | 0.188 |
| missing labels counted as delivered | CatBoost, programme history | 20 | 706 | 130 | 0.615 | 0.702 | 0.269 | 0.191 |
| stress 2025 (all) | Country prior rate | 14 | 233 | 71 | 0.729 | 0.5 | 0.346 | 0.202 |
| stress 2025 (all) | History rule | 14 | 233 | 71 | 0.849 | 0.774 | 0.515 | 0.193 |
| stress 2025 (all) | Logistic, programme history | 14 | 233 | 71 | 0.774 | 0.618 | 0.445 | 0.197 |
| stress 2025 (all) | CatBoost, programme history | 14 | 233 | 71 | 0.654 | 0.653 | 0.31 | 0.21 |
| stress 2025, countries in ESPEN release log only | Country prior rate | 9 | 178 | 63 | 0.827 | 0.5 | 0.565 | 0.212 |
| stress 2025, countries in ESPEN release log only | History rule | 9 | 178 | 63 | 0.903 | 0.774 | 0.533 | 0.203 |
| stress 2025, countries in ESPEN release log only | Logistic, programme history | 9 | 178 | 63 | 0.855 | 0.618 | 0.517 | 0.198 |
| stress 2025, countries in ESPEN release log only | CatBoost, programme history | 9 | 178 | 63 | 0.776 | 0.653 | 0.362 | 0.214 |
| development folds: all events | Country prior rate | 30 | 3614 | 1122 | 0.576 | 0.5 | 0.18 | 0.235 |
| development folds: all events | History rule | 30 | 3614 | 1122 | 0.536 | 0.655 | 0.221 | 0.231 |
| development folds: all events | Logistic, programme history | 30 | 3614 | 1122 | 0.616 | 0.602 | 0.271 | 0.231 |
| development folds: all events | CatBoost, programme history | 30 | 3614 | 1122 | 0.608 | 0.642 | 0.262 | 0.24 |
| development folds: excluding events later moved to IA/surveillance | Country prior rate | 29 | 3432 | 940 | 0.559 | 0.5 | 0.188 | 0.213 |
| development folds: excluding events later moved to IA/surveillance | History rule | 29 | 3432 | 940 | 0.522 | 0.661 | 0.205 | 0.211 |
| development folds: excluding events later moved to IA/surveillance | Logistic, programme history | 29 | 3432 | 940 | 0.591 | 0.604 | 0.247 | 0.212 |
| development folds: excluding events later moved to IA/surveillance | CatBoost, programme history | 29 | 3432 | 940 | 0.58 | 0.647 | 0.242 | 0.221 |
| development folds: non-COVID years | Country prior rate | 30 | 1868 | 421 | 0.623 | 0.5 | 0.225 | 0.174 |
| development folds: non-COVID years | History rule | 30 | 1868 | 421 | 0.625 | 0.746 | 0.342 | 0.166 |
| development folds: non-COVID years | Logistic, programme history | 30 | 1868 | 421 | 0.703 | 0.675 | 0.42 | 0.164 |
| development folds: non-COVID years | CatBoost, programme history | 30 | 1868 | 421 | 0.678 | 0.713 | 0.313 | 0.173 |
