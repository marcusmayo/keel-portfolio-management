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

## Model selection (gateway mode)

By default `claude -p` calls Anthropic directly using `ANTHROPIC_API_KEY`. To run
chat and skills on a cheaper or non-Anthropic model, route `claude -p` through the
bundled LiteLLM gateway. The gateway has no host port -- it is reachable only on the
internal compose network -- so provider configs run keyless: the network boundary is
the control, not a proxy key.

`LITELLM_CONFIG` selects the gateway config and is a **compose-time shell variable**,
not a `keel.env` variable. Pass it on the `up` line (alongside `KEEL_PUBLISH_ADDR`),
the same way Compose reads `${...}` substitutions. Putting it in `keel.env` has no
effect -- the gateway silently falls back to its default config.

OpenRouter (cross-provider aggregator; kimi-k3 / glm-5.2 / deepseek-v4-pro):

    # keel.env -- add:
    #   ANTHROPIC_BASE_URL=http://gateway:4000
    #   ANTHROPIC_MODEL=claude-sonnet-4-5                     (alias -> kimi-k3)
    #   ANTHROPIC_SMALL_FAST_MODEL=claude-3-5-haiku-20241022  (alias -> glm-5.2)
    #   OPENROUTER_API_KEY=sk-or-v1-...
    #   (leave ANTHROPIC_API_KEY as your real Anthropic key -- the keyless gateway
    #    ignores it, and the image-interpret path still uses it against Anthropic)

    sudo env KEEL_PUBLISH_ADDR=<addr> LITELLM_CONFIG=openrouter.yaml \
      docker compose -f infra/docker/compose.yaml --profile gateway up -d

Verify which provider the gateway actually routes to (ground truth from the proxy's
routing table, not the model's self-report):

    ./infra/scripts/verify-gateway.sh

Other configs (`gemini.yaml`, `ollama.yaml`) live in `infra/docker/litellm/`; see
`infra/docs/gateway-findings.md` for the LiteLLM >=1.92 keyless rationale.
