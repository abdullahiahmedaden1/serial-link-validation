# Validation Report — Serial Link Simulation

## Objective

Evaluate a simplified NRZ binary serial link using reproducible Python simulations. The work focuses on measured BER, receiver sampling margin, bandwidth limitations, and automatically applying project-defined performance limits.

## Model and test method

The transmitter maps binary bits to normalized levels −1 and +1. The receiver detects a bit from the sign of its sample relative to a zero threshold. For noise-only tests, independent Gaussian noise is added and the detected BER is compared with the analytical prediction `0.5 * erfc(1 / (sqrt(2) * noise_std))` for this model. `snr_sweep.py` uses the model-specific relation `noise_std = 10**(-snr_db/20)`.

For channel tests, a first-order discrete-time low-pass filter models bandwidth limitations. The eye analyzer estimates vertical eye opening as the fifth percentile of received-one samples minus the ninety-fifth percentile of received-zero samples at each tested phase. The reported timing window is the fraction of the sampled phases (one per sample within the bit period) that have a positive eye height. It is a coarse grid-based estimate: it does not require those phases to be contiguous and is not a calibrated timing margin measurement.

## Regression configuration

The provided report `outputs/regression_report.json` records:

- Generated bits: 20,000 per cutoff; 19,990 analyzed after 10 settling bits.
- Noise standard deviation: 0.12 in normalized signal amplitude units.
- Samples per bit: 16; seed: 42.
- Cutoffs: 0.10, 0.20, 0.40, 0.80 cycles per bit.
- PASS requires all three checks: center BER ≤ 0.01, center eye height ≥ 0.40, and phase window ≥ 0.25 UI.

## Observed results

| Cutoff (cycles/bit) | Error count | BER | Eye height | Timing window (UI) | Decision |
|---:|---:|---:|---:|---:|:---:|
| 0.10 | 5,471 | 0.273687 | -0.684 | 0.0000 | FAIL |
| 0.20 | 1,762 | 0.088144 | -0.104 | 0.4375 | FAIL |
| 0.40 | 0 | 0.000000 | 0.756 | 0.6875 | PASS |
| 0.80 | 0 | 0.000000 | 1.442 | 0.8750 | PASS |

The two lowest-bandwidth configurations failed the BER and eye-height requirements. The two higher-bandwidth cases passed all project-defined checks in this run. An observed BER of zero indicates no errors in the finite test, **not** that error probability is zero.

## Verification and reproducibility

The code includes tests under `tests/`. Run `python -m pytest -q` and regenerate the regression report with `python regression_validation.py`. The README lists the exact commands and bit counts used for every file in `outputs/`. The fixed default random seed makes runs repeatable with the same environment and code. Review the generated JSON and CSV outputs when changing thresholds or test settings.

## Engineering interpretation

Reducing available bandwidth distorts transitions and increases ISI, which reduces eye opening and can raise BER. A system-level validation workflow benefits from combining graphical evidence (eye diagrams and BER curves) with quantitative results and consistent pass/fail rules.

## Important scope limitations

This is a behavioral, educational simulation. It does not model physical silicon, measured analog front ends, link training, equalization, clock-data recovery, jitter, real channel S-parameters, or official protocol compliance. The numerical limits in the regression check are project-specific; passing them is **not** a claim of standards compliance. Results may differ with alternate seeds, sample counts, models, or dependencies.
