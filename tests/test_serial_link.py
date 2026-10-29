import numpy as np
import pytest
from serial_link import simulate


def test_no_noise_means_no_errors():
    result = simulate(n_bits=1000, noise_std=0, samples_per_bit=8)
    assert result['bit_errors'] == 0
    assert result['ber'] == 0
    assert np.array_equal(result['tx_bits'], result['rx_bits'])


def test_reproducibility():
    a = simulate(n_bits=1000, seed=5)
    b = simulate(n_bits=1000, seed=5)
    assert np.array_equal(a['rx_waveform'], b['rx_waveform'])


def test_high_noise_produces_errors():
    result = simulate(n_bits=10000, noise_std=1.5)
    assert result['bit_errors'] > 0
    assert 0 < result['ber'] < 0.5


def test_invalid_parameters():
    with pytest.raises(ValueError):
        simulate(n_bits=0)
    with pytest.raises(ValueError):
        simulate(noise_std=-1)
