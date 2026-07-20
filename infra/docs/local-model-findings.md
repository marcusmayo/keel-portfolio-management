# Local models behind `claude -p` — measured findings (2 vCPU / 8 GiB, CPU-only)

Verdict: no local model is operationally viable behind `claude -p` on this hardware. Local viability requires GPU-class hosting (T4 16GB or better). Cloud providers through the gateway (Gemini, gpt-5) are proven; local is hardware-gated, with the numbers below.

| model | footprint | outcome |
|---|---|---|
| deepseek-r1:1.5b | 1.1 GB | fluent; content wrong; confounded by 4096 default ctx (truncated system prompt) |
| llama3.1:8b | 4.9 GB | rejects thinking params ("does not support thinking") |
| qwen3:8b Q4 | 5.9 GB | loads only via swap on 8 GiB (~442 MiB swapped, one attempt); nonce still grinding past 15 min at ~110% CPU; dual-model contention drove ~47 GB swap reads and wedged the (no-swap) box |
| qwen3:1.7b, num_ctx 16384 | 3.4 GB | fits in RAM; direct generation 5.48 tok/s; `claude -p` nonce failed twice: CLI "Request timed out" at 8m06s, and at 13m54s even with API_TIMEOUT_MS=900000 |

Operational rules learned:
1. Ollama default context is 4096 — far below the `claude -p` system prompt. Always create a variant (FROM model / PARAMETER num_ctx 16384) or the prompt silently truncates.
2. Pin models in gateway mode: the CLI's default model name (observed: claude-opus-4-8 on 2.1.183) will not match alias lists. Set ANTHROPIC_MODEL and ANTHROPIC_SMALL_FAST_MODEL to alias names explicitly.
3. Client timeouts do not stop server-side generation. Ollama keeps grinding after docker/CLI timeouts; recovery is: sudo systemctl restart ollama. Abandoned requests also queue serially ahead of retries.
4. API_TIMEOUT_MS did not rescue slow inference; treat CLI patience as bounded regardless of the env.
5. Thinking models return reasoning in a separate "thinking" field on the ollama API; num_predict can be entirely consumed by thinking with an empty "response". Readers must print both fields.
6. The stock image ships zero swap. Provision an 8G swapfile on the temp disk (/mnt) before any local-model work; without it, exhaustion is a reclaim livelock (SSH dead), not graceful degradation.
7. Self-report and cost are never verification. Ground truth = the gateway's /v1/model/info routing table + a content-bearing nonce.

GPU sizing for the 8B claim: NC4as_T4_v3 (T4 16 GB, ~$0.53/hr, ~$0.18 spot) holds qwen3:8b Q4 + 16k ctx fully in VRAM. Fallbacks: NV12ads_A10_v5 (1/3 A10 ~8 GB, spot ~$0.17 — run 8k ctx), NV18ads_A10_v5 (12 GB), A100 spot as last resort. Quota is per-family per-region.
