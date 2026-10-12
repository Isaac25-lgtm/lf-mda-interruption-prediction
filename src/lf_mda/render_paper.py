"""Render publication tables and figures from saved audit and evaluation artifacts.

Nothing here computes a new result: every number is read from files written by the
audit and pipeline steps. Captions and alt text are generated alongside each figure
into manuscript/figures_and_tables.md so they cannot drift from the data.
"""
from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

from . import paths  # noqa: E402
from .evaluate import top_k_counts  # noqa: E402
from .model import SPEC_BY_NAME  # noqa: E402

SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
# Fixed entity -> colour assignment (categorical slots in validated order).
MODEL_COLOR = {"history_rule": "#2a78d6", "logistic_history": "#eb6834",
               "catboost_history": "#1baf7a", "country_prior_rate": "#eda100"}
NEUTRAL = "#8a8983"
SEQ = LinearSegmentedColormap.from_list("seq_blue", ["#cde2fb", "#6da7ec", "#256abf", "#0d366b"])
KEY = ["country_prior_rate", "history_rule", "logistic_history", "catboost_history"]
SHORT = {"prevalence": "No-skill prevalence", "country_prior_rate": "Country prior rate",
         "history_rule": "History rule", "logistic_parsimonious": "Logistic, five predictors",
         "logistic_iu_only": "Logistic, IU history only",
         "logistic_history": "Logistic, programme history",
         "logistic_history_context": "Logistic, history + context",
         "catboost_history": "CatBoost, programme history",
         "catboost_history_context": "CatBoost, history + context",
         "catboost_history_country_id": "CatBoost, history + country ID"}
CLASS_COLOR = {"delivered": "#2a78d6", "reported_interruption": "#eb6834",
               "excluded (pause, stop, missing, other)": "#c9c8c2"}

DEV = paths.EVALUATION / "development"
LOCK = paths.EVALUATION / "locked_test"
LOCO = paths.EVALUATION / "country_transport"
SENS = paths.EVALUATION / "sensitivity"
EXPL = paths.EVALUATION / "explain"
CAPTIONS: list[dict] = []
NL = chr(10)


def _style() -> None:
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": GRID,
        "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
        "axes.titlecolor": INK, "axes.titlesize": 10, "axes.titleweight": "bold",
        "axes.titlelocation": "left", "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
        "legend.frameon": False, "lines.linewidth": 2, "lines.markersize": 6,
    })


def _save(fig, name: str, title: str, caption: str, alt: str, sources: list[str]) -> None:
    paths.FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(paths.FIGURES / f"{name}.png", dpi=220, bbox_inches="tight")
    plt.close(fig)
    CAPTIONS.append({"id": name, "kind": "figure", "title": title, "caption": caption,
                     "alt": alt, "sources": sources})


def _table(df: pd.DataFrame, name: str, title: str, caption: str, sources: list[str]) -> None:
    paths.TABLES.mkdir(parents=True, exist_ok=True)
    df.to_csv(paths.TABLES / f"{name}.csv", index=False)
    (paths.TABLES / f"{name}.md").write_text(_md(df), encoding="utf-8")
    CAPTIONS.append({"id": name, "kind": "table", "title": title, "caption": caption,
                     "alt": "", "sources": sources})


def _md(df: pd.DataFrame) -> str:
    head = "| " + " | ".join(map(str, df.columns)) + " |"
    sep = "|" + "|".join(["---"] * len(df.columns)) + "|"
    body = ["| " + " | ".join("" if pd.isna(v) else str(v) for v in r) + " |"
            for r in df.itertuples(index=False)]
    return "\n".join([head, sep] + body) + "\n"


def _fmt_ci(est, lo, hi, digits=2) -> str:
    if pd.isna(est):
        return "not estimable"
    if pd.isna(lo):
        return f"{est:.{digits}f}"
    return f"{est:.{digits}f} ({lo:.{digits}f} to {hi:.{digits}f})"


def _gate() -> dict:
    return json.loads((paths.AUDIT / "gate_decision.json").read_text("utf-8"))


# ------------------------------------------------------------------ figures
def fig_decision_schematic() -> None:
    fig, ax = plt.subplots(figsize=(8.2, 2.9))
    ax.axis("off")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 3)
    ax.annotate("", xy=(9.8, 1.2), xytext=(0.2, 1.2),
                arrowprops=dict(arrowstyle="-|>", color=INK2, lw=1.2))
    boxes = [(0.3, "Years t-3 to t-1", "Treatment history known\nto the programme:\ndelivery, coverage, rounds"),
             (3.5, "31 December, year t-1", "DECISION DATE\nRank active IUs by risk;\nallocate supervision"),
             (6.7, "Year t", "OUTCOME\nRound delivered, or reported\n'MDA not delivered'")]
    for x, head, body in boxes:
        ax.add_patch(FancyBboxPatch((x, 1.55), 2.9, 1.25, boxstyle="round,pad=0.04",
                                    fc="#eef4fc" if "DECISION" not in body else "#fdeee7",
                                    ec=GRID, lw=1))
        ax.text(x + 1.45, 2.58, head, ha="center", va="center", fontsize=9, weight="bold",
                color=INK)
        ax.text(x + 1.45, 2.05, body, ha="center", va="center", fontsize=8, color=INK2)
        ax.plot([x + 1.45], [1.2], "o", color=INK2, ms=5)
    ax.text(1.75, 0.75, "Scenario P: features use rows up to t-1", ha="center", fontsize=8,
            color=INK2)
    ax.text(1.75, 0.4, "Scenario E (public data lag): up to t-2", ha="center", fontsize=8,
            color=INK2)
    ax.text(8.15, 0.75, "Outcome-year fields are used only to\nclassify the outcome, never as predictors",
            ha="center", fontsize=8, color=INK2)
    _save(fig, "fig1_decision_schematic", "Prediction clock and information scenarios",
          "The decision date is 31 December of year t-1. Predictors use only records dated "
          "t-1 or earlier (scenario P) or t-2 or earlier (scenario E, reflecting the delay "
          "before ESPEN data are public). Outcome-year records classify the outcome only.",
          "Timeline with three boxes: treatment history in years t-3 to t-1, the decision "
          "date at the end of year t-1, and the outcome in year t.", ["config/protocol.yaml"])


