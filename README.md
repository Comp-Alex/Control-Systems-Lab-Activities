# Control-Systems-Lab-Activities

Control systems lab activities, experiments, and simulations.

## Engineering dashboard

The [Control Systems Engineering Dashboard](dashboard/index.md) summarizes
tracked repository artifacts for PID experiments, system analysis, stability
studies, and control simulations. Its activity coverage indicates whether
matching evidence is present in the repository; it does not infer that an
experiment or study is complete.

The dashboard is refreshed daily by
[`.github/workflows/dashboard.yml`](.github/workflows/dashboard.yml), and can
also be refreshed manually from the Actions tab or locally:

```powershell
python dashboard\generate_dashboard.py
```

The generator uses Python's standard library and Git. To make an activity
appear in a topic, use a descriptive filename or include relevant terms in its
tracked file content. The report lists matching files and recent repository
commits; it does not read untracked or ignored files.