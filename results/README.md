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
Host restart and between-stage CPU, available-memory and disk-queue observations are
retained with the measurements when recorded. They describe the stage boundaries, including
untimed preparation, rather than continuous background load during every timed sample.

`latest/builds.json` contains the current clean-build cohort: all compile/package samples,
untimed cache preparation, exact commands, toolchain details and input hashes. It separates
build costs from runtime measurements. Full Maven logs stay in the ignored local run folder;
log hashes, all timing samples and extracted completion evidence are retained here.

`latest/native-profile.json` contains only the current native artifact's compiler inclusion
counts, code origins, SDK reflection/allocation policy and source hashes. Runtime timings
come from the current comparison groups in `measurements.json`.

Keep the latest complete cohort for each published execution mode and diagnostic profile.
All repeated starts and request samples within that cohort remain available; "latest" does
not mean selecting the last or fastest individual run. Before/after optimization experiments,
superseded cohorts and unused image metadata stay out of the published snapshot. The
extended native cohort retains all 1,000 requests per start.

The JVM matrices use the actual Maven-packaged wrapper. Native and clean-build cohorts
remain the latest measured for those modes, with their distinct artifact inputs identified.

New executions write to ignored `target/runs/<timestamp>/`.
The root Maven aggregator preserves this evidence directory during `clean`; application
modules still clean their own compiled outputs and packaged artifacts.

To replace a published group:

```shell
python tools/publish_results.py jvm-default target/runs/<batch>
python tools/publish_results.py phases target/runs/<diagnostic-batch>
python tools/publish_builds.py target/build-runs/<build-batch>
python tools/publish_native_profile.py target/runs/<current-native-batch> --artifact-build-log target/<native-build.log>
python tools/render_performance.py
python tools/render_charts.py
python tools/verify_latest.py
```

For counterbalanced native batches, pass both directories to `native-standard`. Publishing
requires complete passing comparisons and keeps all starts and samples for each selected
variant. Review the report's written analysis after replacing its numeric grids. Commit the
latest files and generated report together. The result-file allowlist prevents old run
directories and ad hoc audits from being added accidentally. Superseded published data
remains accessible through Git history, without being kept in the current checkout.
