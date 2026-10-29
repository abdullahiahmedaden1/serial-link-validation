"""Milestone 5: eye-height and sampling-phase characterization.

Run from the repository root: python eye_margin.py
This is a sampled, percentile-based eye-opening metric, not a compliance eye mask.
"""
import argparse
import csv
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from channel_validation import simulate_channel


def characterize(result, samples_per_bit=16, settle_bits=10):
    bits = result['tx_bits'][settle_bits:]
    rx = result['rx_waveform'].reshape(-1, samples_per_bit)[settle_bits:]
    if len(bits) < 100 or np.count_nonzero(bits == 0) < 10 or np.count_nonzero(bits == 1) < 10:
        raise ValueError('Insufficient bits for eye margin estimation')
    rows = []
    for phase in range(samples_per_bit):
        samples = rx[:, phase]
        zero, one = samples[bits == 0], samples[bits == 1]
        low_one = float(np.percentile(one, 5))
        high_zero = float(np.percentile(zero, 95))
        opening = low_one - high_zero
        decisions = (samples >= 0).astype(np.int8)
        errors = int(np.count_nonzero(decisions != bits))
        rows.append({'phase': phase, 'phase_ui': (phase + 0.5) / samples_per_bit,
                     'eye_height_p5_p95': opening, 'ber': errors / len(bits),
                     'errors': errors})
    return rows


def run(bits=20000, noise=0.12, samples_per_bit=16, seed=42, output_dir=Path('outputs')):
    output_dir.mkdir(parents=True, exist_ok=True)
    cutoffs = [0.10, 0.20, 0.40, 0.80]
    summary = []
    fig, ax = plt.subplots(figsize=(8, 5))
    for cutoff in cutoffs:
        result = simulate_channel(bits=bits, cutoff_per_bit=cutoff,
                                  noise_std=noise, samples_per_bit=samples_per_bit, seed=seed)
        phase_rows = characterize(result, samples_per_bit)
        center = phase_rows[samples_per_bit // 2]
        positive = [r for r in phase_rows if r['eye_height_p5_p95'] > 0]
        summary.append({'cutoff_cycles_per_bit': cutoff,
                        'center_eye_height': center['eye_height_p5_p95'],
                        'center_ber': center['ber'],
                        'positive_eye_phases': len(positive),
                        'timing_window_ui': len(positive)/samples_per_bit})
        ax.plot([r['phase_ui'] for r in phase_rows],
                [r['eye_height_p5_p95'] for r in phase_rows], marker='.',
                label=f'Cutoff {cutoff:.2f} cycles/bit')
    ax.axhline(0, color='gray', linestyle='--', linewidth=1)
    ax.set(xlabel='Sampling phase (UI)', ylabel='Eye height (5th percentile 1 - 95th percentile 0)',
           title='Sampling phase vs. estimated eye opening')
    ax.legend(); ax.grid(alpha=0.25)
    fig.tight_layout(); fig.savefig(output_dir/'eye_height_vs_phase.png', dpi=160); plt.close(fig)
    with (output_dir/'eye_margin_summary.csv').open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=list(summary[0])); writer.writeheader(); writer.writerows(summary)
    print('Cutoff   Center eye height   Center BER    Positive phases   Timing window (UI)')
    for r in summary:
        print(f"{r['cutoff_cycles_per_bit']:5.2f}    {r['center_eye_height']:16.4f}  "
              f"{r['center_ber']:11.6f}       {r['positive_eye_phases']:2d}/{samples_per_bit}          {r['timing_window_ui']:.3f}")
    print(f"Saved {output_dir / 'eye_height_vs_phase.png'} and {output_dir / 'eye_margin_summary.csv'}")
    print('Note: positive-eye-phases is a coarse, sampled timing-window proxy, not physical jitter tolerance.')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bits', type=int, default=20000)
    parser.add_argument('--noise', type=float, default=0.12)
    parser.add_argument('--samples-per-bit', type=int, default=16)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--output-dir', type=Path, default=Path('outputs'))
    args = parser.parse_args()
    run(bits=args.bits, noise=args.noise, samples_per_bit=args.samples_per_bit,
        seed=args.seed, output_dir=args.output_dir)
