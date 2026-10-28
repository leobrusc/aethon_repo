import numpy as np
from statsmodels.stats.contingency_tables import mcnemar

def bootstrap_ci(values, n=1000, alpha=0.05, seed=2026):
    arr = np.asarray(values, dtype=float)
    if arr.ndim != 1 or not len(arr) or not np.isfinite(arr).all() or n < 1 or not 0 < alpha < 1:
        raise ValueError("Expected finite nonempty values and valid bootstrap parameters")
    rng = np.random.default_rng(seed)
    means = []
    for _ in range(n):
        sample = rng.choice(arr, size=len(arr), replace=True)
        means.append(np.mean(sample))
    lo = np.percentile(means, 100*alpha/2)
    hi = np.percentile(means, 100*(1-alpha/2))
    return float(np.mean(arr)), float(lo), float(hi)


def paired_bootstrap_difference(y_true, first, second, metric, *, clusters=None,
                                n=2000, alpha=.05, seed=2026):
    """Percentile CI for metric(first)-metric(second), preserving row pairs.

    Cluster resampling draws whole source/family clusters with replacement.
    Without clusters, resample independently within each true class.
    Undefined resamples are reported, never silently replaced with zeros.
    """
    truth, first, second = (np.asarray(x) for x in (y_true, first, second))
    if truth.ndim != 1 or not len(truth) or first.shape != truth.shape or second.shape != truth.shape:
        raise ValueError("Expected nonempty aligned paired arrays")
    if n < 1 or not 0 < alpha < 1:
        raise ValueError("Invalid bootstrap parameters")
    if clusters is not None:
        clusters = np.asarray(clusters)
        if clusters.shape != truth.shape:
            raise ValueError("Cluster shape mismatch")
        groups = [np.flatnonzero(clusters == c) for c in np.unique(clusters)]
    else:
        groups = [np.flatnonzero(truth == c) for c in np.unique(truth)]
    rng, differences = np.random.default_rng(seed), []
    for _ in range(n):
        if clusters is None:
            indices = np.concatenate([rng.choice(g, len(g), replace=True) for g in groups])
        else:
            indices = np.concatenate([groups[i] for i in rng.integers(len(groups), size=len(groups))])
        try:
            value = float(metric(truth[indices], first[indices]) - metric(truth[indices], second[indices]))
        except ValueError:
            continue
        if np.isfinite(value):
            differences.append(value)
    point = float(metric(truth, first) - metric(truth, second))
    bounds = np.quantile(differences, [alpha/2, 1-alpha/2]) if differences else [None, None]
    return {"difference": point, "ci_low": bounds[0], "ci_high": bounds[1],
            "confidence": 1-alpha, "seed": seed, "iterations": n,
            "valid_resamples": len(differences), "n_pairs": len(truth),
            "n_clusters": len(groups) if clusters is not None else None,
            "method": "paired cluster percentile" if clusters is not None else "paired class-stratified percentile"}

def mcnemar_test(y_true, y_pred1, y_pred2):
    truth, first, second = (np.asarray(x) for x in (y_true, y_pred1, y_pred2))
    if truth.ndim != 1 or first.shape != truth.shape or second.shape != truth.shape or not len(truth):
        raise ValueError("Expected nonempty aligned one-dimensional paired arrays")
    if any(not np.isin(x, [0, 1]).all() for x in (truth, first, second)):
        raise ValueError("Expected binary labels and predictions")
    correct1, correct2 = first == truth, second == truth
    table = [[int((correct1 & correct2).sum()), int((correct1 & ~correct2).sum())],
             [int((~correct1 & correct2).sum()), int((~correct1 & ~correct2).sum())]]
    result = mcnemar(table, exact=True)
    return result.pvalue