def fig_cohort_flow() -> None:
    flow = pd.read_csv(paths.AUDIT / "cohort_flow.csv")
    n = dict(zip(flow["step"], flow["n"]))

    def get(prefix):
        return next(v for k, v in n.items() if k.strip().startswith(prefix))

    main = [("IU-year cells, target years 2016-2025", get("Target years")),
            ("Requiring MDA at t-1", get("Requiring MDA")),
            ("Delivered MDA in t-1 or t-2\n(broad cohort)", get("Broad cohort")),
            ("Fewer than 5 observed effective rounds\n(primary cohort)", get("Primary cohort")),
            ("Binary outcome available\n(primary analysis set)", get("Primary analysis set"))]
    plain = {"surveillance_or_stopped": "surveillance or stopped",
             "legitimate_pause_IA": "pending impact assessment", "missing_JRF": "not reported",
             "missing_iu_year": "no record", "contradictory": "contradictory record",
             "unknown": "status unknown"}
    excl = [f"Not requiring MDA at t-1: {main[0][1] - main[1][1]:,}",
            f"No delivery in t-1 or t-2: {get('excluded: no delivery'):,}",
            f"5+ effective rounds (due for assessment): {get('excluded: >=5'):,}",
            "Outcome year excluded: " + ", ".join(
                f"{plain.get(k.split(': ')[1].split(' (')[0], 'other')} {v:,}"
                for k, v in n.items() if "excluded, counted" in k)]
    fig, ax = plt.subplots(figsize=(8.4, 5.6))
    ax.axis("off")
    ax.set_xlim(0, 10)
    ax.set_ylim(-0.4, 10.4)
    for i, (label, count) in enumerate(main):
        y = 9.3 - i * 2.0
        ax.add_patch(FancyBboxPatch((0.2, y - 0.55), 4.6, 1.1, boxstyle="round,pad=0.04",
                                    fc="#eef4fc", ec=GRID))
        ax.text(2.5, y, f"{label}\nn = {count:,}", ha="center", va="center", fontsize=8.5,
                color=INK)
        if i < len(main) - 1:
            ax.annotate("", xy=(2.5, y - 1.42), xytext=(2.5, y - 0.6),
                        arrowprops=dict(arrowstyle="-|>", color=INK2, lw=1))
            ax.annotate("", xy=(5.3, y - 1.0), xytext=(2.5, y - 1.0),
                        arrowprops=dict(arrowstyle="-|>", color=NEUTRAL, lw=0.8))
            ax.text(5.4, y - 1.0, excl[i], ha="left", va="center", fontsize=7.6, color=INK2,
                    wrap=True)
    ev = get("reported interruptions")
    ax.text(2.5, 0.2, f"Reported interruptions: {ev:,}    Delivered: {main[-1][1] - ev:,}",
            ha="center", fontsize=8.5, weight="bold", color=INK)
    _save(fig, "fig2_cohort_flow", "Cohort flow with actual counts",
          f"Selection of the primary analysis set from all IU-year cells. Final set: "
          f"{main[-1][1]:,} IU-years with {ev:,} reported interruptions.",
          "Flow chart of five boxes showing how IU-years are narrowed to the primary analysis "
          "set, with the number excluded at each step.", ["reports/audit/cohort_flow.csv"])


def fig_outcomes_by_year() -> None:
    t = pd.read_csv(paths.AUDIT / "primary_cohort_outcome_class_by_year.csv").set_index("year")
    d = pd.DataFrame({"delivered": t.get("delivered", 0),
                      "reported_interruption": t.get("reported_interruption", 0)})
    d["excluded (pause, stop, missing, other)"] = t.drop(
        columns=[c for c in ("delivered", "reported_interruption") if c in t]).sum(axis=1)
    fig, axes = plt.subplots(2, 1, figsize=(7.6, 5.4), sharex=True,
                             gridspec_kw={"height_ratios": [2.2, 1]})
    bottom = np.zeros(len(d))
    for col in d.columns:
        axes[0].bar(d.index, d[col], bottom=bottom, color=CLASS_COLOR[col], width=0.72,
                    edgecolor=SURFACE, linewidth=1.5,
                    label=col.replace("_", " ").capitalize())
        bottom += d[col].to_numpy()
    axes[0].set_ylabel("IU-years in primary cohort")
    axes[0].set_title("Outcome-year status of the primary cohort")
    axes[0].legend(loc="center right", fontsize=8)
    axes[0].grid(axis="x", visible=False)
    rate = d["reported_interruption"] / (d["reported_interruption"] + d["delivered"])
    axes[1].plot(d.index, rate * 100, "-o", color="#eb6834")
    for x, v in rate.items():
        axes[1].text(x, v * 100 + 4, f"{v:.0%}", ha="center", fontsize=7.5, color=INK2)
    axes[1].set_ylim(0, max(70, rate.max() * 100 + 15))
    axes[1].set_ylabel("Interrupted, %")
    axes[1].set_title("Share of labelled IU-years with a reported interruption")
    axes[1].set_xticks(d.index)
    for ax in axes:
        ax.axvspan(2019.5, 2021.5, color=GRID, alpha=0.5, lw=0, zorder=0)
        ax.axvspan(2024.5, 2025.5, color=GRID, alpha=0.5, lw=0, zorder=0)
    axes[0].text(2020.5, axes[0].get_ylim()[1] * 0.93, "COVID-19\nstress years", ha="center",
                 fontsize=7.5, color=INK2)
    axes[0].text(2025, axes[0].get_ylim()[1] * 0.93, "2025\nstress", ha="center", fontsize=7.5,
                 color=INK2)
    _save(fig, "fig3_outcomes_by_year", "Outcome classes and interruption rate by year",
          "Top: IU-years in the primary cohort by outcome-year status. Bottom: reported "
          "interruptions as a share of IU-years with a binary outcome. Shaded years are "
          "pre-specified stress periods.",
          "Stacked bar chart of delivered, interrupted and excluded IU-years per year from "
          "2016 to 2025, above a line chart of the yearly interruption percentage.",
          ["reports/audit/primary_cohort_outcome_class_by_year.csv"])


