| Approach | Role | Predictors | Setting chosen on development folds | Development log loss | Locked-test AUROC (95% CI) | Interruptions captured in top 20% (95% CI) | Difference from history rule, percentage points (95% CI) |
|---|---|---|---|---|---|---|---|
| No-skill prevalence |  | None (training prevalence for every IU) | none to tune | 0.695 | 0.50 (0.50 to 0.50) | 0.20 (0.20 to 0.20) | -27.7 (-47.9 to +0.0) |
| Country prior rate |  | Country's non-delivery rate the year before | none to tune | 0.686 | 0.59 (0.39 to 0.81) | 0.36 (0.12 to 0.63) | -11.5 (-37.0 to +13.5) |
| History rule | Comparator | Fixed points: missed t-1, missed t-2 or t-3, ineffective round at t-1 | none to tune | 0.688 | 0.65 (0.43 to 0.82) | 0.48 (0.20 to 0.68) | reference |
| Logistic, five predictors |  | 5: missed rounds in 3 years, cumulative rounds, last coverage, region and country non-delivery rates | C = 0.001 | 0.680 | 0.66 (0.44 to 0.81) | 0.42 (0.14 to 0.63) | -6.2 (-25.2 to +9.1) |
| Logistic, IU history only | Primary candidate | IU treatment history (11 predictors) | C = 0.001 | 0.678 | 0.64 (0.43 to 0.79) | 0.38 (0.13 to 0.59) | -10.0 (-29.1 to +9.7) |
| Logistic, programme history |  | IU history plus country and region programme history (17) | C = 0.001 | 0.687 | 0.67 (0.48 to 0.81) | 0.41 (0.17 to 0.59) | -6.9 (-22.7 to +9.4) |
| Logistic, history + context |  | Programme history plus conflict and population density (24) | C = 0.001 | 0.706 | 0.56 (0.32 to 0.76) | 0.18 (0.02 to 0.47) | -30.0 (-53.6 to +5.1) |
| CatBoost, programme history |  | IU history plus country and region programme history (17) | depth = 1, l2_leaf_reg = 30 | 0.732 | 0.62 (0.35 to 0.81) | 0.27 (0.01 to 0.50) | -20.8 (-57.2 to +5.1) |
| CatBoost, history + context |  | Programme history plus conflict and population density (24) | depth = 1, l2_leaf_reg = 30 | 0.754 | 0.59 (0.33 to 0.78) | 0.25 (0.00 to 0.49) | -23.1 (-57.2 to +6.1) |
| CatBoost, history + country ID |  | Programme history plus country identity (18) | depth = 1, l2_leaf_reg = 30 | 0.731 | 0.56 (0.31 to 0.77) | 0.16 (0.00 to 0.44) | -31.5 (-63.6 to +11.3) |
