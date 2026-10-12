EXPLORATORY, POST HOC models proposed after the locked test had been opened.

Nothing in this module is confirmatory. These approaches were designed on 2026-10-12
after the locked-test results for the pre-specified models were known. They are
developed and tuned on development folds only, but their held-out numbers cannot count
as an independent test: the design choices were made with knowledge of how the
pre-specified models performed on those same years. A new, untouched year of data is
needed before any of them can be claimed to work.

Motivation, from the audit and the pre-specified results:
  * about 60% of outcome variance lies between country-years, so a model should
    separate "which country-year" from "which IU inside it";
  * the fixed rule ranked well across countries but not within them on the locked
    test, while fitted models did the reverse.

Approaches:
  X1 within_between_logistic  - ridge logistic on country-year means of the IU
     predictors plus each IU's deviation from its country-year mean (a Mundlak-type
     within/between decomposition). Means use predictors only, never outcomes.
  X2 two_level_rank           - rank countries by prior-year non-delivery rate, then
     IUs within a country by the history rule (no fitting for the ranking).
  X3 rule_plus_rounds         - the history rule with one extra term: fewer cumulative
     rounds raises the score (the strongest single within-country predictor on
     development data).