def fig_country_year_heatmap() -> None:
    cy = pd.read_csv(paths.AUDIT / "country_year_event_rates.csv")
    order = cy.groupby("country")["events"].sum().sort_values(ascending=False).index
    rate = cy.pivot(index="country", columns="year", values="rate").reindex(order)
    n = cy.pivot(index="country", columns="year", values="n").reindex(order)
    fig, ax = plt.subplots(figsize=(7.8, 8.2))
    ax.grid(False)
    im = ax.imshow(rate.to_numpy(), cmap=SEQ, vmin=0, vmax=1, aspect="auto")
    for i in range(rate.shape[0]):
        for j in range(rate.shape[1]):
            if not np.isnan(n.iat[i, j]):
                ax.text(j, i, f"{int(n.iat[i, j])}", ha="center", va="center", fontsize=6.3,
                        color="#ffffff" if rate.iat[i, j] > 0.55 else INK)
    ax.set_xticks(range(rate.shape[1]), rate.columns)
    ax.set_yticks(range(rate.shape[0]), rate.index, fontsize=7.5)
    ax.set_xticks(np.arange(-0.5, rate.shape[1]), minor=True)
    ax.set_yticks(np.arange(-0.5, rate.shape[0]), minor=True)
    ax.grid(which="minor", color=SURFACE, linewidth=2)
    ax.tick_params(which="both", length=0)
    cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cb.set_label("Share of eligible IUs with reported interruption")
    cb.outline.set_visible(False)
    ax.set_title("Reported interruptions cluster by country and year")
    g = _gate()["metrics"]
    _save(fig, "fig4_country_year_heatmap", "Interruption rate by country and year",
          f"Each cell is one country-year in the primary cohort; colour is the share of eligible "
          f"IUs with a reported interruption and the number is the count of eligible IUs. Blank "
          f"cells have no eligible IUs. {g['events_in_whole_country_failures']} of "
          f"{g['primary_events']} events fall in country-years where every eligible IU missed "
          f"the round.",
          "Heat map with countries as rows and years 2016 to 2025 as columns. Many cells are "
          "either very light or very dark, showing that whole countries tend to deliver or "
          "miss a round together.", ["reports/audit/country_year_event_rates.csv"])


def fig_country_contribution() -> None:
    c = pd.read_csv(paths.AUDIT / "primary_cohort_by_country.csv").sort_values("iu_years")
    fig, ax = plt.subplots(figsize=(7.4, 7.6))
    ax.barh(c["country"], c["iu_years"] - c["events"], color="#2a78d6", height=0.68,
            label="Delivered")
    ax.barh(c["country"], c["events"], left=c["iu_years"] - c["events"], color="#eb6834",
            height=0.68, edgecolor=SURFACE, linewidth=0.5, label="Reported interruption")
    for y, (tot, ev) in enumerate(zip(c["iu_years"], c["events"])):
        ax.text(tot + 25, y, f"{int(ev)} / {int(tot)}", va="center", fontsize=7, color=INK2)
    ax.set_xlabel("IU-years in primary analysis set (label: events / IU-years)")
    ax.set_title("Countries contributing observations and events")
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="y", labelsize=7.5, length=0)
    ax.legend(loc="lower right", fontsize=8)
    ax.set_xlim(0, c["iu_years"].max() * 1.15)
    _save(fig, "fig5_country_contribution", "Study countries: observations and events",
          f"IU-years and reported interruptions per country in the primary analysis set "
          f"({len(c)} countries; {int((c['events'] > 0).sum())} with at least one event).",
          "Horizontal stacked bars, one per country, showing delivered and interrupted "
          "IU-years. Nigeria is by far the largest contributor.",
          ["reports/audit/primary_cohort_by_country.csv"])


def _forest(ax, ci: pd.DataFrame, metric: str, models: list[str], title: str, ref=None) -> None:
    sub = ci[ci["metric"] == metric].set_index("model").reindex(models)
    y = np.arange(len(models))[::-1]
    for yi, m in zip(y, models):
        r = sub.loc[m]
        if pd.isna(r["estimate"]):
            continue
        color = MODEL_COLOR.get(m, NEUTRAL)
        if not pd.isna(r["ci_low"]):
            ax.plot([r["ci_low"], r["ci_high"]], [yi, yi], color=color, lw=2,
                    solid_capstyle="round")
        ax.plot(r["estimate"], yi, "o", color=color, ms=7, mec=SURFACE, mew=1.5)
        ax.text(1.02, yi, f"{r['estimate']:.2f}", transform=ax.get_yaxis_transform(),
                va="center", fontsize=7.5, color=INK2)
    if ref is not None:
        ax.axvline(ref, color=NEUTRAL, lw=1, ls=(0, (3, 3)))
    ax.set_yticks(y, [SHORT[m] for m in models], fontsize=8)
    ax.set_title(title)
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="y", length=0)


