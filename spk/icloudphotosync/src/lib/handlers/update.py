import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
import config_manager

GITHUB_REPO = "Euphonique/iCloudPhotoSync"
GITHUB_API_URL = "https://api.github.com/repos/%s/releases/latest" % GITHUB_REPO
CACHE_FILE = os.path.join(config_manager.PKG_VAR, "update_cache.json")
CACHE_TTL = 3600


def _read_pkg_version():
    info_path = "/var/packages/iCloudPhotoSync/INFO"
    try:
        with open(info_path, "r") as f:
            for line in f:
                if line.startswith("version="):
                    return line.split("=", 1)[1].strip().strip('"')
    except (OSError, IOError):
        pass
    return "0.0.0"


def _parse_version(v):
    try:
        return tuple(int(x) for x in v.lstrip("v").split(".")[:3])
    except (ValueError, AttributeError):
        return (0, 0, 0)


def _fetch_latest_release():
    import requests
    resp = requests.get(
        GITHUB_API_URL,
        headers={"Accept": "application/vnd.github.v3+json"},
        timeout=15,
    )
    if resp.status_code != 200:
        return None
    data = resp.json()
    tag = data.get("tag_name", "")
    version = tag.lstrip("v")
    body = data.get("body", "")
    published = data.get("published_at", "")
    spk_url = ""
    for asset in data.get("assets", []):
        name = asset.get("name", "")
        if name.endswith(".spk"):
            spk_url = asset.get("browser_download_url", "")
            break
    return {
        "version": version,
        "tag": tag,
        "notes": body,
        "published": published,
        "spk_url": spk_url,
    }


def _get_cached():
    try:
        with open(CACHE_FILE, "r") as f:
            cache = json.load(f)
        if time.time() - cache.get("ts", 0) < CACHE_TTL:
            return cache.get("data")
    except (OSError, IOError, ValueError):
        pass
    return None


def _save_cache(data):
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump({"ts": time.time(), "data": data}, f)
    except (OSError, IOError):
        pass


def _check(force=False):
    if not force:
        cached = _get_cached()
        if cached:
            current = _read_pkg_version()
            cached["current_version"] = current
            cached["update_available"] = _parse_version(cached["version"]) > _parse_version(current)
            return cached

    release = _fetch_latest_release()
    if not release:
        return None
    _save_cache(release)
    current = _read_pkg_version()
    release["current_version"] = current
    release["update_available"] = _parse_version(release["version"]) > _parse_version(current)
    return release


def handle(params):
    action = params.getvalue("action", "check")

    if action == "check":
        force = params.getvalue("force", "0") == "1"
        info = _check(force=force)
        if info is None:
            return {"success": False, "error": {"code": 200, "message": "Could not reach GitHub"}}
        return {"success": True, "data": info}

    return {"success": False, "error": {"code": 101, "message": "Unknown action"}}
