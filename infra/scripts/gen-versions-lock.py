#!/usr/bin/env python3
"""Regenerate infra/versions.lock + infra/docker/requirements.txt from live sources.
Fail-loud: any unmet expectation aborts with a traceback; nothing partial is kept."""
import glob, hashlib, json, os, re, subprocess, sys, urllib.request
from datetime import date

NODE_VER = "20.20.2"
CLAUDE_PKG, CLAUDE_VER = "@anthropic-ai/claude-code", "2.1.183"
PY_PKGS = [("openpyxl", "3.1.5"), ("et_xmlfile", "2.0.0"), ("PyYAML", "6.0.1")]
APT_PKGS = ["docker.io", "docker-compose-v2"]

def fetch(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.read().decode()

# -- node: official signed manifest --
node = {}
for line in fetch(f"https://nodejs.org/dist/v{NODE_VER}/SHASUMS256.txt").splitlines():
    m = re.match(rf"([0-9a-f]{{64}})\s+node-v{re.escape(NODE_VER)}-linux-(x64|arm64)\.tar\.xz$", line)
    if m:
        node[m.group(2)] = m.group(1)
assert set(node) == {"x64", "arm64"}, f"node hashes incomplete: {sorted(node)}"

# -- pypi: all published sha256 per pin (wheels + sdist) --
req_blocks, pin_counts = [], []
for name, ver in PY_PKGS:
    files = json.loads(fetch(f"https://pypi.org/pypi/{name}/{ver}/json"))["urls"]
    hashes = sorted({f["digests"]["sha256"] for f in files})
    assert hashes, f"no published files for {name}=={ver}"
    req_blocks.append(f"{name}=={ver} \\\n" + " \\\n".join(f"    --hash=sha256:{h}" for h in hashes))
    pin_counts.append(f"{name}=={ver} ({len(hashes)} hashes)")

# -- cross-check: locally hashed wheels must appear in PyPI's stated set --
joined = "\n".join(req_blocks)
for whl in sorted(glob.glob("/tmp/pipdl/*.whl")):
    h = hashlib.sha256(open(whl, "rb").read()).hexdigest()
    ok = h in joined
    print(f"cross-check {os.path.basename(whl)}: {'MATCH' if ok else 'MISMATCH'}")
    assert ok, f"local hash absent from PyPI set: {whl}"

# -- npm registry integrity for the claude CLI --
integ = subprocess.run(["npm", "view", f"{CLAUDE_PKG}@{CLAUDE_VER}", "dist.integrity"],
                       capture_output=True, text=True, check=True).stdout.strip()
assert integ.startswith("sha512-"), f"unexpected integrity: {integ!r}"

# -- apt: record what is actually installed --
apt = {}
for p in APT_PKGS:
    apt[p] = subprocess.run(["dpkg-query", "-W", "-f=${Version}", p],
                            capture_output=True, text=True, check=True).stdout.strip()
    assert apt[p], f"{p} not installed"

# -- base image digest captured by the docker step --
dig = open("/tmp/ubuntu2404.digest").read().strip()
assert re.match(r"^sha256:[0-9a-f]{64}$", dig), f"bad digest: {dig!r}"

with open("infra/docker/requirements.txt", "w") as f:
    f.write("# Hash-enforced. Install with: pip install --require-hashes -r requirements.txt\n")
    f.write("# Regenerate via infra/scripts/gen-versions-lock.py — do not hand-edit.\n")
    f.write("\n".join(req_blocks) + "\n")

with open("infra/versions.lock", "w") as f:
    f.write(f"""# Keel pinned versions & hashes — single source for every install path.
# Regenerate: python3 infra/scripts/gen-versions-lock.py   (generated {date.today()} on {os.uname().nodename})
NODE_VERSION={NODE_VER}
NODE_SHA256_LINUX_X64={node['x64']}
NODE_SHA256_LINUX_ARM64={node['arm64']}
CLAUDE_CODE_VERSION={CLAUDE_VER}
CLAUDE_CODE_NPM_INTEGRITY={integ}
UBUNTU_BASE_IMAGE=ubuntu:24.04
UBUNTU_BASE_DIGEST={dig}
DOCKER_IO_APT_VERSION={apt['docker.io']}
DOCKER_COMPOSE_V2_APT_VERSION={apt['docker-compose-v2']}
# Python pins live in infra/docker/requirements.txt: {"; ".join(pin_counts)}
# Node deps pinned by webchat/package-lock.json (integrity enforced by npm ci)
""")
print("WROTE infra/versions.lock + infra/docker/requirements.txt")
