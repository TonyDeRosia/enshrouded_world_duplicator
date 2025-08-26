## **Enshrouded World Duplicator**

[![Tests](https://github.com/YOUR_GITHUB_USERNAME/enshrouded_world_duplicator/actions/workflows/test.yml/badge.svg)](https://github.com/YOUR_GITHUB_USERNAME/enshrouded_world_duplicator/actions/workflows/test.yml)  
A Python-based tool that allows you to safely duplicate your Enshrouded game worlds while preserving all data and settings.

---

### **⚠ Important Notice**  
Before using this tool, **back up your Enshrouded save directory manually**. While this script is designed to safely duplicate worlds, unforeseen issues could result in data loss or corruption. **Proceed at your own risk.**  

After installation, launch the tool with the `world-duplicator` command or by running `python -m world_duplicator` from your IDE or terminal.

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

Install using pip:
```shell
pip install enshrouded-world-duplicator
```

This project exposes a `world-duplicator` entry point via `pyproject.toml`, providing an easy-to-use command-line interface.

### **From source**
1. Clone this repository.
2. Install the package:
   ```shell
   pip install .
   ```
3. Run `world-duplicator` (or `python -m world_duplicator`).

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
### **GUI mode**
Launch the graphical interface:

```shell
world-duplicator
```

or

```shell
python -m world_duplicator
```

### **Command-line usage**
If the Tkinter GUI library is missing on your system, the tool will fall back to command-line mode. You can duplicate worlds directly from the command line using either entry point:

```shell
world-duplicator --source <world_id> --target <world_id>
```

Provide a custom save directory if it cannot be auto-detected:

```shell
world-duplicator --source <src_id> --target <dst_id> --save-dir "/path/to/Enshrouded"
```

Run unattended without confirmation prompts by adding the `--yes` flag:

```shell
world-duplicator --source <src_id> --target <dst_id> --yes
```

Show progress for each file operation with the `--verbose` flag:

```shell
world-duplicator --source <src_id> --target <dst_id> --verbose
# Example output:
# Moved world2-data to world2_backup_20200101000000
# Copied world1-data to world2-data
```

List available worlds and exit:

```shell
world-duplicator --list
```

Include `--save-dir` if the location cannot be auto-detected:

```shell
world-duplicator --list --save-dir "/path/to/Enshrouded"
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
- A progress bar and status messages show each file operation during duplication.

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
- If you cannot install Tkinter, run the tool using the command-line options described above.

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

## **Running Tests**
This project uses `pytest` for its test suite. Run the tests from the repository root with:

```shell
pytest
```

---

## **Final Reminder**
This tool **overwrites the target world completely**. Double-check your selections before confirming. **Back up your files** to avoid irreversible changes.  

Enjoy duplicating your Enshrouded worlds safely! 🚀

