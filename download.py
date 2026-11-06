"""Download the Unity data files of the current RotMG Exalt build from Deca's CDN."""

import argparse
import gzip
import hashlib
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

# Public launcher endpoint; the key is a fixed value shipped with the launcher, not a secret.
INIT_URL = "https://www.realmofthemadgod.com/app/init?platform=standalonewindows64&key=9KnJFxtTvLu2frXv"
USER_AGENT = "rotmg-data"

# The game XML, the sprite index and the sprite atlases are all in resources.assets.
WANTED = re.compile(r"^RotMG Exalt_Data/(globalgamemanagers.*|resources\.assets.*)$")


def fetch(url: str, data: bytes | None = None) -> bytes:
    req = urllib.request.Request(url, data=data, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def build_info() -> dict[str, str]:
    xml = fetch(INIT_URL, data=b"").decode()
    info = dict(re.findall(r"<(Build\w+)>([^<]*)</\1>", xml))
    for key in ("BuildCDN", "BuildHash", "BuildId", "BuildVersion"):
        if key not in info:
            raise RuntimeError(f"{key} missing from app/init response")
    return info


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out", type=Path, nargs="?", help="target directory; a subfolder per build version is created")
    parser.add_argument("--version", action="store_true", help="only print the current build version")
    args = parser.parse_args()

    info = build_info()
    if args.version:
        print(info["BuildVersion"])
        return
    if args.out is None:
        parser.error("out is required")
    base = f"{info['BuildCDN']}{info['BuildHash']}/{info['BuildId']}/"
    manifest = json.loads(fetch(base + "checksum.json"))
    files = [f for f in manifest["files"] if WANTED.match(f["file"])]

    target = args.out / info["BuildVersion"]
    print(f"build {info['BuildVersion']} (hash {info['BuildHash']}): {len(files)} files -> {target}")

    for entry in files:
        data = gzip.decompress(fetch(base + urllib.parse.quote(entry["file"]) + ".gz"))
        if hashlib.md5(data).hexdigest() != entry["checksum"]:
            raise RuntimeError(f"checksum mismatch for {entry['file']}")
        dest = target / entry["file"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        print(f"  {entry['file']} ({dest.stat().st_size:,} bytes)")

    (target / "build.json").write_text(json.dumps(info, indent=2))


if __name__ == "__main__":
    main()
