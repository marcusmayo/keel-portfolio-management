# Keel

Single-operator portfolio management: deterministic Python tools, YAML state,
Excel round-trip review, with an LLM reserved for genuine semantic judgment
only. Keel reconciles work items from external sources (Jira exports, backlog
spreadsheets) against a canonical portfolio, proposes changes, and leaves every
mutation to the operator. It runs as a single pinned container -- self-contained
via Docker Compose on any Docker host, or on Azure via the Bicep templates in
`infra/`.

## Architecture

The pipeline is deterministic-first, with one optional LLM lane:

    sources (Jira CSV, backlog xlsx)
        |  normalize            deterministic field mapping -> canonical proposals
        v
    reconcile                   overlap-coefficient matching vs state/*.yaml
        |                       buckets: changed / gap / conflict / ambiguous /
        |                                duplicate / completed / done_gap
        |  semantic pass        OPTIONAL: LLM judges only the ambiguous bucket
        v                       (SAME/DISTINCT, annotated in place -- never moved)
    score                       WSJF / RICE: LLM proposes factors, pure math computes
        |
        v
    export                      multi-sheet Excel for operator round-trip review

Everything above the semantic pass runs without any model. The LLM appears in
exactly two places -- judging ambiguous matches and proposing scoring factors --
and in both, a deterministic validator owns the result. State lives in plain
YAML under `state/`; knowledge (stakeholder pages, inbox artifacts) under
`knowledge/`. The operator surface is a TOTP-protected webchat (Node/Express)
that dispatches skills via `claude -p`.

## Design principles

- Deterministic first. If arithmetic or string matching can decide, no model is
  consulted. The reconciler's buckets are reproducible byte-for-byte.
- Propose, don't mutate. Skills write proposals; the operator commits. Deletes
  are operator-explicit only -- no tool path performs them.
- Structural boundaries over behavioral rules. Guarantees are enforced by what
  the tooling *cannot* do, not by policy text. Two examples in this repo: the
  employer deploy profile hard-aborts if a Tailscale key is present in the
  environment (an employer VM structurally cannot join a personal tailnet), and
  the LLM gateway has no host port (nothing outside the compose network can
  reach it). This can't-versus-shouldn't split at the tool level is the
  Can't/Shouldn't Framework applied to infrastructure.
- Provenance at decision time. Reconciliation verdicts, scoring inputs, and
  image-egress events are recorded when they happen; re-running a model produces
  a new answer, not the original decision.
- Source of record is explicit. External systems (Jira) own status truth;
  Keel reconciles against them rather than silently overwriting.

## Requirements

- Any Docker host (self-contained path), or an Azure subscription + `az` CLI
  (cloud paths).
- An Anthropic API key -- or a gateway provider key (see Model selection).
- A Tailscale account for the personal cloud profile only.

## Quickstart -- self-contained (any Docker host)

    git clone https://github.com/marcusmayo/keel-portfolio-management.git ~/keel
    cd ~/keel
    ./infra/scripts/build-image.sh        # builds keel:latest, tagged with the git SHA
    ./infra/scripts/bootstrap.sh          # TOTP enrollment + API key prompt -> compose up + smoke

`bootstrap.sh` creates `infra/docker/keel.env` itself (mode 600) -- do not copy
`keel.env.example`, which only documents the variables. It enrolls a TOTP secret
(scan the QR into your authenticator), prompts for the Anthropic key with input
hidden, starts the container, and runs the 8-check smoke test.

Publish address: if the host is joined to a tailnet, the webchat binds to the
tailnet IP; otherwise it binds to `127.0.0.1:8443` -- reach it locally or over
an SSH tunnel (`ssh -L 8443:127.0.0.1:8443 user@host`).

## Azure deployment -- personal profile (Tailscale)

The personal profile creates a VM with no public IP and a deny-all inbound NSG;
the only path in is your tailnet (WireGuard). Cloud-init installs Docker and
Tailscale, joins the tailnet, clones this repo, and builds the image.

1. Generate a Tailscale pre-auth key (admin console): reusable OFF, ephemeral
   OFF, short expiry -- it is consumed once at boot.
2. From a clone of this repo:

       export TAILSCALE_AUTH_KEY=tskey-...
       export KEEL_SSH_PUBKEY="$(cat ~/.ssh/your_key.pub)"
       export KEEL_LOCATION=eastus2          # optional; default eastus2
       export KEEL_RG=keel-personal-rg       # optional
       ./infra/scripts/deploy.sh personal

3. Watch for the node on your tailnet, SSH in as `keeladmin`, and wait for the
   image build: `sudo tail -f /var/log/keel-image-build.log` (ends with
   `BUILT keel:<sha>`).
4. Run `./infra/scripts/bootstrap.sh` (TOTP + key + compose up + smoke), then
   open `http://<tailnet-ip>:8443`.

Notes: the default VM size is `Standard_B2s_v2` -- if validation fails with
`QuotaExceeded` on the Bsv2 family, check `az vm list-usage` for a region where
you have Bsv2 quota and redeploy with `KEEL_LOCATION` set there. Region does not
matter for a tailnet-only box. If a node named `keel-vm` already exists on the
tailnet, the new node auto-suffixes (`keel-vm-1`); rename it in the admin
console after removing the old node.

## Azure deployment -- employer profile (no tailnet)

For running Keel inside an employer network without touching personal
infrastructure. No Tailscale: `deploy.sh employer` aborts if
`TAILSCALE_AUTH_KEY` is even set in the environment. Reachability is SSH only,
restricted to the CIDR you supply; the webchat stays on loopback (use an SSH
tunnel).

    export KEEL_SSH_CIDR=203.0.113.7/32     # or your corporate range
    export KEEL_SSH_PUBKEY="$(cat ~/.ssh/your_key.pub)"
    ./infra/scripts/deploy.sh employer

Then SSH from the allowed CIDR, wait for the image build, run `bootstrap.sh`,
and tunnel to `127.0.0.1:8443`. No secrets transit cloud-init in either profile;
the operator injects them at bootstrap.

## Verification

Smoke (run automatically by bootstrap, re-runnable anytime):

    ./infra/scripts/smoke-test.sh keel-webchat "http://<addr>:8443"

Eight checks: node, claude CLI, openpyxl, pyyaml, container health, HTTP,
zero residue, state writable.

### Running the demo

The Northwind end-to-end demo runs the full reconciliation pipeline against a
synthetic corpus and verifies every step against a ground-truth oracle (29
checks, including a deliberately planted ambiguous paraphrase that must land in
the ambiguous bucket and be judged by the semantic pass). It runs INSIDE the
container -- where the Python deps and the `claude` CLI resolve -- not on the
host (a host guard will stop you with the correct command):

    docker exec -w /app keel-webchat bash run_e2e.sh --yes

`--yes` clears the destructive-demo guard: the demo overwrites
`keel.config.json`, reseeds the corpus, and drafts demo items into `state/`.
Run it on a fresh deployment, before loading real data. Reset with
`bash clean_demo.sh --yes` (also in-container).

From the webchat, the same demo is available as a confirm-gated command: type
`/run-e2e` to read the warning, then `/run-e2e confirm` to execute. Step 9
calls the LLM and can take 30-60s on cloud providers; the chat waits.

## Using Keel

Log in at `http://<addr>:8443` with a TOTP code. Plain messages go to the model
with portfolio context; slash commands dispatch skills. Attachments can be
uploaded for triage; images sent for interpretation are described via a direct
Anthropic call with the egress audited before the request is made.

Skills (`.claude/commands/`):

Intake and triage
- `/inbox` -- show documents staged for triage, not yet processed
- `/classify` -- read-only routing proposal for each staged artifact
- `/process` -- batch-triage the inbox and graduate each artifact
- `/triage` -- process an owner-authored note or transcript into the portfolio
- `/draft-item` -- author description + acceptance criteria for a work item
- `/decompose` -- break an epic into features, or a feature into stories

Normalization and reconciliation
- `/normalize-jira` -- map a Jira CSV export into canonical proposals (read-only)
- `/normalize-backlog` -- map a backlog xlsx into canonical proposals (read-only)
- `/reconcile` -- five-bucket comparison of proposals vs the portfolio (read-only)

Scoring and planning
- `/suggest-score` -- propose WSJF/RICE components for operator review
- `/roadmap` -- hierarchical roadmap from state/*.yaml
- `/pipeline` -- prioritized portfolio status

Reporting and status
- `/briefing` -- decision-readiness briefing
- `/digest` -- daily activity rollup (today or any past day)
- `/weekly` -- weekly operating priorities and performance report
- `/status` -- update a work item's status (proposal -> operator confirm)
- `/portfolio-health` -- cross-check consistency, report mismatches
- `/show` -- display a single work item in full

Knowledge
- `/knowledge` -- what context Keel has for grounding
- `/people` -- everything known about a stakeholder
- `/draft` -- compose a communication in the operator's voice

Exports: the webchat's Export portfolio and Export multi-source buttons produce
Excel workbooks; multi-source carries six sheets (Cross-Source, Source-Only,
Keel-Origin, Unconfirmed, Semantic Matches, Legend) for round-trip review.

## Model selection (gateway mode)

By default `claude -p` calls Anthropic directly using `ANTHROPIC_API_KEY`. To run
chat and skills on a cheaper or non-Anthropic model, route `claude -p` through the
bundled LiteLLM gateway. The gateway has no host port -- it is reachable only on the
internal compose network -- so provider configs run keyless: the network boundary is
the control, not a proxy key.

`LITELLM_CONFIG` selects the gateway config and is a compose-time shell variable,
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
`infra/docs/gateway-findings.md` for the LiteLLM >=1.92 keyless rationale and
`infra/docs/local-model-findings.md` for the local-GPU leg.

## Data persistence

Application state lives in four named Docker volumes (`keel-state`,
`keel-knowledge`, `keel-logs`, `keel-support`), mounted at `/app/state`,
`/app/knowledge`, `/app/logs`, and `/app/support`. The image is code; the volumes
are state. Data written there survives container restarts, `docker compose down`,
and VM reboots. It is destroyed only by `docker compose down -v`, an explicit
`docker volume rm`, or deleting the VM.

## Security posture

- Personal profile: no public IP, deny-all inbound NSG; transport is your
  tailnet (WireGuard). Employer profile: SSH scoped to one CIDR, webchat on
  loopback, and a structural guard against tailnet membership.
- Webchat auth is TOTP; `keel.env` is created mode 600 and never committed.
- No secrets transit cloud-init; the pre-auth key used at boot is scrubbed from
  cloud-init artifacts.
- The LLM gateway is keyless by design and unreachable from outside the compose
  network.
- Outbound image interpretation is audited before egress (model, hash,
  attestation recorded).

## Repository layout

    tools/               deterministic pipeline (normalize, reconcile, score, export)
    .claude/commands/    the 21 skills dispatched by the webchat
    webchat/             Node/Express operator surface (TOTP, skills, exports)
    examples/northwind/  synthetic demo corpus generator
    system/              operator + voice profiles
    infra/               Bicep (personal/employer), cloud-init, compose, LiteLLM
                         configs, scripts (deploy, bootstrap, smoke, verify-gateway),
                         findings docs
    run_e2e.sh           10-step demo pipeline (in-container; oracle-verified)
    clean_demo.sh        reset the demo to a clean state

## License

Apache-2.0. Author: Marcus Mayo -- X: [@MarcusMayoAI](https://x.com/MarcusMayoAI)
-- GitHub: [marcusmayo](https://github.com/marcusmayo)
-- LinkedIn: [marcusmayo](https://www.linkedin.com/in/marcusmayo/)

