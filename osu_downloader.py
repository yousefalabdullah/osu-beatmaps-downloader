import os
import re
import time
import sys
import threading
import subprocess
import importlib

try:
    import requests
except ModuleNotFoundError:
    print("Required library 'requests' is missing. Installing it now...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        importlib.invalidate_caches()
        import requests
        print("Installation successful! Starting script...\n")
        time.sleep(1)
    except Exception as e:
        print(f"Failed to install 'requests' automatically: {e}")
        print("Please install it manually using: pip install requests")
        input("\nPress Enter to exit...")
        sys.exit(1)

from concurrent.futures import ThreadPoolExecutor

CONCURRENT_LIMIT = 4
RETRIES = 2
DELAY = 1

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FILE_PATH = os.path.join(BASE_DIR, "links.txt")
SAVE_DIR = os.path.join(BASE_DIR, "downloaded_maps")

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

paused = False
stop_flag = False
force_refresh = False
done_count = 0

state_lock = threading.Lock()
logs = []
slot_view = {}


def draw_header():
    line = "=" * 55
    out = [
        f"{THEME['menu']}{line}",
        f"                   osu! Downloader",
        f"{line}",
        f"  [P] Pause/Resume | [R] Refresh UI | [Q] Quit Script",
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
        except:
            pass


def read_key():
    if os.name == 'nt':
        try:
            if msvcrt.kbhit():
                return msvcrt.getch().decode('utf-8', errors='ignore').lower()
        except:
            return None
    else:
        if sys.stdin.isatty():
            fd = sys.stdin.fileno()
            try:
                old = termios.tcgetattr(fd)
            except:
                return None
            try:
                tty.setcbreak(fd)
                r, _, _ = select.select([sys.stdin], [], [], 0.05)
                if r:
                    return sys.stdin.read(1).lower()
            except:
                return None
            finally:
                try:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old)
                except:
                    pass
    return None


def input_listener():
    global paused, stop_flag, force_refresh
    while not stop_flag:
        key = read_key()
        if key == 'p':
            paused = not paused
            clear_keys()
        elif key == 'r':
            force_refresh = True
            clear_keys()
        elif key == 'q':
            stop_flag = True
        time.sleep(0.02)


def parse_id(link):
    m = re.search(r"(?:beatmapsets/|/s/|/download/)(\d+)|^(\d+)$", link.strip())
    if not m:
        return None
    return m.group(1) or m.group(2)


def run_download(session, map_id, dest, slot_idx, current_idx, total):
    global paused, stop_flag
    
    if stop_flag:
        return False, "Interrupted"
    if os.path.exists(dest):
        return True, "CACHED"

    endpoints = [
        f"https://api.nerinyan.moe/d/{map_id}",
        f"https://txy1.sayobot.cn/beatmaps/download/full/{map_id}"
    ]
    
    part_file = dest + ".part"
    fail_msg = "Error"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept-Encoding": "identity",
        "Connection": "keep-alive"
    }

    for link in endpoints:
        if stop_flag:
            break
            
        for run in range(1, RETRIES + 1):
            if stop_flag:
                break
                
            response = None
            try:
                response = session.get(link, headers=headers, timeout=7, stream=True)
                response.raise_for_status()
                
                size = response.headers.get('content-length')
                size = int(size) if size else None
                got = 0
                t0 = time.time()

                with open(part_file, "wb") as f:
                    for chunk in response.iter_content(chunk_size=262144):
                        while paused and not stop_flag:
                            time.sleep(0.2)
                            t0 = time.time() - (got / (rate if 'rate' in locals() and rate > 0 else 1))
                        
                        if stop_flag:
                            f.close()
                            if os.path.exists(part_file):
                                os.remove(part_file)
                            if response:
                                response.close()
                            return False, "Interrupted"

                        if chunk:
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
                    if os.path.exists(part_file):
                        os.remove(part_file)
                    if response:
                        response.close()
                    break 

                if os.path.exists(dest):
                    os.remove(dest)
                    
                os.replace(part_file, dest)
                if response:
                    response.close()
                return True, "OK"

            except requests.exceptions.HTTPError as e:
                fail_msg = f"HTTP {response.status_code}" if response else "HTTP Error"
                if response and response.status_code == 404: 
                    response.close()
                    break
            except Exception as e:
                fail_msg = type(e).__name__
                if "timeout" in fail_msg.lower() or "timeouterror" in fail_msg.lower():
                    fail_msg = "Timeout"
                elif "connection" in fail_msg.lower():
                    fail_msg = "ConnError"
                
                if os.path.exists(part_file):
                    try:
                        os.remove(part_file)
                    except:
                        pass
                if response:
                    try:
                        response.close()
                    except:
                        pass
                if run < RETRIES and not stop_flag:
                    time.sleep(DELAY)
                    continue
                else:
                    break

    return False, fail_msg


