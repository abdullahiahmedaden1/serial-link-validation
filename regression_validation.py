"""Milestone 6: repeatable pass/fail regression for a simulated NRZ channel.

Requires channel_validation.py and eye_margin.py in the same folder.
Run from the repository root: python regression_validation.py
"""
import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from channel_validation import simulate_channel
from eye_margin import characterize

DEFAULT_CUTOFFS = [0.10, 0.20, 0.40, 0.80]


def evaluate(ber, eye_height, window_ui, max_ber=0.01,
             min_eye_height=0.40, min_window_ui=0.25):
    """Compare measurements to *project-defined* limits, not industry standards."""
    checks = {
        'ber': ber <= max_ber,
        'eye_height': eye_height >= min_eye_height,
        'timing_window': window_ui >= min_window_ui,
    }
    return {'status': 'PASS' if all(checks.values()) else 'FAIL', 'checks': checks}


def run(bits=20_000, noise=0.12, samples_per_bit=16, seed=42,
        cutoffs=None, output_dir=Path('outputs'), max_ber=0.01,
        min_eye_height=0.40, min_window_ui=0.25):
    if bits < 110 or samples_per_bit < 4 or noise < 0:
        raise ValueError('bits >= 110, samples_per_bit >= 4 and noise >= 0 required')
    if not (0 <= max_ber <= 1) or min_window_ui < 0:
        raise ValueError('Invalid validation limits')
    if cutoffs is None:
        cutoffs = DEFAULT_CUTOFFS
    if not cutoffs or any(c <= 0 for c in cutoffs):
        raise ValueError('Provide at least one positive cutoff')
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for cutoff in cutoffs:
        result = simulate_channel(bits=bits, cutoff_per_bit=cutoff,
                                  noise_std=noise, samples_per_bit=samples_per_bit,
                                  seed=seed)
        phases = characterize(result, samples_per_bit=samples_per_bit)
        center = phases[samples_per_bit // 2]
        window_ui = sum(p['eye_height_p5_p95'] > 0 for p in phases) / samples_per_bit
        verdict = evaluate(center['ber'], center['eye_height_p5_p95'], window_ui,
                           max_ber, min_eye_height, min_window_ui)
        rows.append({
            'cutoff_cycles_per_bit': cutoff, 'bits_evaluated': bits-10,
            'center_errors': center['errors'], 'center_ber': center['ber'],
            'center_eye_height': center['eye_height_p5_p95'],
            'timing_window_ui': window_ui,
            'ber_check': verdict['checks']['ber'],
            'eye_height_check': verdict['checks']['eye_height'],
            'timing_window_check': verdict['checks']['timing_window'],
            'status': verdict['status'],
        })
    csv_path = output_dir / 'regression_results.csv'
    with csv_path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    report = {
        'description': 'Behavioral simulated NRZ link: non-compliance project thresholds',
        'generated_utc': datetime.now(timezone.utc).isoformat(),
        'configuration': {'bits': bits, 'noise_std': noise,
                          'samples_per_bit': samples_per_bit, 'seed': seed},
        'limits': {'max_center_ber': max_ber, 'min_center_eye_height': min_eye_height,
                   'min_timing_window_ui': min_window_ui},
        'summary': {'pass': sum(r['status']=='PASS' for r in rows),
                    'fail': sum(r['status']=='FAIL' for r in rows),
                    'total': len(rows)},
        'results': rows,
    }
    (output_dir / 'regression_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('Cutoff   Center BER  Eye height  Window(UI)  Verdict')
    for r in rows:
        print(f"{r['cutoff_cycles_per_bit']:6.2f}    {r['center_ber']:8.5f}  "
              f"{r['center_eye_height']:10.3f}  {r['timing_window_ui']:10.3f}  {r['status']}")
    print(f"Summary: {report['summary']['pass']} PASS, {report['summary']['fail']} FAIL")
    print(f'Reports: {csv_path} and {output_dir / "regression_report.json"}')
    print('FAIL means the project-defined performance limit was not met, NOT that the simulation crashed.')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bits', type=int, default=20_000)
    parser.add_argument('--noise', type=float, default=0.12)
    parser.add_argument('--samples-per-bit', type=int, default=16)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--max-ber', type=float, default=0.01)
    parser.add_argument('--min-eye-height', type=float, default=0.40)
    parser.add_argument('--min-window-ui', type=float, default=0.25)
    parser.add_argument('--output-dir', type=Path, default=Path('outputs'))
    args = parser.parse_args()
    run(bits=args.bits, noise=args.noise, samples_per_bit=args.samples_per_bit,
        seed=args.seed, max_ber=args.max_ber, min_eye_height=args.min_eye_height,
        min_window_ui=args.min_window_ui, output_dir=args.output_dir)
