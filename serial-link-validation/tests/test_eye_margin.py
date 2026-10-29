from channel_validation import simulate_channel
from eye_margin import characterize


def test_phase_count():
    result = simulate_channel(bits=1000, cutoff_per_bit=.4, samples_per_bit=16)
    rows = characterize(result, 16)
    assert len(rows) == 16
    assert all(0 <= row['ber'] <= 1 for row in rows)


def test_wider_bandwidth_more_center_eye():
    narrow = characterize(simulate_channel(bits=3000, cutoff_per_bit=.1, samples_per_bit=16), 16)
    wide = characterize(simulate_channel(bits=3000, cutoff_per_bit=.8, samples_per_bit=16), 16)
    assert wide[8]['eye_height_p5_p95'] > narrow[8]['eye_height_p5_p95']