def fig_model_comparison() -> None:
    lock = pd.read_csv(LOCK / "locked_intervals.csv")
    lock = lock[(lock["scenario"] == "P") & (lock["subset"] == "locked_test_2023_2024")]
    dev = pd.read_csv(DEV / "development_intervals.csv")
    dev = dev[(dev["scenario"] == "P") & (dev["subset"] == "rolling_2019_2022")]
    models = [m for m in SHORT if m in set(lock["model"]) and m != "prevalence"]
    fig, axes = plt.subplots(2, 3, figsize=(12.6, 6.6), sharey=True)
    for row, (ci, tag) in enumerate([(dev, "Development folds 2019-2022"),
                                     (lock, "Locked test 2023-2024")]):
        _forest(axes[row, 0], ci, "auroc", models, f"{tag}: AUROC", ref=0.5)
        _forest(axes[row, 1], ci, "within_country_year_auroc", models,
                "AUROC within country-year", ref=0.5)
        _forest(axes[row, 2], ci, "capture_at_20pct", models,
                "Interruptions captured in top 20%", ref=0.2)
    for ax in axes.ravel():
        ax.set_xlim(0, 1)
    fig.subplots_adjust(wspace=0.28, hspace=0.42)
    n = int(lock["n_clusters"].iloc[0])
    _save(fig, "fig6_model_comparison", "Baselines versus models, with country-clustered intervals",
          f"Points are estimates; bars are 95% percentile intervals from a bootstrap that "
          f"resamples whole countries ({n} countries in the locked test). Dashed lines mark "
          f"no discrimination (0.5) or chance capture (0.2). Top row is development only.",
          "Six forest plots comparing eight approaches on AUROC, within-country-year AUROC and "
          "capture at 20% capacity, for development folds and for the locked test. Intervals "
          "are wide and overlap heavily.",
          ["reports/evaluation/development/development_intervals.csv",
           "reports/evaluation/locked_test/locked_intervals.csv"])


def _locked_primary() -> pd.DataFrame:
    p = pd.read_parquet(paths.PROCESSED / "predictions_heldout.parquet")
    return p[(p["scenario"] == "P") & (p["window"] == "locked_test") & p["eligible_primary"]
             & p["y"].notna()].reset_index(drop=True)


def _direct_label(ax, x, y, text, color) -> None:
    ax.text(x, y, text, fontsize=7.5, color=INK2, va="center",
            bbox=dict(fc=SURFACE, ec="none", pad=0.6))
    ax.plot([x - 0.012], [y], "s", color=color, ms=5, clip_on=False)


def fig_roc_pr() -> None:
    d = _locked_primary()
    y = d["y"].to_numpy()
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.4))
    for m in KEY:
        s = d[f"r_{m}"].to_numpy()
        thr = np.r_[np.inf, np.sort(np.unique(s))[::-1]]
        tpr = np.array([((s >= t) & (y == 1)).sum() / y.sum() for t in thr])
        fpr = np.array([((s >= t) & (y == 0)).sum() / (1 - y).sum() for t in thr])
        with np.errstate(invalid="ignore"):
            prec = np.array([y[s >= t].mean() if (s >= t).any() else np.nan for t in thr])
        axes[0].plot(fpr, tpr, color=MODEL_COLOR[m], label=SHORT[m])
        axes[1].plot(tpr[1:], prec[1:], color=MODEL_COLOR[m], label=SHORT[m])
    axes[0].plot([0, 1], [0, 1], color=NEUTRAL, lw=1, ls=(0, (3, 3)))
    axes[1].axhline(y.mean(), color=NEUTRAL, lw=1, ls=(0, (3, 3)))
    axes[1].text(0.99, y.mean() + 0.02, f"prevalence {y.mean():.0%}", ha="right", fontsize=7.5,
                 color=INK2)
    axes[0].set(xlabel="False positive rate", ylabel="True positive rate",
                title="ROC, locked test 2023-2024", xlim=(0, 1), ylim=(0, 1.02))
    axes[1].set(xlabel="Recall (share of interruptions captured)", ylabel="Precision",
                title="Precision-recall", xlim=(0, 1), ylim=(0, 1.02))
    axes[0].legend(loc="lower right", fontsize=8)
    _save(fig, "fig7_roc_pr", "ROC and precision-recall curves on the locked test",
          f"Locked test 2023-2024, primary cohort: {len(d)} IU-years, {int(y.sum())} reported "
          f"interruptions (prevalence {y.mean():.1%}). Curves use each approach's ranking score.",
          "Two line charts. Left: ROC curves for four approaches against the diagonal. Right: "
          "precision-recall curves against the prevalence line.",
          ["data/processed/predictions_heldout.parquet"])


def fig_calibration() -> None:
    d = _locked_primary()
    fig, axes = plt.subplots(1, 4, figsize=(12.4, 3.5), sharey=True)
    for ax, m in zip(axes, KEY):
        p = d[f"p_{m}"].to_numpy()
        try:
            bins = pd.qcut(p, 5, duplicates="drop")
        except ValueError:
            bins = pd.Series(["all"] * len(p))
        g = d.assign(p=p, bin=np.asarray(bins)).groupby("bin", observed=True).agg(
            pred=("p", "mean"), obs=("y", "mean"), n=("y", "size"), ev=("y", "sum"))
        ax.plot([0, 1], [0, 1], color=NEUTRAL, lw=1, ls=(0, (3, 3)))
        ax.plot(g["pred"], g["obs"], "-o", color=MODEL_COLOR[m], ms=7, mec=SURFACE, mew=1.5)
        for _, r in g.iterrows():
            ax.text(r["pred"], r["obs"] + 0.06, f"{int(r['ev'])}/{int(r['n'])}", ha="center",
                    fontsize=7, color=INK2)
        ax.set(xlim=(0, 1), ylim=(0, 1.05), title=SHORT[m], xlabel="Mean predicted risk")
    axes[0].set_ylabel("Observed interruption share")
    _save(fig, "fig8_calibration", "Calibration on the locked test",
          "Predicted risk (after the pre-specified recalibration fitted on development folds) "
          "against observed share, in fifths of predicted risk. Labels are events / IU-years "
          "in each group. With events concentrated in a few country-years, calibration "
          "estimates are unstable.",
          "Four small panels, one per approach, each plotting observed interruption share "
          "against mean predicted risk with a diagonal reference line.",
          ["data/processed/predictions_heldout.parquet"])


