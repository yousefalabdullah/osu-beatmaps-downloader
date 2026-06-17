import os
import re
import time
import sys
import threading
import urllib.request
import urllib.error

COLORS = {
    "ok": "\033[92mOK\033[0m",
    "failed": "\033[91mFAILED\033[0m",
    "cached": "\033[94mCACHED (Skipped)\033[0m",
    "invalid": "\033[93mInvalid URL format:\033[0m",
    "start": "\033[96mFound {total} links. Starting downloads...\033[0m",
    "reason": "\033[93m(Reason: {reason})\033[0m",
    "info": "\033[95m",
    "menu": "\033[92m",
    "reset": "\033[0m"
}

if os.name == 'nt':
    import msvcrt
    os.system('')
else:
    import tty
    import termios
    import select

# Dynamically resolve paths relative to the script's actual location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LINKS_FILE = os.path.join(SCRIPT_DIR, "links.txt")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "downloaded_maps")

MAX_RETRIES = 3
RETRY_DELAY = 1

is_paused = False
is_cancelled = False
exit_program = False


def print_welcome_menu():
    border = "=" * 55
    print(f"{COLORS['menu']}{border}")
    print(f"{COLORS['menu']}      osu! Bulk Map Downloader - Quick Start Guide")
    print(f"{COLORS['menu']}{border}")
    print("  [P] Pause/Resume : Pause the current download instantly.")
    print("                     Press 'P' again to resume.")
    print("  [C] Cancel Map   : Stop downloading the current map, delete")
    print("                     the partial file, and skip to the next.")
    print("  [Q] Quit Script  : Safely terminate the downloader without")
    print("                     leaving corrupted or half-downloaded files.")
    print(f"{COLORS['menu']}{border}\n")


def get_ch():
    if os.name == 'nt':
        try:
            if msvcrt.kbhit():
                return msvcrt.getch().decode('utf-8', errors='ignore').lower()
        except:
            return None
    else:
        if sys.stdin.isatty():
            try:
                rlist, _, _ = select.select([sys.stdin], [], [], 0.05)
                if rlist:
                    fd = sys.stdin.fileno()
                    old_settings = termios.tcgetattr(fd)
                    try:
                        tty.setraw(fd)
                        ch = sys.stdin.read(1)
                    finally:
                        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                    return ch.lower()
            except:
                return None
    return None


def listen_keyboard():
    global is_paused, is_cancelled, exit_program
    while not exit_program:
        ch = get_ch()
        if ch == 'p':
            is_paused = not is_paused
            print(f"\r\n{COLORS['info']}==> PAUSED. Press 'P' to resume...\r" if is_paused else f"\r\n{COLORS['info']}==> RESUMED.\r")
        elif ch == 'c':
            is_cancelled = True
            print(f"\r\n{COLORS['info']}==> Cancelling current download...\r")
        elif ch == 'q':
            exit_program = True
            is_cancelled = True
            print(f"\r\n{COLORS['info']}==> Exiting safely...\r")
        time.sleep(0.05)


def get_map_id(url):
    match = re.search(r"(?:beatmapsets/|/s/|/download/)(\d+)|^(\d+)$", url.strip())
    if not match: 
        return None
    return match.group(1) or match.group(2)


def download_set(opener, map_id, file_path):
    global is_paused, is_cancelled
    
    mirrors = [
        f"https://api.nerinyan.moe/d/{map_id}",
        f"https://txy1.sayobot.cn/beatmaps/download/full/{map_id}",
    ]
    
    temp_path = file_path + ".part"
    error_reason = "Unknown error"

    for url in mirrors:
        if is_cancelled: break
        
        for attempt in range(1, MAX_RETRIES + 1):
            if is_cancelled: break
            
            try:
                req = urllib.request.Request(
                    url, 
                    headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
                )
                
                with opener.open(req, timeout=20) as res:
                    with open(temp_path, "wb") as f:
                        while True:
                            while is_paused and not is_cancelled:
                                time.sleep(0.2)
                            
                            if is_cancelled:
                                f.close()
                                if os.path.exists(temp_path):
                                    os.remove(temp_path)
                                return False, "Cancelled by user"

                            chunk = res.read(65536)
                            if not chunk:
                                break
                            f.write(chunk)
                
                if os.path.exists(temp_path) and os.path.getsize(temp_path) < 2048:
                    error_reason = "Invalid Map / Not Found"
                    os.remove(temp_path)
                    break

                if os.path.exists(file_path):
                    os.remove(file_path)
                os.replace(temp_path, file_path)
                return True, "OK"

            except urllib.error.HTTPError as e:
                error_reason = f"HTTP {e.code}"
                if e.code == 404:
                    error_reason = "404 Not Found"
                    break
            except Exception as e:
                error_reason = type(e).__name__
                if os.path.exists(temp_path):
                    try: os.remove(temp_path)
                    except: pass
                
                if attempt < MAX_RETRIES and not is_cancelled:
                    time.sleep(RETRY_DELAY)
                    continue
                else:
                    break 

    return False, "Cancelled by user" if is_cancelled else f"Failed on all mirrors ({error_reason})"


def main():
    global is_cancelled, exit_program
    
    print_welcome_menu()

    if not os.path.exists(LINKS_FILE):
        print(f"Error: 'links.txt' not found in the script directory.\r")
        print(f"Expected path: {LINKS_FILE}\r")
        print("\nPress ENTER to close...")
        input()
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(LINKS_FILE, "r", encoding="utf-8") as f:
        urls = list(dict.fromkeys(line.strip() for line in f if line.strip()))

    total = len(urls)
    
    if total == 0:
        print(f"Notice: 'links.txt' is empty. Nothing to download.\r")
        print("\nPress ENTER to close...")
        input()
        return

    print(COLORS['start'].format(total=total) + "\r\n")

    threading.Thread(target=listen_keyboard, daemon=True).start()
    
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())

    for idx, url in enumerate(urls, 1):
        if exit_program:
            break

        is_cancelled = False
        map_id = get_map_id(url)
        
        if not map_id:
            print(f"[{idx}/{total}] {COLORS['invalid']} {url}\r")
            continue

        file_path = os.path.join(OUTPUT_DIR, f"{map_id}.osz")

        if os.path.exists(file_path):
            print(f"[{idx}/{total}] Map {map_id} -> {COLORS['cached']}\r")
            continue

        print(f"[{idx}/{total}] Fetching map {map_id}... ", end="", flush=True)
        success, reason = download_set(opener, map_id, file_path)
        
        if success:
            print(COLORS['ok'] + "\r")
            time.sleep(0.2)
        else:
            print(f"{COLORS['failed']} -> {COLORS['reason'].format(reason=reason)}\r")
            if exit_program:
                break

    print("\nDone. Press ENTER to exit...\r")
    input()


if __name__ == "__main__":
    main()
