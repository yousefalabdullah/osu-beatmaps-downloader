# Simple osu! Batch Downloader

A lightweight Python script designed to batch download **osu! beatmapsets** via community-maintained mirrors. It requires no official API keys, tokens, or credentials.

---

## 🚀 Features

* **Zero Configuration:** No official osu! API key or login credentials required.
* **Auto-Fallback:** Tries the fast **Nerinyan** mirror first; automatically falls back to **Sayobot** if the map isn't found.
* **Smart Duplication Checks:** Automatically skips maps that have already been downloaded to save time and bandwidth.
* **URL Flexibility:** Accepts full osu! beatmapset links, legacy `/s/` URLs, or direct numeric IDs.

---

## 🛠️ Requirements

The script runs on standard **Python 3** and requires the `requests` library to handle file streaming.

### Installing Dependencies

* **On Arch Linux (or Arch-based distros):** You can install the required package directly through your system package manager:
  
  sudo pacman -S python-requests
  

* **On Windows or other Linux distros:** You can run it inside a virtual environment and install it via `pip`:
  
  pip install requests
  
  *(If you encounter any issues, feel free to check online guides, tutorials, or consult an AI assistant).*

---

## 📖 How to Use

### 1. Prepare Your Links File
Create a file named `links.txt` in the exact same directory as the script. Place your osu! beatmap links inside, keeping **one link per line**. 

*(Note: The default file contains 5 example maps so you can see how it works. You can delete those links and paste your own).*

**Supported Formats for `links.txt`:**

[https://osu.ppy.sh/beatmapsets/1956659#mania/4055755](https://osu.ppy.sh/beatmapsets/1956659#mania/4055755)
[https://osu.ppy.sh/beatmapsets/2341595](https://osu.ppy.sh/beatmapsets/2341595)
[https://osu.ppy.sh/s/934974](https://osu.ppy.sh/s/934974)
1347618


💡 *Tip: You can mix multiple formats, but using the second format (`https://osu.ppy.sh/beatmapsets/2341595`) is highly recommended to avoid any formatting issues.*

### 2. Run the Script
Open your terminal or Command Prompt in the script's directory and execute:

python osu_downloader.py

Alternatively, if you cannot open the terminal directly inside that directory, use the absolute path:

python "C:/path-to-your-directory/osu_downloader.py"


### 3. Import to osu!
Once completed, all your downloaded maps will be stored inside a folder named `downloaded_maps`.
* Open **osu!**.
* Select all the downloaded `.osz` files.
* **Drag-and-drop** them directly into the game window to extract them all at once.
*(Alternatively, you can open them together, run them one by one, or move them directly into your game's `Songs` or beatmaps directory).*

---

## 🌐 Credits & API Declarations

This script does not scrape the official osu! website. Instead, it utilizes infrastructure fully maintained by the osu! community:

* **Primary Mirror API:** [Nerinyan](https://nerinyan.moe/) – Used for high-speed map distribution and discovery.
* **Fallback Mirror API:** [Sayobot Support Team](https://sayobot.cn/) – Used as a reliable fallback network endpoint for older or archived mapsets if the primary API is unavailable.

> ⚠️ **Disclaimer:** This tool is an unofficial community asset. All beatmap assets, audio tracks, and backgrounds belong to their respective creators and copyright holders. This project is not affiliated with, associated with, or endorsed by the official osu! team.

---

## ✍️ Authorship

This utility was built, refactored, and optimized using AI (vibe coded) by **Yousef Al-Abdullah**.  
🌐 **osu! Profile:** [Yousef Al-Abdullah](https://osu.ppy.sh/users/28499404/)