def fig_capture_curve() -> None:
    d = _locked_primary()
    y = d["y"].to_numpy()
    fracs = np.linspace(0.02, 1, 50)
    fig, ax = plt.subplots(figsize=(6.6, 4.6))
    ax.plot([0, 1], [0, 1], color=NEUTRAL, lw=1, ls=(0, (3, 3)), label="Random selection")
    for m in KEY:
        s = d[f"r_{m}"].to_numpy()
        cap = [top_k_counts(y, s, f)[0] / y.sum() for f in fracs]
        ax.plot(np.r_[0, fracs], np.r_[0, cap], color=MODEL_COLOR[m], label=SHORT[m])
    for k in (0.1, 0.2):
        ax.axvline(k, color=GRID, lw=1)
        ax.text(k, 1.03, f"{k:.0%} capacity", ha="center", fontsize=7.5, color=INK2)
    ax.set(xlim=(0, 1), ylim=(0, 1.08), xlabel="Share of eligible IUs flagged for support",
           ylabel="Share of reported interruptions captured",
           title="Capture curve, locked test 2023-2024")
    ax.legend(loc="lower right", fontsize=8)
    _save(fig, "fig9_capture_curve", "Interruptions captured by support capacity",
          f"Share of the {int(y.sum())} locked-test interruptions found among the top-ranked "
          f"IUs, by the share of IUs flagged. Ties are handled by expected value.",
          "Line chart of captured interruptions against the share of IUs flagged, for four "
          "approaches and a diagonal for random selection.",
          ["data/processed/predictions_heldout.parquet"])


def fig_temporal_stability() -> None:
    dev = pd.read_csv(DEV / "development_metrics.csv")
    dev = dev[(dev["scenario"] == "P") & dev["subset"].str.startswith("year_")]
    dev = dev.assign(year=dev["subset"].str[5:].astype(int))
    lock = pd.read_csv(LOCK / "locked_metrics.csv")
    lock = lock[(lock["scenario"] == "P") & lock["subset"].isin(["year_2023", "year_2024",
                                                                 "stress_2025"])]
    lock = lock.assign(year=lock["subset"].str[-4:].astype(int))
    allm = pd.concat([dev, lock])
    fig, axes = plt.subplots(1, 3, figsize=(12.6, 3.9))
    specs = [("auroc", "AUROC", 0.5), ("within_country_year_auroc", "AUROC within country-year", 0.5),
             ("capture_at_20pct", "Captured in top 20%", 0.2)]
    for ax, (metric, title, ref) in zip(axes, specs):
        for m in KEY:
            s = allm[allm["model"] == m].sort_values("year")
            ax.plot(s["year"], s[metric], "-o", color=MODEL_COLOR[m], label=SHORT[m], ms=5)
        ax.axhline(ref, color=NEUTRAL, lw=1, ls=(0, (3, 3)))
        ax.axvspan(2019.5, 2021.5, color=GRID, alpha=0.5, lw=0)
        ax.axvspan(2024.5, 2025.5, color=GRID, alpha=0.5, lw=0)
        ax.axvline(2022.5, color=INK2, lw=1)
        ax.set(ylim=(0, 1.02), title=title, xlabel="Target year")
        ax.set_xticks(sorted(allm["year"].unique()))
    axes[0].text(2022.45, 0.04, "development ", ha="right", fontsize=7.5, color=INK2)
    axes[0].text(2022.55, 0.04, " held out", ha="left", fontsize=7.5, color=INK2)
    axes[2].legend(loc="lower left", fontsize=7.5)
    ev = allm[allm["model"] == "history_rule"].sort_values("year")
    counts = ", ".join(f"{int(r.year)}: {int(r.events)}/{int(r.n)}" for r in ev.itertuples())
    _save(fig, "fig10_temporal_stability", "Performance by target year",
          f"Yearly estimates (events / IU-years: {counts}). Years 2019-2022 are rolling-origin "
          f"development folds; 2023-2024 are the locked test; 2025 is the stress year. Shaded "
          f"bands are stress periods. Single-year estimates rest on few country-years and are "
          f"shown without intervals; they indicate variability, not trends.",
          "Three line charts of yearly AUROC, within-country-year AUROC and capture at 20% "
          "for four approaches from 2019 to 2025. Values swing widely between years.",
          ["reports/evaluation/development/development_metrics.csv",
           "reports/evaluation/locked_test/locked_metrics.csv"])


def fig_country_transport() -> None:
    f = LOCO / "transport_by_country.csv"
    if not f.exists():
        return
    t = pd.read_csv(f)
    t = t[t["supports_external_claim"] & t["model"].isin(KEY)]
    if t.empty:
        return
    order = (t[t["model"] == "history_rule"].sort_values("events")["country"]).tolist()
    fig, ax = plt.subplots(figsize=(7.6, 0.42 * len(order) + 1.8))
    y = np.arange(len(order))
    for i, m in enumerate(KEY):
        s = t[t["model"] == m].set_index("country").reindex(order)
        ax.plot(s["auroc"], y + (i - 1.5) * 0.17, "o", color=MODEL_COLOR[m], label=SHORT[m],
                ms=6, mec=SURFACE, mew=1)
    ev = t[t["model"] == "history_rule"].set_index("country").reindex(order)
    ax.set_yticks(y, [f"{c} ({int(e)}/{int(n)})" for c, e, n in
                      zip(order, ev["events"], ev["n"])], fontsize=8)
    ax.axvline(0.5, color=NEUTRAL, lw=1, ls=(0, (3, 3)))
    ax.set(xlim=(0, 1), xlabel="AUROC in the held-out country (events / IU-years)",
           title="Leave-one-country-out transport, development years")
    ax.grid(axis="y", visible=False)
    ax.legend(loc="lower left", fontsize=7.5, ncol=2, bbox_to_anchor=(0, -0.32))
    _save(fig, "fig11_country_transport", "Performance in countries excluded from training",
          f"Each country was held out in turn and predicted by models trained on all other "
          f"countries (development years 2016-2022, no country identity). Only the {len(order)} "
          f"countries with at least 10 events and 10 non-events are shown. This is transport "
          f"across countries within the same calendar years, not a future-year test.",
          "Dot plot of held-out-country AUROC for four approaches, one row per country. "
          "Results vary widely by country and several fall near or below 0.5.",
          ["reports/evaluation/country_transport/transport_by_country.csv"])


