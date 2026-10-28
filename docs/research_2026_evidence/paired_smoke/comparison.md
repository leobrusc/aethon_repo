# Exploratory paired tooling smoke

{
  "hypothesis": "equal paired correctness; two-sided exact McNemar",
  "n_pairs": 18,
  "mcnemar_p": 1.0,
  "multiplicity": "unadjusted exploratory; prespecify family before confirmatory interpretation",
  "accuracy": {
    "difference": 0.0,
    "ci_low": -0.22222222222222227,
    "ci_high": 0.22361111111111145,
    "confidence": 0.95,
    "seed": 2026,
    "iterations": 200,
    "valid_resamples": 200,
    "n_pairs": 18,
    "n_clusters": null,
    "method": "paired class-stratified percentile"
  },
  "f1": {
    "difference": 0.09523809523809523,
    "ci_low": -0.0925,
    "ci_high": 0.41758241758241754,
    "confidence": 0.95,
    "seed": 2026,
    "iterations": 200,
    "valid_resamples": 200,
    "n_pairs": 18,
    "n_clusters": null,
    "method": "paired class-stratified percentile"
  },
  "recall": {
    "difference": 0.125,
    "ci_low": 0.0,
    "ci_high": 0.375,
    "confidence": 0.95,
    "seed": 2026,
    "iterations": 200,
    "valid_resamples": 200,
    "n_pairs": 18,
    "n_clusters": null,
    "method": "paired class-stratified percentile"
  },
  "smoke_only": true,
  "note": "No confirmatory significance claim; reused historical B3 predictions on the exact baseline smoke rows",
  "provenance": {
    "results\\research_2026\\baselines\\protectai-validated-smoke-2026-10-28\\predictions.csv": "21e42286e507fff18756adcd91d1d17d05fe9e5aaeb13cb28b74c4dc2e8c078d",
    "results\\revision\\detection\\per_prompt_results.csv": "914901a1ed82836dfb42567cb376ec90f20459d1ad0f9b12d72568f4bfca202a"
  }
}