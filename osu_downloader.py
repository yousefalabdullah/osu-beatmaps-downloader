import os
import re
import time
import sys
import threading
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor

THEME = {
    "ok": "\033[92mOK\033[0m",
    "failed": "\033[91mFAILED\033[0m",
    "cached": "\033[94mCACHED\033[0m",
    "invalid": "\033[93mInvalid URL:\033[0m",
    "start": "\033[96mFound {total} links. Processing slots...\033[0m",
    "reason": "\033[93m({reason})\033[0m",
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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, "links.txt")
SAVE_DIR = os.path.join(BASE_DIR, "downloaded_maps")

CONCURRENT_LIMIT = 4
RETRIES = 2
DELAY = 1

paused = False
stop_flag = False
done_count = 0
state_lock = threading.Lock()

logs = []
slot_view = {i: "Idle..." for i in range(CONCURRENT_LIMIT)}


def draw_header():
    line = "=" * 55
    out = [
        f"{THEME['menu']}{line}",
        f"            osu! Downloader      ",
        f"{line}",
        f"  [P] Pause/Resume | [Q] Quit Script",
        f"{line}{THEME['reset']}"
    ]
    return "\n".join(out) + "\n"


def clear_keys():
    if os.name == 'nt':
        while msvcrt.kbhit():
            msvcrt.getch()
    else:
        try:
            while select.select([sys.stdin], [], [], 0.0)[0]:
                sys.stdin.read(1)
        except: pass


def read_key():
    if os.name == 'nt':
        try:
            if msvcrt.kbhit():
                return msvcrt.getch().decode('utf-8', errors='ignore').lower()
        except: return None
    else:
        if sys.stdin.isatty():
            fd = sys.stdin.fileno()
            try: old = termios.tcgetattr(fd)
            except: return None
            try:
                tty.setcbreak(fd)
                r, _, _ = select.select([sys.stdin], [], [], 0.05)
                if r:
                    return sys.stdin.read(1).lower()
            except: return None
            finally:
                try: termios.tcsetattr(fd, termios.TCSADRAIN, old)
                except: pass
    return None


def input_listener():
    global paused, stop_flag
    while not stop_flag:
        key = read_key()
        if key == 'p':
            paused = not paused
            clear_keys()
        elif key == 'q':
            stop_flag = True
        time.sleep(0.02)


def parse_id(link):
    m = re.search(r"(?:beatmapsets/|/s/|/download/)(\d+)|^(\d+)$", link.strip())
    if not m: return None
    return m.group(1) or m.group(2)


def run_download(client, map_id, dest, slot_idx, current_idx, total):
    global paused, stop_flag
    if stop_flag: return False, "Interrupted"
    if os.path.exists(dest): return True, "CACHED"

    endpoints = [
        f"https://api.nerinyan.moe/d/{map_id}",
        f"https://txy1.sayobot.cn/beatmaps/download/full/{map_id}",
    ]

    part_file = dest + ".part"
    fail_msg = "Error"

    for link in endpoints:
        if stop_flag: break
        for run in range(1, RETRIES + 1):
            if stop_flag: break
            try:
                request = urllib.request.Request(link)
                request.add_header("User-Agent", "Mozilla/5.0")
                request.add_header("Connection", "keep-alive")

                with client.open(request, timeout=12) as response:
                    size = response.getheader('Content-Length')
                    size = int(size) if size else None
                    got = 0
                    t0 = time.time()

                    with open(part_file, "wb") as f:
                        while True:
                            while paused and not stop_flag:
                                time.sleep(0.2)
                                t0 = time.time() - (got / (rate if 'rate' in locals() and rate > 0 else 1))

                            if stop_flag:
                                f.close()
                                if os.path.exists(part_file): os.remove(part_file)
                                return False, "Interrupted"

                            chunk = response.read(65536)
                            if not chunk: break
                            f.write(chunk)
                            got += len(chunk)

                            dt = time.time() - t0
                            if dt > 0:
                                rate = got / dt
                                mb_s = rate / 1048576
                                mb_got = got / 1048576

                                if size:
                                    mb_total = size / 1048576
                                    mb_remaining = mb_total - mb_got
                                    pct = (got / size) * 100
                                    with state_lock:
                                        slot_view[slot_idx] = f"Slot {slot_idx+1} -> [{current_idx}/{total}] Map {map_id}: {pct:5.1f}% ({mb_got:.1f}/{mb_total:.1f} MB, Rem: {mb_remaining:.1f} MB) @ {mb_s:5.2f} MB/s"
                                else:
                                    with state_lock:
                                        slot_view[slot_idx] = f"Slot {slot_idx+1} -> [{current_idx}/{total}] Map {map_id}: {mb_got:.1f} MB Loaded @ {mb_s:5.2f} MB/s"

                if os.path.exists(part_file) and os.path.getsize(part_file) < 2048:
                    fail_msg = "Empty File"
                    if os.path.exists(part_file): os.remove(part_file)
                    break

                if os.path.exists(dest): os.remove(dest)
                os.replace(part_file, dest)
                return True, "OK"

            except urllib.error.HTTPError as e:
                fail_msg = f"HTTP {e.code}"
                if e.code == 404: break
            except Exception as e:
                fail_msg = type(e).__name__
                if os.path.exists(part_file):
                    try: os.remove(part_file)
                    except: pass
                if run < RETRIES and not stop_flag:
                    time.sleep(DELAY)
                    continue
                else: break

    return False, fail_msg


