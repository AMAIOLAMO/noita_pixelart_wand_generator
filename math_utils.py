def clampf(v: float, a: float, b: float) -> float:
    return max(
        a, min(b, v)
    )
