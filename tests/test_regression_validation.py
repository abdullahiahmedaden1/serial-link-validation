import json

import pytest
from regression_validation import evaluate, run


def test_evaluate_pass():
    assert evaluate(0.001, 0.8, 0.5)['status'] == 'PASS'


def test_evaluate_fail_individual_limits():
    for ber, eye, window in [(0.02, 0.8, 0.5), (0.001, 0.1, 0.5), (0.001, 0.8, 0.1)]:
        assert evaluate(ber, eye, window)['status'] == 'FAIL'


def test_report_written_and_repeatable(tmp_path):
    a = run(bits=500, output_dir=tmp_path / 'run_a', cutoffs=[0.1, 0.8])
    b = run(bits=500, output_dir=tmp_path / 'run_b', cutoffs=[0.1, 0.8])
    assert a['results'] == b['results']
    assert a['summary']['total'] == 2
    assert (tmp_path / 'run_a' / 'regression_results.csv').exists()
    assert json.loads((tmp_path / 'run_a' / 'regression_report.json').read_text())['summary'] == a['summary']


def test_invalid_inputs(tmp_path):
    with pytest.raises(ValueError):
        run(bits=100, output_dir=tmp_path)
