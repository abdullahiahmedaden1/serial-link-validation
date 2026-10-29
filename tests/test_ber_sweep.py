from math import isclose

import pytest

from ber_sweep import run_sweep, theoretical_ber


def test_theory_zero_noise():
    assert theoretical_ber(0.0) == 0.0


def test_theory_increases_with_noise():
    assert theoretical_ber(0.25) < theoretical_ber(0.5) < theoretical_ber(1.0)


def test_invalid_noise():
    with pytest.raises(ValueError):
        theoretical_ber(-0.1)


def test_zero_noise_no_errors():
    results = run_sweep([0.0], n_bits=200, samples_per_bit=4)
    assert results[0]["errors"] == 0
    assert isclose(results[0]["measured_ber"], 0.0)


def test_fixed_seed_reproducible():
    a = run_sweep([0.5], n_bits=500, seed=24)
    b = run_sweep([0.5], n_bits=500, seed=24)
    assert a == b
