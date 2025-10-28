# Jim-G FiveM Map Collision Checker

![jim G green zone red zone Views](https://komarev.com/ghpvc/?username=jimgordon20)

A simple, interactive Python utility to scan your FiveM `resources` folder for file conflicts and redundant duplicates among map-related files. Finding these collisions is crucial for debugging map load errors, broken collisions, and invisible map elements.

The generated HTML report includes a **"Copy Dir"** button to instantly grab the directory path of a conflicting file, speeding up the fix process.

---

## 1. Requirements 🛠️

You need **Python 3.x** installed and properly added to your system's PATH.

For the best experience (progress bars and colored console output), install these two libraries:

```bash
pip install colorama tqdm
```


# 2. Setup 📂
1. Download: Obtain both files from the repository:

jim_g_collision_checker.py (The Python script)

Check_FiveM_Resources.bat (The launch file)

2. Placement: Ensure both files are saved in the same folder.



## 3. How to Run 🚀
The tool is designed to run easily using the batch file.

1. Run the Batch File: Double-click Check_FiveM_Resources.bat.

2. Provide Path: The script will open and prompt you to enter the directory path.

   .  Copy the full path to your main FiveM resources folder (e.g., C:\FXServer\server-data\resources).

   . Paste the path into the terminal and press ENTER.



## 4. Interactive Configuration Guide ⚙️
After providing the path, the script will guide you through selecting which file types to search. This allows you to focus on critical files (.ymap, .ybn) while ignoring large or less critical files (.ydr, .ypt).

Pattern,Description,Recommendation
*.ymap,Map Data (Placement/Details),Highly Recommended
*.ybn,Bounds/Collision Data,Highly Recommended
light_ymaps,Light Map Files (lodlights*.ymap / vw_*.ymap),Recommended
*.ymt,Meta/Config Files,Recommended
*.ytd,Textures Dictionary,Recommended
*.ydr,Drawable (3D Models),Optional
*.ydd,Drawable Dictionary (Model Container),Optional
*.ytyp,Types/Manifest (Map/MLO Definitions),Optional
*.ycd,Clip Dictionary (Animations),Optional
*.ynv,Navigation Mesh (AI Navigation),Optional
*.ypt,Particle Effects (FX),Optional

Input Options:

 . Enter 1 for YES (Search).

 . Enter 2 for NO (Ignore).

 . Press ENTER to accept the default recommendation shown.

 . Press ENTER again to begin the file hashing and scan.


## 5. Reviewing the Report
The final output is saved to collision_report.html in the script's folder.

Conflict Type,Status,Action Required
🔴 Critical Conflict,"Same filename, different content (hash).","MUST FIX. Only one version loads, causing map failures."
🟡 Redundant Duplicate,"Same filename, identical content (hash).",Cleanup.

Use the Copy Dir button next to any entry to copy the parent resource folder's path directly to your clipboard for quick file management.





