"""Milestone 1: reproducible NRZ link simulation and BER measurement."""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use('Agg')  # Works even without a GUI/display
import matplotlib.pyplot as plt
import numpy as np


def simulate(n_bits: int = 100_000, noise_std: float = 0.5,
             samples_per_bit: int = 16, seed: int = 42) -> dict:
    """Simulate binary NRZ (+1/-1) over an additive Gaussian noise channel.

    A fixed center sample of each bit is used for ideal-timing detection.
    The model does NOT include channel bandwidth limits, ISI, or jitter yet.
    """
    if n_bits <= 0 or samples_per_bit <= 0 or noise_std < 0:
        raise ValueError('n_bits and samples_per_bit must be positive; noise_std >= 0')

    rng = np.random.default_rng(seed)
    tx_bits = rng.integers(0, 2, size=n_bits, dtype=np.int8)
    tx_symbols = 2 * tx_bits.astype(np.float64) - 1.0
    tx_waveform = np.repeat(tx_symbols, samples_per_bit)
    rx_waveform = tx_waveform + rng.normal(0.0, noise_std, tx_waveform.size)

    sample_positions = np.arange(n_bits) * samples_per_bit + samples_per_bit // 2
    rx_samples = rx_waveform[sample_positions]
    rx_bits = (rx_samples >= 0.0).astype(np.int8)
    errors = int(np.count_nonzero(tx_bits != rx_bits))

    return {
        'tx_bits': tx_bits, 'rx_bits': rx_bits,
        'tx_waveform': tx_waveform, 'rx_waveform': rx_waveform,
        'sample_positions': sample_positions,
        'bit_errors': errors, 'ber': errors / n_bits,
    }


def make_plot(result: dict, samples_per_bit: int, output: Path,
              display_bits: int = 20) -> None:
    n = min(display_bits, len(result['tx_bits'])) * samples_per_bit
    time_in_bits = np.arange(n) / samples_per_bit
    fig, axes = plt.subplots(2, 1, figsize=(11, 6), sharex=True)
    axes[0].step(time_in_bits, result['tx_waveform'][:n], where='post')
    axes[0].set_ylabel('TX amplitude')
    axes[0].set_title('Transmitted NRZ waveform')
    axes[1].plot(time_in_bits, result['rx_waveform'][:n], linewidth=0.8)
    points = result['sample_positions']
    points = points[points < n]
    axes[1].scatter(points / samples_per_bit,
                    result['rx_waveform'][points], s=16, label='Decision samples')
    axes[1].axhline(0, linestyle='--', color='gray', label='Decision threshold')
    axes[1].set_ylabel('RX amplitude')
    axes[1].set_xlabel('Time (bit periods)')
    axes[1].set_title('Received waveform with additive Gaussian noise')
    axes[1].legend(loc='upper right')
    for ax in axes:
        ax.grid(alpha=0.3)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bits', type=int, default=100_000)
    parser.add_argument('--noise', type=float, default=0.5,
                        help='Gaussian noise standard deviation, amplitude units')
    parser.add_argument('--samples-per-bit', type=int, default=16)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--output', type=Path, default=Path('outputs/waveforms.png'))
    args = parser.parse_args()
    result = simulate(args.bits, args.noise, args.samples_per_bit, args.seed)
    make_plot(result, args.samples_per_bit, args.output)
    print(f'Bits transmitted: {args.bits:,}')
    print(f'Bit errors:       {result["bit_errors"]:,}')
    print(f'Measured BER:     {result["ber"]:.8f}')
    print(f'Plot saved to:    {args.output}')
    if result['bit_errors'] == 0:
        print('Note: zero observed errors does not prove the true BER is zero.')


if __name__ == '__main__':
    main()
