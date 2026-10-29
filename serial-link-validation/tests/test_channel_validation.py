import numpy as np
import pytest
from channel_validation import simulate_channel, lowpass


def test_reproducible():
    a = simulate_channel(bits=500, cutoff_per_bit=0.2, seed=123)
    b = simulate_channel(bits=500, cutoff_per_bit=0.2, seed=123)
    assert a['bit_errors'] == b['bit_errors']
    assert np.array_equal(a['rx_waveform'], b['rx_waveform'])


def test_error_count_matches_ber():
    result = simulate_channel(bits=1000, cutoff_per_bit=0.1)
    assert result['ber'] == result['bit_errors'] / 1000


def test_more_bandwidth_improves_ber_for_noiseless_model():
    narrow = simulate_channel(bits=4000, cutoff_per_bit=0.05, noise_std=0)
    wide = simulate_channel(bits=4000, cutoff_per_bit=1.5, noise_std=0)
    assert narrow['ber'] > wide['ber']
    assert wide['bit_errors'] == 0


def test_invalid_input():
    with pytest.raises(ValueError):
        simulate_channel(bits=0)
    with pytest.raises(ValueError):
        lowpass(np.ones(8), cutoff_per_bit=0, samples_per_bit=16)
