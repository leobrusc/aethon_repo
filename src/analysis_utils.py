import numpy as np
from statsmodels.stats.contingency_tables import mcnemar

def bootstrap_ci(values, n=1000, alpha=0.05):
    arr = np.array(values)
    means = []
    for _ in range(n):
        sample = np.random.choice(arr, size=len(arr), replace=True)
        means.append(np.mean(sample))
    lo = np.percentile(means, 100*alpha/2)
    hi = np.percentile(means, 100*(1-alpha/2))
    return float(np.mean(arr)), float(lo), float(hi)

def mcnemar_test(y_true, y_pred1, y_pred2):
    b = sum((a==1 and b1==0 and b2==1) for a,b1,b2 in zip(y_true,y_pred1,y_pred2))
    c = sum((a==0 and b1==1 and b2==0) for a,b1,b2 in zip(y_true,y_pred1,y_pred2))
    table = [[0, b],[c,0]]
    result = mcnemar(table)
    return result.pvalue