def fig_explain() -> None:
    fs, fc = EXPL / "shap_importance_catboost_history.csv", EXPL / "coefficients_logistic_history.csv"
    if not (fs.exists() and fc.exists()):
        return
    shap, coef = pd.read_csv(fs).head(12)[::-1], pd.read_csv(fc).head(12)[::-1]
    fig, axes = plt.subplots(1, 2, figsize=(11.4, 4.6))
    axes[0].barh(shap["feature"], shap["mean_abs_shap_log_odds"], color="#1baf7a", height=0.62)
    axes[0].set(title="CatBoost: mean |SHAP| (log-odds)", xlabel="Mean absolute contribution")
    colors = ["#eb6834" if v > 0 else "#2a78d6" for v in coef["standardised_log_odds"]]
    axes[1].barh(coef["term"].str.replace(r"^(num|cat)__", "", regex=True),
                 coef["standardised_log_odds"], color=colors, height=0.62)
    axes[1].axvline(0, color=INK2, lw=1)
    axes[1].set(title="Logistic: standardised coefficients",
                xlabel="Log-odds per SD (orange = higher risk, blue = lower)")
    for ax in axes:
        ax.grid(axis="y", visible=False)
        ax.tick_params(axis="y", labelsize=7.5, length=0)
    fig.subplots_adjust(wspace=0.55)
    _save(fig, "fig12_explainability", "What the fitted models rely on",
          "Left: mean absolute SHAP contribution per predictor for the CatBoost programme-history "
          "model on its training data. Right: the twelve largest standardised coefficients of the "
          "logistic programme-history model. These describe model associations only; they are "
          "not causal effects and must not be read as programme risk factors.",
          "Two horizontal bar charts ranking predictors by importance in the CatBoost model and "
          "by coefficient size in the logistic model.",
          ["reports/evaluation/explain/shap_importance_catboost_history.csv",
           "reports/evaluation/explain/coefficients_logistic_history.csv"])


