# What belongs in this repository

Keep the Maven applications and module descriptors, shared workload, Python harness and
tests, Docker/PowerShell build recipes, emulator configuration and npm lockfile, checked-in
native metadata with its input hashes, and the analysis reports.

`results/retained-evidence.json` is the explicit inventory of published evidence. It lists
files, byte sizes and SHA-256 hashes. The initial archive retains the batches cited by the
reports and result index, including unsuccessful and instrumented diagnostics, together
with their raw JSON samples, environment/source provenance, graph inventories and validation
records. It also retains the raw native-agent JSON used by the native integration. Eligibility
and failure markers are preserved: an unsuccessful run does not become a baseline by being
archived.

New result directories are ignored by default. To publish a new comparison:

1. Review its capability results, source/image identities, resource limits and interpretation.
2. Include all relevant runs and diagnostics, not only favorable samples. Check generated
   files for credentials or private local configuration before publishing.
3. Add the selected evidence explicitly with `git add -f`, update the manifest with
   `python tools/verify_retained_evidence.py --refresh`, and link the report to that evidence.
4. Run `python tools/verify_retained_evidence.py` and the harness tests before committing.

Build directories, Maven repository snapshots, JARs/native executables, native-agent binaries,
Docker images, npm dependencies, IDE files, private environment overrides, logs and command
argument files remain local. Existing copies are preserved during the submodule conversion.
Compiled native reachability metadata under application resources is an intentional build
input and is retained. The two committed `.env` files contain only public fixture defaults.

Historical evidence is an immutable record. Do not rewrite its paths, source snapshots or
checksums to look like a newer checkout. `.gitattributes` preserves file bytes across Git
checkouts so source/evidence hashes are not changed by automatic newline conversion.
