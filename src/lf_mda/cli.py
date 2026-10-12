"""Command-line entry point: `python -m lf_mda.cli <step>` or `lf-mda <step>`."""
from __future__ import annotations

import argparse
import json
import sys


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(
        prog="lf-mda", description="LF MDA interruption feasibility audit and prediction")
    sub = ap.add_subparsers(dest="step", required=True)
    d = sub.add_parser("download", help="download ESPEN LF IU-level extracts (all countries)")
    d.add_argument("--countries", nargs="*")
    d.add_argument("--force", action="store_true")
    sub.add_parser("audit", help="profile raw data, build the panel, run the label gate")
    c = sub.add_parser("context", help="fetch and build IU geometry and conflict tables")
    c.add_argument("--no-download", action="store_true")
    dv = sub.add_parser("develop", help="rolling-origin tuning and comparison (development years)")
    dv.add_argument("--n-boot", type=int, default=500)
    lk = sub.add_parser("lock", help="fit selected models once and score the held-out years")
    lk.add_argument("--n-boot", type=int, default=2000)
    lk.add_argument("--amend", default=None, help="reason for a documented protocol amendment")
    lo = sub.add_parser("loco", help="leave-one-country-out transport (development years)")
    lo.add_argument("--n-boot", type=int, default=1000)
    sub.add_parser("sensitivity", help="sensitivity analyses from saved predictions")
    sub.add_parser("explain", help="coefficients and SHAP importance")
    sub.add_parser("describe", help="descriptive burden, level and recovery analyses")
    ex = sub.add_parser("exploratory", help="EXPLORATORY post hoc models (not confirmatory)")
    ex.add_argument("--n-boot", type=int, default=1000)
    sub.add_parser("manuscript", help="fill the manuscript template from result files")
    sub.add_parser("report", help="render paper tables and figures from saved results")
    sub.add_parser("dashboard-data", help="build the compact dataset the dashboard reads")
    sub.add_parser("all", help="audit -> develop -> lock -> loco -> sensitivity -> explain -> "
                               "report -> dashboard-data (stops if the gate is not GO)")
    args = ap.parse_args(argv)

    if args.step == "download":
        from .ingest import download_all
        print(download_all(countries=args.countries, force=args.force)["status"]
              .value_counts().to_string())
    elif args.step == "audit":
        from .audit import run_audit
        print(json.dumps(run_audit()["gate"], indent=2))
    elif args.step == "context":
        from . import spatial
        if not args.no_download:
            spatial.download_geometry()
            spatial.download_ucdp()
        print(json.dumps(spatial.build_context(), indent=2))
    elif args.step == "develop":
        _require_gate()
        from .pipeline import run_development
        print(json.dumps(run_development(args.n_boot), indent=2))
    elif args.step == "lock":
        _require_gate()
        from .pipeline import run_locked_test
        res = run_locked_test(args.n_boot, args.amend)
        print(res["metrics"].to_string(index=False))
    elif args.step == "loco":
        _require_gate()
        from .pipeline import run_loco
        print(run_loco(args.n_boot).to_string(index=False))
    elif args.step == "sensitivity":
        from .pipeline import run_sensitivity
        print(run_sensitivity().to_string(index=False))
    elif args.step == "explain":
        from .pipeline import run_explain
        run_explain()
    elif args.step == "describe":
        from .describe import run_descriptive
        print(json.dumps(run_descriptive(), indent=2))
    elif args.step == "exploratory":
        from .exploratory import run_exploratory
        print(run_exploratory(args.n_boot).to_string(index=False))
    elif args.step == "manuscript":
        from .manuscript import render_manuscript
        print(render_manuscript())
    elif args.step == "report":
        from .render_paper import render_all
        render_all()
    elif args.step == "dashboard-data":
        from .dashboard_data import build_dashboard_data
        print(json.dumps(build_dashboard_data(), indent=2))
    elif args.step == "all":
        from .audit import run_audit
        gate = run_audit()["gate"]
        print(json.dumps(gate, indent=2))
        if not gate["decision"].startswith("GO"):
            print("Gate is not GO: stopping before any model is fitted.", file=sys.stderr)
            sys.exit(2)
        from .dashboard_data import build_dashboard_data
        from .describe import run_descriptive
        from .exploratory import run_exploratory
        from .manuscript import render_manuscript
        from .pipeline import (
            run_development,
            run_explain,
            run_locked_test,
            run_loco,
            run_sensitivity,
        )
        from .render_paper import render_all
        run_descriptive()
        run_development()
        run_locked_test()
        run_loco()
        run_sensitivity()
        run_explain()
        run_exploratory()
        render_all()
        render_manuscript()
        build_dashboard_data()


def _require_gate() -> None:
    """Refuse to fit models unless the audit has produced a GO decision."""
    from . import paths
    gate_file = paths.AUDIT / "gate_decision.json"
    if not gate_file.exists():
        sys.exit("No gate decision found. Run `lf-mda audit` first.")
    decision = json.loads(gate_file.read_text("utf-8"))["gate"]["decision"]
    if not decision.startswith("GO"):
        sys.exit(f"Label gate decision is {decision}: modelling is not permitted.")


if __name__ == "__main__":
    main()
