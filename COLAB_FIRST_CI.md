# KEP Colab-first CI

GitHub remains the source of truth, but compute-heavy validation no longer runs automatically in GitHub Actions.

## Colab

Run these cells:

```python
!git clone https://github.com/modernsnc2022-ai/Korea-Employment-Passport.git
%cd Korea-Employment-Passport
!bash scripts/run_colab_ci.sh
```

For official-source monitoring:

```python
!bash scripts/run_colab_source_monitor.sh
```

Only after a human review of exact changed fingerprints, the reviewed baseline may be accepted with:

```python
!bash scripts/run_colab_source_monitor.sh "$(pwd)" accept-current
```

## Kaggle / Lightning

The same shell scripts are portable to Kaggle and Lightning workers with Node 22, Python 3.12-compatible runtime, npm, Chromium dependencies, and outbound HTTPS.

## GitHub Actions policy

The repository workflows `static-check`, `ui-smoke`, `beta-launch-gate`, `official-source-monitor`, and `source-volatility-diagnostic` are manual-dispatch only. Do not re-enable push, pull_request, or schedule triggers without an explicit budget decision.

GitHub Pages may still show a Pages build/deployment run when its branch content changes. Treat Pages hosting/deployment separately from validation compute.
