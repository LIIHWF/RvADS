FLOAT_EPS = 1e-10


def lerp(min_val, max_val, rate):
    return min_val + (max_val - min_val) * rate


def clamp(val, min_val, max_val):
    return min(max_val, (max(min_val, val)))


