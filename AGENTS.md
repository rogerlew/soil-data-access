# Soil Data Access contributor guide

This is an independent, unofficial, open-source soil-data service in assessment.
Read docs/contract.md and docs/wepppy-release-gate.md before changing behavior. Implement against the active
ExecPlan in docs/implementation-plan.md and keep its progress and decisions current.
Change the contract and acceptance fixtures before executable behavior.
Do not claim full SDA compatibility, national coverage, parity, or performance
without retained evidence identifying source release, code revision, and hardware.
Preserve source identifiers, nulls, units, precision, and relationship semantics.
Unsupported SQL must fail explicitly; never silently rewrite its meaning.
Use task branches. Keep source, tests, import tools, and portable Compose here;
environment deployment ownership belongs to /workdir/open-wepp-org.
No production deployment, DNS, firewall, or shared database changes are implied by
local implementation. Keep credentials and data downloads outside Git.
Public SQL execution requires a documented threat model and security review.

Initial deployment is gated by WEPPpy cache/artifact parity plus import, security,
capacity, and recovery evidence. Full SDA parity is deferred, not a blocker for
that bounded release. Never claim deployment readiness from offline assessment
checks or treat processed project caches as raw SDA/source-import ground truth.
