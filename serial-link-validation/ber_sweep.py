"""Milestone 2: characterize BER against Gaussian noise for the NRZ link."""
from __future__ import annotations

import argparse
import csv
from math import erfc, sqrt
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from serial_link import simulate

DEFAULT_NOISE = [0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0]


def theoretical_ber(noise_std: float) -> float:
    """For equally likely +/-1 symbols, ideal sampling, and Gaussian noise."""
    if noise_std < 0:
        raise ValueError("Noise standard deviation cannot be negative")
    return 0.0 if noise_std == 0 else 0.5 * erfc(1.0 / (sqrt(2.0) * noise_std))


def run_sweep(noise_levels: list[float], n_bits: int = 100_000,
              samples_per_bit: int = 16, seed: int = 42) -> list[dict]:
    if any(x < 0 for x in noise_levels):
        raise ValueError("All noise levels must be nonnegative")
    results = []
    for level in noise_levels:
        data = simulate(n_bits=n_bits, noise_std=level,
                        samples_per_bit=samples_per_bit, seed=seed)
        results.append({
            "noise_std": level,
            "bits": n_bits,
            "errors": data["bit_errors"],
            "measured_ber": data["ber"],
            "theoretical_ber": theoretical_ber(level),
        })
    return results


def save_csv(results: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=[
            "noise_std", "bits", "errors", "measured_ber", "theoretical_ber"])
        writer.writeheader()
        writer.writerows(results)


def save_plot(results: list[dict], path: Path) -> None:
    levels = [r["noise_std"] for r in results]
    theory = [r["theoretical_ber"] for r in results]
    # Logarithmic axes cannot show BER=0, so exclude those points rather than
    # plotting them as though they have a small nonzero BER.
    measured_x = [r["noise_std"] for r in results if r["errors"] > 0]
    measured_y = [r["measured_ber"] for r in results if r["errors"] > 0]
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.semilogy(levels, theory, "-", label="Theoretical BER")
    ax.semilogy(measured_x, measured_y, "o", label="Measured BER")
    ax.set_xlabel("Gaussian noise standard deviation (amplitude units)")
    ax.set_ylabel("Bit error rate (BER)")
    ax.set_title("NRZ Link: BER vs Gaussian Noise")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bits", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--samples-per-bit", type=int, default=16)
    parser.add_argument("--noise-levels", type=float, nargs="+", default=DEFAULT_NOISE)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    args = parser.parse_args()
    results = run_sweep(args.noise_levels, args.bits, args.samples_per_bit, args.seed)
    csv_path = args.output_dir / "ber_sweep.csv"
    plot_path = args.output_dir / "ber_vs_noise.png"
    save_csv(results, csv_path)
    save_plot(results, plot_path)
    print(f"{'Noise std':>10} {'Errors':>10} {'Measured BER':>15} {'Theory BER':>15}")
    for r in results:
        print(f"{r['noise_std']:10.2f} {r['errors']:10,d} "
              f"{r['measured_ber']:15.8f} {r['theoretical_ber']:15.8f}")
    print(f"\nCSV saved: {csv_path}\nPlot saved: {plot_path}")
    print("Note: 0 observed errors does NOT mean the true BER is zero.")


if __name__ == "__main__":
    main()
