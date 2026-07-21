# Keel

Single-operator portfolio management: deterministic Python tools, YAML
state, Excel round-trip review, LLM reserved for semantic judgment only.
Runs as a pinned, hash-verified container -- self-contained via Docker
Compose, or on Azure via the Bicep templates in infra/.

Quickstart and full documentation: see infra/README.md.
(Stub README -- full public README pending.)

## Running the demo

The Northwind end-to-end demo runs the full reconciliation pipeline against a
synthetic corpus and verifies every step against a ground-truth oracle. It runs
INSIDE the container -- where the Python deps and the `claude` CLI resolve -- not
on the host:

    docker exec -w /app keel-webchat bash run_e2e.sh --yes

`--yes` clears the destructive-demo guard: the demo overwrites `keel.config.json`,
reseeds the corpus, and drafts demo items into `state/`. Run it on a fresh
deployment, before loading real data. Reset with `bash clean_demo.sh --yes`.

## Data persistence

Application state lives in four named Docker volumes (`keel-state`,
`keel-knowledge`, `keel-logs`, `keel-support`), mounted at `/app/state`,
`/app/knowledge`, `/app/logs`, and `/app/support`. The image is code; the volumes
are state. Data written there survives container restarts, `docker compose down`,
and VM reboots. It is destroyed only by `docker compose down -v`, an explicit
`docker volume rm`, or deleting the VM.