def ui_loop(total):
    global stop_flag, done_count, paused
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()

    while not stop_flag:
        frame = []
        frame.append(draw_header())

        if paused:
            frame.append(f"{THEME['info']}==== DOWNLOADS PAUSED. PRESS 'P' TO RESUME ===={THEME['reset']}\n")
        else:
            frame.append("Status: Running...\n")

        frame.append("--- Log ---")
        with state_lock:
            for row in logs[-8:]:
                frame.append(row)
        frame.append("-----------\n")

        frame.append("--- Channels ---")
        with state_lock:
            for i in range(CONCURRENT_LIMIT):
                frame.append(slot_view[i])
        frame.append("----------------")

        frame.append(f"\n[Progress: {done_count}/{total}]")

        out_str = "\033[H" + "\n".join(f"\033[K{line}" for line in frame)
        sys.stdout.write(out_str)
        sys.stdout.flush()
        time.sleep(0.25)


def main():
    global done_count, stop_flag

    if not os.path.exists(FILE_PATH):
        sys.stdout.write("\033[2J\033[H")
        print(draw_header())
        print(f"Missing text file: {FILE_PATH}\n")
        input("Press Enter to close...")
        return

    os.makedirs(SAVE_DIR, exist_ok=True)

    with open(FILE_PATH, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    seen = set()
    cleaned_urls = []
    for u in lines:
        if u not in seen:
            seen.add(u)
            cleaned_urls.append(u)

    job_list = []
    for u in cleaned_urls:
        mid = parse_id(u)
        if mid:
            target = os.path.join(SAVE_DIR, f"{mid}.osz")
            if os.path.exists(target):
                logs.append(f"Map {mid} -> {THEME['cached']}")
                done_count += 1
            else:
                job_list.append((mid, target))
        else:
            logs.append(f"{THEME['invalid']} {u}")

    total_jobs = len(job_list) + done_count

    if len(job_list) == 0:
        sys.stdout.write("\033[2J\033[H")
        print(draw_header())
        print("--- Log Summary ---")
        for row in logs: print(row)
        input(f"\nAll files cached. Press Enter to exit...")
        return

    threading.Thread(target=input_listener, daemon=True).start()
    threading.Thread(target=ui_loop, args=(total_jobs,), daemon=True).start()

    http_handler = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
    pool_slots = list(range(CONCURRENT_LIMIT))
    running_tasks = {}

    with ThreadPoolExecutor(max_workers=CONCURRENT_LIMIT) as pool:
        for idx, (mid, path) in enumerate(job_list, done_count + 1):
            if stop_flag: break

            while len(pool_slots) == 0 and not stop_flag:
                time.sleep(0.04)
                ready = [t for t in running_tasks if t.done()]
                for t in ready:
                    s = running_tasks.pop(t)
                    pool_slots.append(s)
                    try:
                        ok, msg = t.result()
                        with state_lock:
                            done_count += 1
                            current_name = slot_view[s].split('Map ')[1].split(':')[0] if 'Map ' in slot_view[s] else mid
                            if ok:
                                if msg == "CACHED":
                                    logs.append(f"[{done_count}/{total_jobs}] Map {current_name} -> {THEME['cached']}")
                                else:
                                    logs.append(f"[{done_count}/{total_jobs}] Map {current_name} -> {THEME['ok']}")
                            else:
                                if msg != "Interrupted":
                                    logs.append(f"[{done_count}/{total_jobs}] Map {current_name} -> {THEME['failed']} {THEME['reason'].format(reason=msg)}")
                                else:
                                    done_count -= 1
                    except: pass

            if stop_flag: break

            free_slot = pool_slots.pop(0)
            with state_lock:
                slot_view[free_slot] = f"Slot {free_slot+1} -> [{idx}/{total_jobs}] Connecting {mid}..."

            future = pool.submit(run_download, http_handler, mid, path, free_slot, idx, total_jobs)
            running_tasks[future] = free_slot

        while running_tasks:
            ready = [t for t in running_tasks if t.done()]
            for t in ready:
                s = running_tasks.pop(t)
                try:
                    ok, msg = t.result()
                    with state_lock:
                        done_count += 1
                        current_name = slot_view[s].split('Map ')[1].split(':')[0] if 'Map ' in slot_view[s] else mid
                        if ok:
                            if msg == "CACHED":
                                logs.append(f"[{done_count}/{total_jobs}] Map {current_name} -> {THEME['cached']}")
                            else:
                                logs.append(f"[{done_count}/{total_jobs}] Map {current_name} -> {THEME['ok']}")
                        else:
                            if msg != "Interrupted":
                                logs.append(f"[{done_count}/{total_jobs}] Map {current_name} -> {THEME['failed']} {THEME['reason'].format(reason=msg)}")
                            else:
                                done_count -= 1
                except: pass
                with state_lock: slot_view[s] = "Idle..."
            time.sleep(0.04)

    stop_flag = True
    time.sleep(0.2)
    sys.stdout.write("\033[2J\033[H")
    print(draw_header())
    print("--- Session Summary ---")
    for row in logs: print(row)
    clear_keys()
    input(f"\nFinished! Total processed: {done_count}. Press Enter to exit...")


if __name__ == "__main__":
    main()
