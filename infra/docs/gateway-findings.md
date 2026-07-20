# LiteLLM Gateway + Ollama: Resolution Chain (T4 GPU leg, 2026-07-19)

Proving the cross-provider seam (webchat -> LiteLLM gateway -> host ollama -> qwen3 on a T4) surfaced five distinct faults, all specific to LiteLLM >= 1.92 and/or host-run ollama. Documented so the path is not re-walked.

## The five faults, in the order they surfaced

1. **`LITELLM_MASTER_KEY` in the environment activates DB-backed key validation.** Setting a master key (via env or `general_settings.master_key`) makes LiteLLM validate every presented credential against a virtual-key database. With no DB, authenticated calls fail `400 {"type":"no_db_connected","error":"No connected db"}`. Removing the yaml line is NOT sufficient — LiteLLM reads `LITELLM_MASTER_KEY` from the environment independently. **Fix:** unset the env var AND remove the yaml `master_key`; run the gateway keyless. Single-operator, network-isolated deployments rely on the network boundary, not a proxy key.

2. **Dangling `general_settings:` (null).** Removing `master_key` can leave a childless `general_settings:` line, which parses as null. Harmless here but wrong. **Fix:** remove the empty block. (Lesson: every config transform must be count-asserted; in a parse-time-validated config no edit is cosmetic.)

3. **Startup race.** `docker inspect` reports `State.Status=running` before the LiteLLM HTTP listener is up. Probes fired in that window return a bare connection error, masking the real state. **Fix:** poll `/health/liveliness` for HTTP 200 before probing.

4. **Ollama bound to `127.0.0.1`.** Host-run ollama defaults to loopback, which is unreachable from the gateway container across the docker bridge -> `Connection refused (111)`. **Fix:** bind `0.0.0.0` via a systemd override: `/etc/systemd/system/ollama.service.d/bind.conf` with `Environment="OLLAMA_HOST=0.0.0.0:11434"`, then `daemon-reload` + restart. Safe ONLY behind network isolation (no inbound path to 11434).

5. **`ollama/` vs `ollama_chat/` endpoint prefix.** `ollama/` routes to ollama's `/api/generate` (legacy completion), which flattens system+messages into one prompt; this version's flattening rejects `claude -p`'s array-form system block ("system message is not in the correct format"). `ollama_chat/` routes to `/api/chat`, which handles structured system/messages natively. **Fix:** use the `ollama_chat/` prefix. (LiteLLM's own docs recommend `ollama_chat`.)

## Verified working config (both litellm/qwen.yaml and litellm/ollama.yaml)
- model: `ollama_chat/qwen3-8b-16k` (chat endpoint + the 16k num_ctx variant)
- api_base: `http://host.docker.internal:11434` (compose provides the extra_host)
- litellm_settings.drop_params: true
- NO general_settings / NO master_key (keyless)

## Result
- T4 employer profile: smoke 8/8 on the stock public artifact (PASS).
- qwen3-8b-16k on the T4: fully in VRAM (7.5 GB), ~36 tok/s, cold-load ~90s.
- Cross-provider seam proven end to end at the API layer AND the webchat UI (plain chat + skill dispatch confirmed in-browser).

## Known limitations (ledgered, not blockers)
- `claude -p` against LiteLLM->ollama can trip a system-message format check on the `/api/generate` path; `ollama_chat` (`/api/chat`) resolves it.
- Local qwen via `ollama_chat` handles chat and skill DISPATCH; autonomous tool EXECUTION is limited (documented LiteLLM<->ollama tool-call parsing issues). Tool-grade judgment is proven on the frontier cloud legs, not the local 8b.
- Any new provider config (e.g. OpenRouter) should be written keyless from the start.
- Deploy-time step (not a committed file): the ollama 0.0.0.0 systemd override.
