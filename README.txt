========================================================================
                      SIMPLE OSU! BATCH DOWNLOADER
========================================================================

A lightweight Python script designed to batch download
osu! beatmapsets community-maintained mirrors.
And it requires no official API keys or credentials.

------------------------------------------------------------------------
FEATURES
------------------------------------------------------------------------
* Zero Configuration: No official osu! API key or login required.
* Auto-Fallback: Tries the fast Nerinyan mirror first; automatically
  falls back to Sayobot if the map isn't found.
* Smart Duplication Checks: Skips maps that have already been downloaded
  to save time and bandwidth.
* URL Flexibility: Accepts full osu! beatmapset links, legacy /s/ URLs,
  or direct numeric IDs.

------------------------------------------------------------------------
REQUIREMENTS
------------------------------------------------------------------------
The script runs on standard Python 3, so naturally you need to install
python 3 and it requires the 'requests' library to handle file
streaming.

Installing Dependencies:
- On Arch Linux (or an arch based distro), you can install the
required package directly through your system package manager:

    sudo pacman -S python-requests

- If you are on Windows or other linux distros, you can run it inside
a virtual environment and use:

    'pip install requests'

- Google it or watch a tutorial if you couldn't figure it out yourself
or even ask AI for it.

------------------------------------------------------------------------
HOW TO USE
------------------------------------------------------------------------
1. Prepare Your Links File:
   Open a file named 'links.txt' in the exact same directory as the
   script. Place your osu! beatmap links inside, keeping
   ONE LINK PER LINE.
   I did put 5 maps as an example to see yourself how to put the maps
   you can delete those links and put your own of course.

   Example formats for 'links.txt':
   -----------------------------------------
   https://osu.ppy.sh/beatmapsets/1956659#mania/4055755
   https://osu.ppy.sh/beatmapsets/2341595
   https://osu.ppy.sh/s/934974
   1347618
   -----------------------------------------
   Note: You can use one format from above or multiple formats,
   Preferably use the second format
   (https://osu.ppy.sh/beatmapsets/2341595) if you encoutered
   any problems with the format

2. Run the Script:
   Open your terminal in the script's directory and execute it
   using the command:

    python osu_downloader.py

   Or (if you couldn't figure out how to open the terminal
   inside the directory, open the terminal or cmd):

    python "c:/the-directory/of-the-file/osu_downloader.py"

3. Import to osu!:
   Once finished, all your maps will be stored inside a folder called
   'downloaded_maps'. Open osu!, select all the .osz files,
   and drag-and-drop them right into the game window to extract them
   all at once. (Or excute them together or even one by one
   or drop them in the beatmaps directory, it doesn't matter, use your
   prefered way.)

------------------------------------------------------------------------
CREDITS & API DECLARATIONS
------------------------------------------------------------------------
This script does not scrape the official osu! website. Instead, it
utilizes infrastructure maintained by the osu! community:

* Primary Mirror API: Nerinyan API (https://nerinyan.moe/)
  Used for high-speed map distribution and discovery.

* Fallback Mirror API: Sayobot Support Team (https://sayobot.cn/)
  Used as a reliable fallback network endpoint for older or archived
  mapsets or if the primary API didn't work for whatever reason.

Disclaimer: This tool is an unofficial community asset. All beatmap
assets, audio tracks, and backgrounds belong to their respective
creators and copyright holders. And osu! team does not affiliate with
this project in any way, and all copyrights belong to them.

------------------------------------------------------------------------
AUTHORSHIP
------------------------------------------------------------------------
This utility was built, refactored, and optimized using AI
(aka vibe coded) by Yousef Al-Abdullah.
osu! profile: https://osu.ppy.sh/users/28499404/

========================================================================
