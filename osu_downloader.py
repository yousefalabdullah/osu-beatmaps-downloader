import os
import re
import time
import requests

LINKS_FILE = "links.txt"
OUTPUT_DIR = "downloaded_maps"


def get_map_id(url):
    match = re.search(r"(?:beatmapsets|s|download)/(\d+)", url)
    return match.group(1) if match else None


def download_set(map_id, file_path):
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    }

    # Order of preference for mirrors
    mirrors = [
        f"https://api.nerinyan.moe/d/{map_id}",
        f"https://txy1.sayobot.cn/beatmaps/download/full/{map_id}",
    ]

    for url in mirrors:
        try:
            res = requests.get(url, headers=headers, stream=True, timeout=30)
            if res.status_code == 200:
                with open(file_path, "wb") as f:
                    for chunk in res.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True
        except requests.exceptions.RequestException:
            continue  # Try next mirror if network drops
    return False


def main():
    if not os.path.exists(LINKS_FILE):
        print(f"Error: Missing {LINKS_FILE}")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(LINKS_FILE, "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    total = len(urls)
    print(f"Found {total} links. Starting downloads...")

    for idx, url in enumerate(urls, 1):
        map_id = get_map_id(url)
        if not map_id:
            print(f"[{idx}/{total}] Invalid URL format: {url}")
            continue

        file_path = os.path.join(OUTPUT_DIR, f"{map_id}.osz")

        if os.path.exists(file_path):
            print(f"[{idx}/{total}] Map {map_id} cached. Skipping.")
            continue

        print(f"[{idx}/{total}] Fetching map {map_id}... ", end="", flush=True)

        if download_set(map_id, file_path):
            print("OK")
            time.sleep(1)
        else:
            print("FAILED")


if __name__ == "__main__":
    main()
