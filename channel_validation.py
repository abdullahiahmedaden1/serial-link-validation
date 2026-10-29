"""Milestone 4: bandwidth-limited NRZ channel, BER sweep and eye diagrams.

Run: python channel_validation.py
Uses a first-order low-pass approximation (not a physical SerDes model).
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def lowpass(waveform: np.ndarray, cutoff_per_bit: float, samples_per_bit: int) -> np.ndarray:
    """One-pole RC lowpass; cutoff is in cycles per bit period.

    y[n] = a*x[n] + (1-a)*y[n-1], with a=1-exp(-2*pi*fc/fs).
    This is the exact zero-order-hold discretization of an RC response.
    """
    if cutoff_per_bit <= 0 or samples_per_bit < 2:
        raise ValueError('cutoff_per_bit must be positive, samples_per_bit >= 2')
    alpha = -np.expm1(-2 * np.pi * cutoff_per_bit / samples_per_bit)
    out = np.empty_like(waveform, dtype=np.float64)
    state = 0.0
    for i, value in enumerate(waveform):
        state = alpha * value + (1.0 - alpha) * state
        out[i] = state
    return out


def simulate_channel(bits: int = 20_000, cutoff_per_bit: float = 0.25,
                     noise_std: float = 0.12, samples_per_bit: int = 16,
                     seed: int = 42) -> dict:
    if bits < 2 or noise_std < 0 or samples_per_bit < 4 or cutoff_per_bit <= 0:
        raise ValueError('bits >= 2, samples_per_bit >= 4, noise_std >= 0, cutoff > 0 required')
    rng = np.random.default_rng(seed)
    tx_bits = rng.integers(0, 2, size=bits, dtype=np.int8)
    tx_waveform = np.repeat(2 * tx_bits.astype(float) - 1.0, samples_per_bit)
    filtered = lowpass(tx_waveform, cutoff_per_bit, samples_per_bit)
    rx_waveform = filtered + rng.normal(0, noise_std, size=filtered.size)
    indices = np.arange(bits) * samples_per_bit + samples_per_bit // 2
    rx_bits = (rx_waveform[indices] >= 0).astype(np.int8)
    errors = int(np.count_nonzero(rx_bits != tx_bits))
    return {'tx_bits': tx_bits, 'tx_waveform': tx_waveform,
            'filtered_waveform': filtered, 'rx_waveform': rx_waveform,
            'sample_indices': indices, 'rx_bits': rx_bits,
            'bit_errors': errors, 'ber': errors / bits}


def plot_eye(result: dict, samples_per_bit: int, path: Path,
             max_traces: int = 180) -> None:
    """Overlay consecutive two-bit waveform windows; time origin is bit boundary.

    Decision center occurs at x=0.5 or x=1.5 bit periods.
    """
    waveform = result['rx_waveform']
    width = 2 * samples_per_bit
    # Start after initial transient. Aligned on bit boundaries.
    starts = np.arange(10 * samples_per_bit, len(waveform) - width + 1,
                       2 * samples_per_bit, dtype=int)[:max_traces]
    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(width) / samples_per_bit
    for start in starts:
        ax.plot(x, waveform[start:start + width], color='tab:blue', alpha=0.12,
                linewidth=0.8)
    for center in (0.5, 1.5):
        ax.axvline(center, color='tab:orange', linestyle=':', linewidth=1.0)
    ax.axhline(0, color='gray', linestyle='--', linewidth=1.0)
    ax.set(xlabel='Time (bit periods)', ylabel='Received amplitude',
           title='Eye diagram (aligned 2-bit windows)')
    ax.set_xlim(0, 2)
    ax.grid(alpha=0.2)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def run_sweep(bits: int, noise_std: float, samples_per_bit: int,
              seed: int, cutoffs: list[float], output_dir: Path) -> list[dict]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for cutoff in cutoffs:
        result = simulate_channel(bits, cutoff, noise_std, samples_per_bit, seed)
        rows.append({'cutoff_cycles_per_bit': cutoff,
                     'bits': bits, 'errors': result['bit_errors'], 'ber': result['ber']})
    with (output_dir / 'bandwidth_sweep.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot([r['cutoff_cycles_per_bit'] for r in rows],
            [r['ber'] for r in rows], marker='o')
    ax.set(xlabel='Low-pass cutoff (cycles per bit)', ylabel='Measured BER',
           title='Effect of bandwidth limitation on BER')
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_dir / 'ber_vs_bandwidth.png', dpi=160)
    plt.close(fig)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bits', type=int, default=20_000)
    parser.add_argument('--noise', type=float, default=0.12)
    parser.add_argument('--samples-per-bit', type=int, default=16)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--output-dir', type=Path, default=Path('outputs'))
    args = parser.parse_args()
    cutoffs = [0.05, 0.10, 0.20, 0.40, 0.80, 1.50]
    rows = run_sweep(args.bits, args.noise, args.samples_per_bit,
                     args.seed, cutoffs, args.output_dir)
    print('Cutoff (cycles/bit)    Errors     Measured BER')
    for row in rows:
        print(f"{row['cutoff_cycles_per_bit']:>18.2f}  {row['errors']:>8,}    {row['ber']:.8f}")
    for cutoff, name in [(0.10, 'eye_narrow_bandwidth.png'),
                         (0.80, 'eye_wide_bandwidth.png')]:
        result = simulate_channel(args.bits, cutoff, args.noise,
                                  args.samples_per_bit, args.seed)
        plot_eye(result, args.samples_per_bit, args.output_dir / name)
    print(f'Plots and CSV saved to: {args.output_dir.resolve()}')
    print('Model: first-order low-pass + Gaussian noise, ideal receiver timing.')
    print('Note: zero observed errors does not prove BER is zero.')


if __name__ == '__main__':
    main()
