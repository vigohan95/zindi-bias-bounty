"""One command for everything in WRITEUP §7 (Best Bias Discovery).

    PYTHONUTF8=1 python reproduce_section7.py            # tables + offline spot-check + figure (needs the challenge data)
    PYTHONUTF8=1 python reproduce_section7.py --offline  # only the TxDOT spot-check table from our results CSV (no data, no network)
    PYTHONUTF8=1 python reproduce_section7.py --online   # also re-query the TxDOT service (>= 0.5 s between requests)

Steps, in order:
  1. bias_discovery.py          -> bias_discovery_out.md (every number in §7.2, §7.3 and the import-era stratum); ~5 min
  2. spotcheck_txdot.py --offline -> rebuilds spotcheck/spotcheck_txdot_summary.md from spotcheck/spotcheck_txdot_results.csv
     (raw TxDOT responses are not redistributed; `python spotcheck_txdot.py` re-queries the service online)
  3. figure_unnamed_roads.py    -> figures/fig_unnamed_roads.png
Data folder: ./data next to the scripts, or ZINDI_WORK. Each step is an ordinary script; run them separately if preferred.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def run(script: str, *args: str) -> None:
    cmd = [sys.executable, str(HERE / script), *args]
    print("\n$", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True, cwd=HERE)


def main() -> None:
    if "--offline" in sys.argv:
        run("spotcheck_txdot.py", "--offline")
        return
    run("bias_discovery.py", "--out", str(HERE / "bias_discovery_out.md"))
    run("spotcheck_txdot.py", *([] if "--online" in sys.argv else ["--offline"]))
    run("figure_unnamed_roads.py")
    print("\nSection 7 reproduced: bias_discovery_out.md, spotcheck/spotcheck_txdot_summary.md, figures/fig_unnamed_roads.png")


if __name__ == "__main__":
    main()
