#!/usr/bin/env python3
"""
Avia Solutions - turn a monthly passenger pull into a seasonality profile.
==========================================================================
The annual ODPOO store has no month column, so real seasonality needs a MONTHLY Sabre pull
(passengers by month for the Genoa catchment -> New York). Feed the 12 monthly totals in here
and it prints the normalised --profile string for seasonality_check.py (mean month = 1.0).

RUN (Jan..Dec passenger totals, any units, comma-separated):
    py -3.12 seasonality_from_monthly.py 3100,2900,3600,4300,5500,6700,8000,8000,6200,5000,3700,5600

Then:
    py -3.12 seasonality_check.py genoa_nyc --profile <printed string>
"""
import sys

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def main():
    if len(sys.argv) < 2:
        sys.exit("Pass 12 monthly passenger totals, comma-separated (Jan first). See the header.")
    vals = [float(x) for x in sys.argv[1].replace(" ", "").split(",")]
    if len(vals) != 12:
        sys.exit(f"Need 12 values (got {len(vals)}).")
    mean = sum(vals) / 12.0
    if mean <= 0:
        sys.exit("All-zero input.")
    idx = [v / mean for v in vals]                      # normalised so the mean month = 1.0
    print("monthly demand index (mean = 1.0):")
    for m in range(12):
        print(f"  {MONTHS[m]}  {idx[m]:.2f}   ({vals[m]:,.0f})")
    print(f"\nAug/Feb ratio {idx[7]/idx[1]:.1f}; peak {max(idx):.2f} ({MONTHS[idx.index(max(idx))]}), "
          f"trough {min(idx):.2f} ({MONTHS[idx.index(min(idx))]})")
    print("\n--profile " + ",".join(f"{x:.3f}" for x in idx))


if __name__ == "__main__":
    main()