# ------------------------------------------------------------------ tables
def tables() -> None:
    win = pd.read_csv(paths.AUDIT / "events_by_window.csv")
    t1 = win.copy()
    t1["prevalence"] = (t1["prevalence"] * 100).round(1)
    _table(t1, "table1_cohort_by_window", "Cohort size, events and clustering by window",
           "IU-years, reported interruptions and the number of countries and country-years "
           "contributing events, for the primary and sensitivity cohorts.",
           ["reports/audit/events_by_window.csv"])
    c = pd.read_csv(paths.AUDIT / "primary_cohort_by_country.csv")
    c["share_of_all_events"] = (c["share_of_all_events"] * 100).round(1)
    _table(c.drop(columns="iso2"), "table2_population_by_country",
           "Study population and events by country",
           "Primary analysis set by country: IU-years, events, distinct IUs, years covered.",
           ["reports/audit/primary_cohort_by_country.csv"])

    ci = pd.read_csv(LOCK / "locked_intervals.csv")
    met = pd.read_csv(LOCK / "locked_metrics.csv")
    rows = []
    for scen in ("P", "E"):
        for subset in ("locked_test_2023_2024", "stress_2025"):
            c1 = ci[(ci["scenario"] == scen) & (ci["subset"] == subset)]
            m1 = met[(met["scenario"] == scen) & (met["subset"] == subset)]
            for m in [x for x in SHORT if x in set(c1["model"])]:
                g = c1[c1["model"] == m].set_index("metric")
                mm = m1[m1["model"] == m].iloc[0]

                def f(k, d=2):
                    return _fmt_ci(g.loc[k, "estimate"], g.loc[k, "ci_low"], g.loc[k, "ci_high"], d)
                rows.append({
                    "scenario": scen, "evaluation": subset, "approach": SHORT[m],
                    "n": int(mm["n"]), "events": int(mm["events"]),
                    "AUROC (95% CI)": f("auroc"),
                    "AUROC within country-year (95% CI)": f("within_country_year_auroc"),
                    "PR-AUC (95% CI)": f("pr_auc"),
                    "Captured in top 10% (95% CI)": f("capture_at_10pct"),
                    "Captured in top 20% (95% CI)": f("capture_at_20pct"),
                    "Precision in top 20%": f"{mm['precision_at_20pct']:.2f}",
                    "Brier (95% CI)": f("brier", 3),
                    "Calibration intercept": f"{mm['calibration_intercept']:.2f}",
                    "Calibration slope": ("not estimable" if pd.isna(mm["calibration_slope"])
                                          else f"{mm['calibration_slope']:.2f}"),
                    "Observed/expected": f"{mm['observed_expected_ratio']:.2f}",
                })
    _table(pd.DataFrame(rows), "table3_performance",
           "Discrimination, calibration and capture on held-out years",
           "Point estimates with 95% percentile intervals from a country-cluster bootstrap "
           "(2,000 resamples). Scenario P uses information to t-1; scenario E to t-2. The "
           "locked test is the primary evaluation; 2025 is a robustness check only.",
           ["reports/evaluation/locked_test/locked_intervals.csv",
            "reports/evaluation/locked_test/locked_metrics.csv"])

    d = pd.read_csv(LOCK / "locked_differences_vs_rule.csv")
    d = d[d["metric"].isin(["auroc", "within_country_year_auroc", "capture_at_10pct",
                            "capture_at_20pct", "brier"])].copy()
    d["approach"] = d["model"].map(SHORT)
    d["difference vs history rule (95% CI)"] = [
        _fmt_ci(a, b, c_, 3) for a, b, c_ in zip(d["difference"], d["ci_low"], d["ci_high"])]
    _table(d[["scenario", "subset", "approach", "metric", "difference vs history rule (95% CI)",
              "interval_excludes_zero"]], "table3b_differences_vs_rule",
           "Paired differences against the history rule",
           "Each approach minus the fixed history rule on the same IU-years, with country-cluster "
           "bootstrap intervals. A gain is claimed only where the interval excludes zero.",
           ["reports/evaluation/locked_test/locked_differences_vs_rule.csv"])

    s = pd.read_csv(SENS / "sensitivity_metrics.csv")
    s = s[s["model"].isin(KEY)].copy()
    s["approach"] = s["model"].map(SHORT)
    keep = ["analysis", "approach", "countries", "n", "events", "auroc",
            "within_country_year_auroc", "capture_at_20pct", "brier"]
    t4 = s[keep].copy()
    for col in keep[5:]:
        t4[col] = t4[col].round(3)
    for col in ("countries", "n", "events"):
        t4[col] = t4[col].astype("Int64")
    _table(t4, "table4_sensitivity", "Sensitivity analyses",
           "Scenario P point estimates under alternative cohorts, label assumptions and data "
           "restrictions. No intervals are shown; these analyses test direction and stability.",
           ["reports/evaluation/sensitivity/sensitivity_metrics.csv"])

    devm = pd.read_csv(DEV / "development_intervals.csv")
    devm = devm[devm["metric"].isin(["auroc", "within_country_year_auroc", "capture_at_20pct",
                                     "brier", "log_loss"])].copy()
    devm["approach"] = devm["model"].map(SHORT)
    devm["estimate (95% CI)"] = [_fmt_ci(a, b, c_, 3) for a, b, c_ in
                                 zip(devm["estimate"], devm["ci_low"], devm["ci_high"])]
    _table(devm[["scenario", "subset", "approach", "metric", "estimate (95% CI)"]],
           "tableS1_development_performance", "Development (rolling-origin) performance",
           "Out-of-fold performance on development target years 2019-2022; used for model "
           "selection. Country-cluster bootstrap, 500 resamples.",
           ["reports/evaluation/development/development_intervals.csv"])
    if (LOCO / "transport_pooled_intervals.csv").exists():
        lo = pd.read_csv(LOCO / "transport_pooled_intervals.csv")
        lo = lo[lo["metric"].isin(["auroc", "within_country_year_auroc", "capture_at_20pct",
                                   "brier"])].copy()
        lo["approach"] = lo["model"].map(SHORT)
        lo["estimate (95% CI)"] = [_fmt_ci(a, b, c_, 3) for a, b, c_ in
                                   zip(lo["estimate"], lo["ci_low"], lo["ci_high"])]
        _table(lo[["approach", "metric", "estimate (95% CI)"]], "tableS2_country_transport",
               "Leave-one-country-out transport (pooled)",
               "Predictions for each country from models trained on all other countries, "
               "development years, pooled across held-out countries.",
               ["reports/evaluation/country_transport/transport_pooled_intervals.csv"])


def write_captions() -> None:
    out = paths.ROOT / "manuscript" / "figures_and_tables.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Figures and tables", "",
             "Generated by `python -m lf_mda.cli report`. Do not edit by hand: captions carry "
             "numbers read from the result files listed under each item.", ""]
    for kind, head in (("figure", "## Figures"), ("table", "## Tables")):
        lines += [head, ""]
        for c in [c for c in CAPTIONS if c["kind"] == kind]:
            ext = "png" if kind == "figure" else "csv"
            folder = "figures" if kind == "figure" else "tables"
            lines += [f"### {c['id']}: {c['title']}", "",
                      f"File: `reports/{folder}/{c['id']}.{ext}`", "", c["caption"], ""]
            if c["alt"]:
                lines += [f"Alt text: {c['alt']}", ""]
            lines += ["Derived from: " + ", ".join(f"`{s}`" for s in c["sources"]), ""]
    out.write_text("\n".join(lines), encoding="utf-8")


