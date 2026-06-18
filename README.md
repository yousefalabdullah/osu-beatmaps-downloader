# a Simple osu! Bulk Downloader Tool

A lightweight Python script designed to batch download **osu! beatmapsets** in bulk via community-maintained mirrors. It requires no official API keys, tokens, or credentials.

---

## 🚀 Features

* **Zero Configuration:** No official osu! API key or login credentials required.
* **Auto-Fallback:** Tries the fast **Nerinyan** mirror first; automatically falls back to **Sayobot** if the map isn't found.
* **Smart Duplication Checks:** Automatically skips maps that have already been downloaded to save time and bandwidth.
* **URL Flexibility:** Accepts full osu! beatmapset links, legacy `/s/` URLs, or direct numeric IDs.

---

## 🛠️ Requirements

The script runs on standard **Python 3**.
So naturally you first need to install [Python3](https://www.python.org/downloads/) for your operating system.

## 📖 How to Use

### 1. Prepare Your beatmaps list
Place your osu! beatmap links inside a file called `links.txt` inside the same directory as the script, keeping **one beatmap link per line**. 

*(Note: The default file contains 5 example maps so you can see how it works. You can delete those links and paste your own).*

**supported beatmnaps links formats inside `links.txt`:**
```text
https://osu.ppy.sh/beatmapsets/1956659#mania/4055755
https://osu.ppy.sh/beatmapsets/2341595
https://osu.ppy.sh/s/934974
1347618
```
💡 *Tip: You can mix multiple formats, but using the second format (`https://osu.ppy.sh/beatmapsets/2341595`) for all of the beatmaps is highly recommended to avoid any formatting issues.*

### 2. Run the Script
If you are on windows you can just double click it after you put your beatmaps list. if you are not on windows tho or it didn't work, you can use the alternative method:
Open your terminal or Command Prompt in the script's directory and execute:
```bash
python osu_downloader.py
```
Alternatively, if you cannot open the terminal directly inside that directory, use the full directory:
```cmd
python "C:/path-to-your-directory/osu_downloader.py"
```

### 3. Import to osu!
Once completed, all your downloaded maps will be stored inside a folder named `downloaded_maps`.
* Open **osu!**.
* Select all the downloaded `.osz` files.
* **Drag-and-drop** them directly into the game window to extract them all at once.
*(Alternatively, you can open them together, run them one by one, or move them directly into your game's `Songs` or beatmaps directory, just import them in your preferred way!).*

---

## 🌐 Credits & API Declarations

This script does not scrape the official osu! website. Instead, it utilizes infrastructure fully maintained by the osu! community:

* **Primary Mirror API:** [Nerinyan](https://nerinyan.moe/) – Used for high-speed map distribution and discovery.
* **Fallback Mirror API:** [Sayobot Support Team](https://sayobot.cn/) – Used as a reliable fallback network endpoint for older or archived mapsets if the primary API is unavailable.

> ⚠️ **Disclaimer:** This tool is an unofficial community asset. All beatmap assets, audio tracks, and backgrounds belong to their respective creators and copyright holders. This project is not affiliated with, associated with, or endorsed by the official osu! team.

---

## ✍️ Authorship

This utility was built, refactored, and optimized using AI (vibe coded) by **Yousef Al-Abdullah**.  
