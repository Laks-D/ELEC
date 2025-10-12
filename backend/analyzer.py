# backend/analyzer.py
import math

def detect_anomaly(units, baseline=200):
    """
    Units: numeric or string. baseline is sample average units (adjustable).
    Returns dict: anomaly boolean + reason string.
    """
    try:
        u = float(units)
    except Exception:
        return {"anomaly": False, "reason": "units-not-parsed"}

    if u == 0:
        return {"anomaly": True, "reason": "zero-reading-detected"}
    if u > baseline * 1.5 and u <= baseline * 6:
        return {"anomaly": True, "reason": "spike-detected-possible-ac-or-cumulative"}
    if u > baseline * 6:
        return {"anomaly": True, "reason": "extremely-large-reading-possible-cumulative-or-data-error"}
    return {"anomaly": False, "reason": "no-major-anomaly"}

def format_appliance_percentages(preds_dict):
    """
    preds_dict: {appliance: kWh}
    returns list of tuples (name, kWh, percent)
    """
    total = sum(preds_dict.values()) if preds_dict else 0.0
    if total == 0:
        return [(k, v, 0.0) for k, v in preds_dict.items()]
    out = []
    for k, v in preds_dict.items():
        pct = 100.0 * v / total
        out.append((k, round(v,1), round(pct,1)))
    return out