def results_summary() -> str:
    """Plain-language results block with every number read from result files."""
    g = _gate()
    m = g["metrics"]
    lines = [
        f"*Generated by `lf-mda report` from the result files; gate decision "
        f"`{g['gate']['decision']}`, independent information "
        f"`{g['gate']['information_adequacy']}`, expert label review pending.*", "",
        f"- **Data:** {m['n_raw_rows']:,} IU-year records, {m['n_countries']} country files, "
        f"{m['n_ius']:,} implementation units, 2014-2025.",
        f"- **Primary cohort:** {m['primary_n']:,} IU-years with {m['primary_events']:,} reported "
        f"interruptions in {m['primary_countries']} countries "
        f"({m['primary_event_countries']} with at least one event).",
        f"- **Clustering:** {m['events_in_whole_country_failures'] / m['primary_events']:.0%} of "
        f"interruptions occurred in country-years where every eligible IU missed the round; "
        f"{1 - m['within_country_year_variance_share']:.0%} of outcome variance lies between "
        f"country-years.",
        f"- **Locked test (2023-2024):** {m['test_n']} IU-years, {m['test_events']} "
        f"interruptions from {m['test_event_countries']} countries and "
        f"{m['test_event_country_years']} country-years.", ""]
    if not (LOCK / "locked_intervals.csv").exists():
        lines.append("No model has been evaluated.")
        return NL.join(lines)
    ci = pd.read_csv(LOCK / "locked_intervals.csv")
    diffs = pd.read_csv(LOCK / "locked_differences_vs_rule.csv")

    def block(scen: str, subset: str) -> pd.DataFrame:
        c = ci[(ci["scenario"] == scen) & (ci["subset"] == subset)]
        rows = []
        for mod in [x for x in SHORT if x in set(c["model"]) and x != "prevalence"]:
            gk = c[c["model"] == mod].set_index("metric")
            rows.append({"Approach": SHORT[mod]} | {
                lab: _fmt_ci(gk.loc[k, "estimate"], gk.loc[k, "ci_low"], gk.loc[k, "ci_high"])
                for k, lab in (("auroc", "AUROC"),
                               ("within_country_year_auroc", "AUROC within country-year"),
                               ("capture_at_20pct", "Captured in top 20%"))})
        return pd.DataFrame(rows)

    lines += ["**Locked test 2023-2024, scenario P (95% country-cluster bootstrap intervals):**",
              "", _md(block("P", "locked_test_2023_2024")).rstrip(), ""]
    d = diffs[(diffs["scenario"] == "P") & (diffs["subset"] == "locked_test_2023_2024")
              & (diffs["metric"] == "capture_at_20pct")]
    lock = json.loads((LOCK / "LOCK.json").read_text("utf-8"))
    primary = lock["primary_candidate"]
    d = d[~d["model"].isin(["prevalence", "country_prior_rate"])]
    pr = d[d["model"] == primary].iloc[0]
    passed = bool(pr["difference"] >= 0.05 and pr["ci_low"] > 0)
    lines.append(
        f"**Pre-specified test of improvement over the history rule: "
        f"{'met' if passed else 'not met'}.** The primary candidate, chosen on development "
        f"folds by pooled log loss, was {SHORT[primary]}. Its share of interruptions captured "
        f"at 20% capacity differed from the history rule by "
        f"{_fmt_ci(pr['difference'], pr['ci_low'], pr['ci_high'], 3)}. The criterion was a "
        f"gain of at least 0.05 with a 95% interval above zero.")
    others = d[d["model"] != primary]
    clear = others[(others["difference"] >= 0.05) & (others["ci_low"] > 0)]
    if clear.empty:
        lines.append(
            f"None of the other {len(others)} approaches cleared that criterion either "
            f"(exploratory, no adjustment for multiple comparisons).")
    else:
        names = "; ".join(f"{SHORT[r.model]} {_fmt_ci(r.difference, r.ci_low, r.ci_high, 3)}"
                          for r in clear.itertuples())
        lines.append(
            f"Among the other {len(others)} approaches, {len(clear)} cleared the same "
            f"criterion: {names}. These comparisons are exploratory: they were not the "
            f"pre-specified primary candidate and are not adjusted for multiple comparisons.")
    lines += ["", "**Scenario E (public data only, two-year lag), same IU-years:**", "",
              _md(block("E", "locked_test_2023_2024")).rstrip(), "",
              "**2025 stress year, scenario P (robustness only, not part of the primary "
              "test):**", "", _md(block("P", "stress_2025")).rstrip(), ""]
    f = LOCO / "transport_pooled_intervals.csv"
    if f.exists():
        lo = pd.read_csv(f)
        rows = []
        for mod in [x for x in SHORT if x in set(lo["model"])]:
            gk = lo[lo["model"] == mod].set_index("metric")
            rows.append({"Approach": SHORT[mod]} | {
                lab: _fmt_ci(gk.loc[k, "estimate"], gk.loc[k, "ci_low"], gk.loc[k, "ci_high"])
                for k, lab in (("auroc", "AUROC"),
                               ("within_country_year_auroc", "AUROC within country-year"),
                               ("capture_at_20pct", "Captured in top 20%"))})
        tr = pd.read_csv(LOCO / "transport_by_country.csv")
        n_sup = tr.loc[tr["supports_external_claim"], "iso2"].nunique()
        lines += ["**Countries excluded from training (leave-one-country-out, development "
                  f"years 2016-2022; {n_sup} of {tr['iso2'].nunique()} countries have enough "
                  "events and non-events for a country-specific estimate):**", "",
                  _md(pd.DataFrame(rows)).rstrip(), ""]
    return NL.join(lines)


def write_results_summary() -> None:
    text = results_summary()
    (paths.REPORTS / "RESULTS_SUMMARY.md").write_text(
        NL.join(["# Results summary", "", text, ""]), encoding="utf-8")
    readme = paths.ROOT / "README.md"
    start, end = "<!-- RESULTS:START -->", "<!-- RESULTS:END -->"
    if readme.exists():
        body = readme.read_text(encoding="utf-8")
        if start in body and end in body:
            head, rest = body.split(start, 1)
            _, tail = rest.split(end, 1)
            readme.write_text(NL.join([head + start, text, end + tail]), encoding="utf-8")


def render_all() -> None:
    _style()
    CAPTIONS.clear()
    fig_decision_schematic()
    fig_cohort_flow()
    fig_outcomes_by_year()
    fig_country_year_heatmap()
    fig_country_contribution()
    have_models = (LOCK / "locked_intervals.csv").exists()
    if have_models:
        fig_model_comparison()
        fig_roc_pr()
        fig_calibration()
        fig_capture_curve()
        fig_temporal_stability()
        fig_country_transport()
        fig_explain()
        tables()
    write_captions()
    write_results_summary()
    print(f"rendered {sum(c['kind'] == 'figure' for c in CAPTIONS)} figures and "
          f"{sum(c['kind'] == 'table' for c in CAPTIONS)} tables")


if __name__ == "__main__":
    render_all()
