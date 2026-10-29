import pytest
from snr_sweep import snr_to_noise_std, expected_ber, run_sweep


def test_zero_db_snr_has_unit_noise_std():
    assert snr_to_noise_std(0) == pytest.approx(1)


def test_higher_snr_has_lower_ber():
    assert expected_ber(snr_to_noise_std(9)) < expected_ber(snr_to_noise_std(0))


def test_run_sweep_count_and_error_bounds():
    rows = run_sweep([0, 6], n_bits=1000)
    assert len(rows) == 2
    assert all(0 <= r['errors'] <= r['bits'] for r in rows)
    assert all(r['measured_ber'] == r['errors'] / r['bits'] for r in rows)
