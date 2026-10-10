# HTF Asymmetry Atlas

A reproducible, descriptive study of **higher-timeframe (HTF) candle asymmetry**: how often quarterly, semiannual and yearly candles close up versus down, and how large the up-moves are compared with the down-moves.

Feed it daily OHLC data for any asset. It builds calendar candles, computes the statistics, and writes charts and CSV tables you can drop straight into a report.

The first worked example is **XAUUSD (gold), 2001–2025**.

> This is descriptive statistics, not a trading strategy, a backtest, or a forecast.

---

## What it measures

For each timeframe (Quarterly, Semiannual, Yearly):

| Area | Metrics |
|---|---|
| Direction | candle count, bullish / bearish counts and %, bull/bear ratio |
| Return baseline | mean, median, standard deviation, min, max of candle return |
| Asymmetry | mean and median of up-candles vs down-candles, up/down magnitude ratio, upside share of absolute returns, sum of positive vs negative returns |
| Candle risk | high–low range as % of open, mean candle body, longest bullish and bearish streaks |
| Uncertainty | 95% Wilson interval, year-block bootstrap (3,000 resamples, seed 42) |
| Persistence | next-candle direction conditional on the previous candle |
| Regimes | per-calendar-year breakdown |

## Quick start

```bash
git clone https://github.com/<your-username>/htf-asymmetry-atlas.git
cd htf-asymmetry-atlas
pip install -r requirements.txt
python generate_report.py --csv input/xauusd_daily.csv --start 2001-01-01 --end 2025-12-31 --out output
```

Requirements: Python 3.10+, `numpy`, `pandas`, `matplotlib`.

### Arguments

| Flag | Default | Description |
|---|---|---|
| `--csv` | required | Path to the daily OHLC CSV |
| `--start` | `2001-01-01` | First date included |
| `--end` | `2025-12-31` | Last date included |
| `--out` | `output` | Output folder (created if missing) |

### Using your own asset

1. Prepare a CSV with these headers (ascending or descending order both work):

   ```
   Date,Open,High,Low,Close
   2001-01-02,273.15,273.55,267.95,269.05
   ```

   Dates must be `YYYY-MM-DD`.
2. Run the script with `--csv`, `--start`, `--end` and a separate `--out` folder per asset.

> **Known limitation:** chart titles and axis labels in the current script still say "XAUUSD" and "USD/oz". Change those strings in `generate_report.py` when you run another asset.

## Method

- **Calendar aggregation.** Quarters are Jan–Mar, Apr–Jun, Jul–Sep, Oct–Dec. Semiannual is Jan–Jun and Jul–Dec. Yearly is Jan–Dec.
- **Candle return** = `(period Close / period Open − 1) × 100`. It is a candle-body measure, not a holding return across gaps.
- **High / Low** are the max and min of the daily data inside the period.
- **Completeness rule.** Only complete calendar periods inside `--start` / `--end` are used. This does not check for missing daily rows.
- **Overlapping scales.** Quarterly, semiannual and yearly observations come from the same price path, so they are not independent samples.
- **Bootstrap.** Whole calendar years are resampled to preserve within-year dependence.

## Output files

Everything is written to `--out`.

**Report pages (PNG)**

| File | Content |
|---|---|
| `01_direction_and_baseline.png` | counts, bullish frequency, mean/median returns |
| `02_upside_downside_magnitude.png` | conditional up/down magnitude and contribution |
| `03_range_and_streaks.png` | intraperiod range and directional streaks |
| `04_uncertainty.png` | Wilson and year-block bootstrap intervals |
| `05_direction_transitions.png` | directional persistence |
| `06_historical_return_heatmap.png` | period-by-period return heatmap |
| `07_year_by_year_regimes.png` | changes across calendar years |
| `08_executive_conclusion.png` | narrative classification and limitations |
| `htf_asymmetry_dashboard.png` | 4-panel overview |
| `quarterly_candles.png`, `semiannual_candles.png`, `yearly_candles.png`, `all_three_htf_candles.png` | HTF candlestick charts |

**Tables (CSV)**

| File | Content |
|---|---|
| `htf_full_statistics.csv` | all summary statistics per timeframe |
| `htf_all_candles.csv` | every HTF candle with return, range, wicks |
| `htf_transitions.csv` | transition counts and mean next return |
| `htf_by_year.csv` | per-year breakdown |
| `htf_year_block_bootstrap.csv` | bootstrap confidence intervals |

To share a report, zip the `output/` folder only.

## Example result: XAUUSD 2001–2025

| | Quarterly | Semiannual | Yearly |
|---|---:|---:|---:|
| Candles | 100 | 50 | 25 |
| Bullish | 68 (68.0%) | 37 (74.0%) | 19 (76.0%) |
| Mean candle return | +3.00% | +6.17% | +12.89% |
| Mean up-candle | +6.78% | +10.71% | +19.39% |
| Mean down-candle | −5.01% | −6.75% | −7.70% |
| Up/down magnitude ratio | 1.35× | 1.59× | 2.52× |
| Longest bullish / bearish run | 12 / 6 | 8 / 3 | 12 / 3 |

Gold's upward drift over this period shows up on all three timeframes. The longer the candle, the more the bullish share and the up/down magnitude ratio widen. Yearly has only 25 observations, so its intervals are wide (Wilson 95% for bullish share: 56.6%–88.5%). A 25-year gold sample reflects one historical regime and says nothing certain about the future.

## Data notes

- `input/xauusd_daily.csv` (6,433 daily rows, 2001-01-02 to 2025-12-31) is included for reproducibility.
- Validate the provenance of your data and check it for missing dates before formal publication.
- Check redistribution rights of the data source before making a repo public.

## Limitations

- Descriptive only: no transaction costs, no execution model, no out-of-sample test.
- Small samples at the yearly level.
- Serial dependence between consecutive candles makes the Wilson interval optimistic. Use the bootstrap as a sensitivity check.
- Results depend on calendar boundaries and the data vendor's daily close (session and timezone conventions).

## Repository layout

```
htf-asymmetry-atlas/
├── generate_report.py     # main script
├── requirements.txt
├── input/
│   └── xauusd_daily.csv   # example data
└── output/                # generated charts and CSVs
```

## License

Add a `LICENSE` file before publishing. MIT for code and CC BY 4.0 for reports is a common split.

## Author

Alif Arya Wiranda (Alifio), Ilmugunung Academia.
