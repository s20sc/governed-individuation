# Research records and offline analyses for authority claims in adaptive agents

This is the research-records release research-v1.0.0, dated22October2026. It includes retained study records, two prospective collections (152 and128 generation attempts), AI-assisted clause annotations, observation-class analyses, supporting figure sources/assets and qualified BEHAVIOR saved-cost records. It generates no new model responses and does not rerun the simulator or deployment backend.

## Recompute the supported results

The complete entry point has been validated on Python3.10.9 and Python3.12.14. Choose a new output directory outside this immutable tree:

    python -B reproducibility/run_offline.py /absolute/new/reanalysis-output
    cd analysis
    python -B -m unittest test_observation_analysis.py
    cd ../reproducibility
    python -B -m unittest test_full_scope_entry.py

The entry point runs10 bounded readers. Thirteen outputs require byte equality with this derivative's expected outputs; two JSON outputs use the original eight-control/twelve-cost numerical contracts. Observation results differ from the original expected JSON only in the enclosing archive identity. All counts, record IDs, labels, quoted clauses and scientific values are unchanged. Read reproducibility/NUMERICAL-CONTRACTS.md and IMPLEMENTATION-AVAILABILITY.md for their exact scope and absent implementations. Figure sources do not imply that every original figure input or full experimental runtime is supplied.

## Provenance and private reports

The original internal archive is preserved separately. This derivative excludes private code/scientific review reports and the internal freeze-check report. Frozen plans, input files, collection authorizations, raw requests/responses, annotations and scientific expected outputs remain byte-identical. The unchanged launch authorizations retain their original review digests, but the actual reports are not distributed or revalidated here. The control verifier now checks those retained digest bindings without reading the omitted private reports. Package manifests, this verifier and its corresponding regression test identify the derivative. No scientific scorer function or collection constant changes.

provenance/derivation-map.json enumerates every removed, added and changed archive leaf, including original and derivative identities. Collection logs retain original host-path strings as provenance; the supported relocated entry point does not access those host paths. No claim of complete anonymization is made.

## Rights and publication status

Author-controlled software is licensed under MIT. Author-controlled data, figures, research documentation and the retained author manuscript text are licensed under CC BY4.0. Existing third-party terms and attribution notices continue to apply. See LICENSING.md and the two complete licence texts for exact scope, including nested ZIP members. No third-party rights are granted by the authors.

This version is published at https://github.com/s20sc/governed-individuation/releases/tag/research-v1.0.0. The manifest identifies the files; inputs/research-data.zip retains its independently checked identity. Original collection records retain preparation-time status text and private-review digests as provenance. Such text does not describe the publication status or revoke the licence of this version. The underlying private review reports are excluded and are not revalidated by this release.

No author photographs, biographies or current journal submission files are included. Two retained V8 manuscript TeX files remain in the older study archive as scientific reference inputs. Original machine paths remain as provenance. Scientific AI annotation requests/responses are retained research data. Byte binding and offline arithmetic do not authenticate original model execution, establish human annotation ground truth, demonstrate causal governance gains or reproduce absent execution implementations.

Citation metadata is supplied in CITATION.cff. This is a GitHub research release, not a DOI registration or journal submission.

Runtime limitation: Python3.9.6 failed a strict feedback-output comparison at two non-whitelisted floating-point leaves. That execution remains a failure; no expected scientific value or numerical tolerance was widened. Python3.10.9 passed independent checks and Python3.12.14 passed local and relocated OS-sandbox checks. Other interpreter versions are unverified.
