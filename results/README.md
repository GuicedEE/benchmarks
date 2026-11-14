# Latest benchmark results

Only the current published measurement set lives here. Read [RESULTS.md](../RESULTS.md)
for the grids, percentage differences and analysis.

Chart regeneration uses the optional report dependency `matplotlib` (`python -m pip install matplotlib`).
Running benchmarks and verifying the published report require only the Python standard library.

`latest/measurements.json` contains every selected fresh start, raw latency sample,
capability result, phase capture and immutable image identity used by the report. Its
manifest records the byte count and SHA-256. It excludes source copies, logs, compiled
artifacts and superseded experiments. Original input hashes and batch IDs remain available
for provenance. Different profiles remain separate rather than pooling incomparable runs.

New executions write to ignored `target/runs/<timestamp>/`. To replace a published group:

```shell
python tools/publish_results.py jvm-default target/runs/<batch>
python tools/render_performance.py
python tools/render_charts.py
python tools/verify_latest.py
```

For counterbalanced native batches, pass both directories to `native-standard`. Publishing
requires complete passing comparisons and keeps all starts and samples for each selected
variant. Review the report's written analysis after replacing its numeric grids. Commit the
latest files and generated report together. Superseded published data remains in Git history.