def ui_loop(total, limit):
    global stop_flag, done_count, paused, force_refresh
    
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()

    while not stop_flag:
        try:
            if force_refresh:
                sys.stdout.write("\033[2J\033[H")
                sys.stdout.flush()
                force_refresh = False

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
                for i in range(limit):
                    frame.append(slot_view.get(i, "Idle..."))
            frame.append("----------------")
            
            frame.append(f"\n[Progress: {done_count}/{total}]")

            out_str = "\033[H" + "\n".join(f"\033[K{line}" for line in frame)
            sys.stdout.write(out_str)
            sys.stdout.flush()
        except:
            pass
        time.sleep(0.25)


def main():
    global done_count, stop_flag, slot_view, CONCURRENT_LIMIT
    
    if not os.path.exists(FILE_PATH):
        sys.stdout.write("\033[2J\033[H")
        print(draw_header())
        print(f"Missing text file: {FILE_PATH}\n")
        input("Press Enter to close...")
        return

    sys.stdout.write("\033[2J\033[H")
    print(draw_header())
    
    while True:
        choice = input("Do you want a single or parallel download? (s/p): ").strip().lower()
        if choice == 's':
            CONCURRENT_LIMIT = 1
            break
        elif choice == 'p':
            CONCURRENT_LIMIT = 4
            break
        else:
            print("Invalid choice. Please enter 's' for single or 'p' for parallel.\n")

    slot_view = {i: "Idle..." for i in range(CONCURRENT_LIMIT)}
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
        for row in logs:
            print(row)
        input(f"\nAll files cached. Press Enter to exit...")
        return

    threading.Thread(target=input_listener, daemon=True).start()
    threading.Thread(target=ui_loop, args=(total_jobs, CONCURRENT_LIMIT), daemon=True).start()
    
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=CONCURRENT_LIMIT, pool_maxsize=CONCURRENT_LIMIT)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    pool_slots = list(range(CONCURRENT_LIMIT))
    running_tasks = {}

    with ThreadPoolExecutor(max_workers=CONCURRENT_LIMIT) as pool:
        for idx, (mid, path) in enumerate(job_list, done_count + 1):
            if stop_flag:
                break

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
                    except:
                        pass

            if stop_flag:
                break
            
            free_slot = pool_slots.pop(0)
            with state_lock:
                slot_view[free_slot] = f"Slot {free_slot+1} -> [{idx}/{total_jobs}] Connecting {mid}..."
            
            future = pool.submit(run_download, session, mid, path, free_slot, idx, total_jobs)
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
                except:
                    pass
                with state_lock:
                    slot_view[s] = "Idle..."
            time.sleep(0.04)

    stop_flag = True
    session.close()
    time.sleep(0.2)
    
    sys.stdout.write("\033[2J\033[H")
    print(draw_header())
    print("--- Session Summary ---")
    for row in logs:
        print(row)
    clear_keys()
    input(f"\nFinished! Total processed: {done_count}. Press Enter to exit...")


if __name__ == "__main__":
    main()
    
