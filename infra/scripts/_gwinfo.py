"""Print the gateway's live routing table and the upstream provider prefix.
Ground truth = the running proxy's config, not the model's self-report
(any model will claim to be Claude: the CLI system prompt says it is)."""
import json, sys
d = json.load(sys.stdin)
rows = d.get("data", [])
if not rows:
    print("  (no models -- proxy returned empty)"); sys.exit(1)
provs = set()
for m in rows:
    up = (m.get("litellm_params") or {}).get("model", "?")
    provs.add(up.split("/")[0])
    print(f"  {m.get('model_name'):<28} -> {up}")
print("PROVIDERS=" + ",".join(sorted(provs)))
