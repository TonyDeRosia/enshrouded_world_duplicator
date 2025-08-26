## **Enshrouded World Duplicator**  
A Python-based tool that allows you to safely duplicate your Enshrouded game worlds while preserving all data and settings.

---

### **⚠ Important Notice**  
Before using this tool, **back up your Enshrouded save directory manually**. While this script is designed to safely duplicate worlds, unforeseen issues could result in data loss or corruption. **Proceed at your own risk.**  

You can simply paste the `world_duplicator.py` into a compiler like **VS Code** and run it.

---

## **⚡ Tips for Identifying Your World**  
A **smart way** to determine which world you want to edit is by checking the **date modified** column in your file explorer. After leaving a game, the world files will update with the latest timestamp, allowing you to easily identify the most recently played world.

---

## **Requirements**  
Before running this tool, ensure you have:

- **Python 3.10 or newer** installed  
  - Download: [https://www.python.org/downloads/](https://www.python.org/downloads/)  
  - During installation on Windows, check **"Add Python to PATH"**  
  - To check your Python version, open a terminal/command prompt and run:  
    ```shell
    python --version
    ```

---

## **Installation**  
1. **Save** the `world_duplicator.py` script to any location on your computer.  
2. Ensure your system meets the requirements below.  

### **Windows**  
- Python’s **Tkinter** library is included by default.  
- No additional setup required if Python is installed correctly.  

### **Linux**  
You may need to install Tkinter manually:  
- **Ubuntu/Debian:**  
  ```shell
  sudo apt-get install python3-tk
  ```
- **Fedora:**  
  ```shell
  sudo dnf install python3-tkinter
  ```
- **Arch Linux:**  
  ```shell
  sudo pacman -S tk
  ```

---

## **Running the Program**  
Run the script:

- **Double-click** `world_duplicator.py`
- **OR** open a terminal/command prompt in the script’s directory and run:
  ```shell
  python world_duplicator.py
  ```

### **Command-line usage**
You can bypass the graphical interface and duplicate worlds directly from the command line:

```shell
python world_duplicator.py --source <world_id> --target <world_id>
```

Provide a custom save directory if it cannot be auto-detected:

```shell
python world_duplicator.py --source <src_id> --target <dst_id> --save-dir "/path/to/Enshrouded"
```

Run unattended without confirmation prompts by adding the `--yes` flag:

```shell
python world_duplicator.py --source <src_id> --target <dst_id> --yes
```

List available worlds and exit:

```shell
python world_duplicator.py --list
```

Include `--save-dir` if the location cannot be auto-detected:

```shell
python world_duplicator.py --list --save-dir "/path/to/Enshrouded"
```

Both `--source` and `--target` must be valid world IDs. The script will report success or failure via the command line.

### **Using the program:**
- The tool attempts to detect your save directory automatically on startup. It looks in:
  - `%APPDATA%\\Roaming\\Enshrouded` (Windows)
  - `~/.steam/steam/steamapps/compatdata/1203620/pfx/drive_c/users/steamuser/AppData/Roaming/Enshrouded` (Linux/Steam)
- If detection fails, click **"Select Save Folder"** to choose your Enshrouded save directory.
- Select a **source world** (the one you want to copy).
- Select a **target world** (the one you want to replace).
- Click **"Duplicate World"** to begin.

---

## **Finding Your Save Directory**  
Your Enshrouded save files are typically located at:  

### **Windows**  
```shell
%APPDATA%\Roaming\Enshrouded\
```
**or**  
```shell
C:\Users\[YourUsername]\AppData\Roaming\Enshrouded\
```

### **Linux (Steam)**  
```shell
~/.steam/steam/steamapps/compatdata/1203620/pfx/drive_c/users/steamuser/AppData/Roaming/Enshrouded/
```

---

## **Troubleshooting**  

### **Common Issues**  
#### **"Python is not recognized as a command"**  
- **Windows:** Reinstall Python and ensure **"Add Python to PATH"** is checked.  
- **Linux:** Install Python using:  
  ```shell
  sudo apt install python3
  ```

#### **"No module named tkinter"**  
- **Windows:** Reinstall Python.  
- **Linux:** Install Tkinter (`python3-tk` or equivalent for your distribution).  

#### **"Permission denied" errors**  
- **Windows:** Run the script as an **administrator**.  
- **Linux:** Use `sudo` when running the script.  

### **Log File Location**  
If you run into errors, check the logs:  

#### **Windows:**  
```shell
%USERPROFILE%\.enshrouded_world_duplicator\world_duplicator.log
```
#### **Linux:**  
```shell
~/.enshrouded_world_duplicator/world_duplicator.log
```

---

## **Safety Features**  
- **Asks for confirmation** before overwriting worlds.  
- **Validates** save directory and world files before proceeding.  
- Preserves **world metadata, timestamps, and settings**.  
- **Logs all operations** for debugging and recovery.  

---

## **⚠ Best Practices to Avoid Data Loss**  
1. **Always make a backup** of your Enshrouded save directory before using this tool.  
2. **Do not interrupt** the duplication process once started.  
3. **Verify the correct worlds are selected** before confirming duplication.  
4. Ensure the **game is completely closed** before using the tool.  

---

## **Technical Details**  
- Uses **Python's built-in libraries** (no external dependencies required).  
- Performs **safe file operations** with error handling.  
- Maintains **all world configurations and metadata**.  
- Works with the **latest version of Enshrouded** (as of **February 2024**).  

---

## **Final Reminder**  
This tool **overwrites the target world completely**. Double-check your selections before confirming. **Back up your files** to avoid irreversible changes.  

Enjoy duplicating your Enshrouded worlds safely! 🚀

