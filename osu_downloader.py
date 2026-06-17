import os
import re
import time
import sys
import urllib.request
import urllib.error

REQ_MODE = False
try:
    import requests
    REQ_MODE = True
except ImportError:
    pass

OK, FAIL, SKIP = "\033[92mOK\033[0m", "\033[91mFAILED\033[0m", "\033[94mCACHED\033[0m"
WARN, INFO, RESET = "\033[93m", "\033[95m", "\033[0m"

saved_tty = None
if os.name != 'nt':
    import tty, termios, select
    if sys.stdin.isatty():
        saved_tty = termios.tcgetattr(sys.stdin.fileno())
else:
    import msvcrt
    try: os.system('color')
    except: pass

is_paused = False
is_cancelled = False
exit_now = False

ID_PATTERN = re.compile(r"(?:beatmapsets/|/s/|/download/)(\d+)|^(\d+)$")
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"}


def print_banner():
    print(f"{WARN}======================================================={RESET}\r")
    print(f"{WARN}      osu! Bulk Map Downloader - Quick Start Guide     {RESET}\r")
    print(f"{WARN}======================================================={RESET}\r")
    print("  [P] Pause/Resume : Pause current download instantly.\r\n"
          "  [C] Cancel Map   : Skip current map and delete temp file.\r\n"
          "  [Q] Quit Script  : Exit safely without corrupting files.\r")
    print(f"{WARN}======================================================={RESET}\r\n")


def check_io():
    global is_paused, is_cancelled, exit_now

    if os.name == 'nt':
        try:
            if not msvcrt.kbhit(): return
            ch = msvcrt.getch()
            if ch in (b'\x00', b'\xe0'):
                msvcrt.getch()
                return
            ch = ch.decode('utf-8', errors='ignore').lower()
        except: return
    else:
        if not (sys.stdin and sys.stdin.isatty()): return
        try:
            r, _, _ = select.select([sys.stdin], [], [], 0.001)
            if not r: return
            ch = sys.stdin.read(1).lower()
        except: return

    if ch == 'p':
        is_paused = not is_paused
        print(f"\r\n{INFO}==> PAUSED. Press 'P' to resume...\r" if is_paused else f"\r\n{INFO}==> RESUMED.\r")
    elif ch == 'c':
        is_cancelled = True
        print(f"\r\n{INFO}==> Cancelling current download...\r")
    elif ch == 'q':
        exit_now = True
        is_cancelled = True
        print(f"\r\n{INFO}==> Exiting safely...\r")


def req_stream(session, url, tmp):
    global is_paused, is_cancelled
    with session.get(url, headers=UA, timeout=8, stream=True) as res:
        if res.status_code != 200: return False, f"HTTP {res.status_code}"
        with open(tmp, "wb") as f:
            for chunk in res.iter_content(chunk_size=1024):
                check_io()
                while is_paused and not is_cancelled:
                    check_io()
                    time.sleep(0.02)
                if is_cancelled: return False, "Cancelled"
                if chunk: f.write(chunk)
    return True, "OK"


def url_stream(opener, url, tmp):
    global is_paused, is_cancelled
    req = urllib.request.Request(url, headers=UA)
    with opener.open(req, timeout=10) as res:
        sock = res.fp.raw._sock if hasattr(res, 'fp') and hasattr(res.fp, 'raw') else None
        if sock: sock.settimeout(5.0)
        with open(tmp, "wb") as f:
            while True:
                check_io()
                while is_paused and not is_cancelled:
                    check_io()
                    time.sleep(0.02)
                if is_cancelled: return False, "Cancelled"
                try: chunk = res.read(1024)
                except: raise TimeoutError("Stalled")
                if not chunk: break
                f.write(chunk)
    return True, "OK"


def exec_dl(backend, map_id, path):
    global is_paused, is_cancelled
    mirrors = [
        f"https://api.nerinyan.moe/d/{map_id}",
        f"https://txy1.sayobot.cn/beatmaps/download/full/{map_id}"
    ]
    tmp = path + ".part"
    err = "Unknown error"

    for url in mirrors:
        if is_cancelled: break
        for r in range(3):
            if is_cancelled: break
            while is_paused and not is_cancelled:
                check_io()
                time.sleep(0.02)
            if is_cancelled: break

            try:
                success, msg = req_stream(backend, url, tmp) if REQ_MODE else url_stream(backend, url, tmp)
                if not success:
                    err = msg
                    if "404" in msg: break
                    continue

                if os.path.exists(tmp) and os.path.getsize(tmp) < 2048:
                    err = "Invalid File"
                    os.remove(tmp)
                    break

                if os.path.exists(path): os.remove(path)
                os.replace(tmp, path)
                return True, "OK"

            except Exception as e:
                err = "Stalled" if "stalled" in str(e).lower() else type(e).__name__
                if os.path.exists(tmp):
                    try: os.remove(tmp)
                    except: pass
                if r < 2 and not is_cancelled:
                    time.sleep(1)
                    continue
                else: break
    return False, "Cancelled" if is_cancelled else f"Failed ({err})"


def main():
    global is_cancelled, exit_now
    if os.name != 'nt' and saved_tty and sys.stdin.isatty():
        tty.setcbreak(sys.stdin.fileno())

    try:
        print_banner()
        if not os.path.exists("links.txt"):
            if os.name != 'nt' and saved_tty and sys.stdin.isatty():
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, saved_tty)
            print("Error: links.txt missing.\r")
            return

        os.makedirs("downloaded_maps", exist_ok=True)
        with open("links.txt", "r", encoding="utf-8") as f:
            urls = list(dict.fromkeys(ln.strip() for ln in f if ln.strip()))

        total = len(urls)
        print(f"Found {total} links. Running via {'requests' if REQ_MODE else 'urllib'}...\r\n")
        backend = requests.Session() if REQ_MODE else urllib.request.build_opener(urllib.request.HTTPCookieProcessor())

        for idx, url in enumerate(urls, 1):
            if exit_now: break
            is_cancelled = False

            m = ID_PATTERN.search(url.strip())
            map_id = (m.group(1) or m.group(2)) if m else None
            if not map_id:
                print(f"[{idx}/{total}] {WARN}Invalid:{RESET} {url}\r")
                continue

            file_path = os.path.join("downloaded_maps", f"{map_id}.osz")
            if os.path.exists(file_path):
                print(f"[{idx}/{total}] Map {map_id} -> {SKIP}\r")
                continue

            print(f"[{idx}/{total}] Downloading {map_id}...\r")
            success, reason = exec_dl(backend, map_id, file_path)
            print(f"-> Status: {OK}\r\n" if success else f"-> Status: {FAIL} ({reason})\r\n")
            if not success and exit_now: break

        if REQ_MODE: backend.close()
        print("Done.\r")

    except Exception as e:
        if os.name != 'nt' and saved_tty and sys.stdin.isatty():
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, saved_tty)
        print(f"\nRuntime Error: {e}\r")
    finally:
        if os.name != 'nt' and saved_tty and sys.stdin.isatty():
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, saved_tty)


if __name__ == "__main__":
    main()
