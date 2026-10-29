"""Milestone 3: validate measured BER against theory across SNR values.

SNR here means average symbol power / noise variance, with +/-1 symbols.
It is not Eb/N0 for a bandwidth-defined physical link.
"""
from __future__ import annotations

import argparse
import csv
from math import erfc, sqrt
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from serial_link import simulate

DEFAULT_SNR_DB = [-3, 0, 3, 6, 9, 12]


def snr_to_noise_std(snr_db: float) -> float:
    """Unit-amplitude symbols: SNR_dB = -20 * log10(noise_std)."""
    return 10 ** (-snr_db / 20)


def expected_ber(noise_std: float) -> float:
    """Antipodal +/-1 signaling with ideal timing and independent Gaussian noise."""
    return 0.5 * erfc(1 / (sqrt(2) * noise_std))


def run_sweep(snr_values: list[float], n_bits: int = 100_000, seed: int = 42) -> list[dict]:
    if n_bits <= 0:
        raise ValueError("n_bits must be positive")
    rows = []
    for snr_db in snr_values:
        noise_std = snr_to_noise_std(snr_db)
        result = simulate(n_bits=n_bits, noise_std=noise_std,
                          samples_per_bit=1, seed=seed)
        rows.append({
            "snr_db": snr_db,
            "noise_std": noise_std,
            "bits": n_bits,
            "errors": result["bit_errors"],
            "measured_ber": result["ber"],
            "theoretical_ber": expected_ber(noise_std),
        })
    return rows


def save_results(rows: list[dict], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "snr_sweep.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.semilogy([r["snr_db"] for r in rows],
                [r["theoretical_ber"] for r in rows], "-", label="Theoretical BER")
    observed = [r for r in rows if r["errors"] > 0]
    ax.semilogy([r["snr_db"] for r in observed],
                [r["measured_ber"] for r in observed], "o", label="Measured BER")
    ax.set_xlabel("Signal-to-noise ratio (dB)")
    ax.set_ylabel("Bit error rate (BER)")
    ax.set_title("NRZ Link Validation: BER vs SNR")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "ber_vs_snr.png", dpi=150)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bits", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--snr-db", type=float, nargs="+", default=DEFAULT_SNR_DB)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    args = parser.parse_args()
    if not args.snr_db:
        parser.error("At least one SNR value is required")
    rows = run_sweep(args.snr_db, n_bits=args.bits, seed=args.seed)
    save_results(rows, args.output_dir)
    print(f"{'SNR(dB)':>8} {'Noise std':>11} {'Errors':>9} {'Measured BER':>15} {'Theory BER':>15}")
    for row in rows:
        print(f"{row['snr_db']:8.1f} {row['noise_std']:11.5f} {row['errors']:9,d} "
              f"{row['measured_ber']:15.8f} {row['theoretical_ber']:15.8f}")
    print(f"\nSaved {args.output_dir / 'snr_sweep.csv'} and {args.output_dir / 'ber_vs_snr.png'}")
    print("Zero observed errors does not prove zero true BER.")


if __name__ == "__main__":
    main()
