import os
import json
import shutil
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import time
import argparse
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


def init_logger() -> Path:
    """Create per-user log directory and configure logging."""
    log_root = Path(os.environ.get("USERPROFILE", Path.home())) / ".enshrouded_world_duplicator"
    log_root.mkdir(parents=True, exist_ok=True)
    log_file = log_root / "world_duplicator.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        filename=log_file,
    )
    return log_file


# Configure logging
init_logger()


def guess_save_directory() -> Optional[Path]:
    """Try to locate the Enshrouded save directory on common systems."""
    possible_locations = []

    # Windows standard location
    appdata = os.getenv("APPDATA")
    if appdata:
        possible_locations.append(Path(appdata) / "Enshrouded")
        # Some setups may append an extra 'Roaming'
        possible_locations.append(Path(appdata) / "Roaming" / "Enshrouded")

    # Linux (Steam/Proton) location
    possible_locations.append(
        Path.home()
        / ".steam/steam/steamapps/compatdata/1203620/pfx/drive_c/users/steamuser"
        / "AppData/Roaming/Enshrouded"
    )

    for location in possible_locations:
        if location.exists():
            return location
    return None

@dataclass
class WorldInfo:
    """Store world information with validation"""
    id: str
    name: str
    path: Path
    index_data: dict
    is_deleted: bool = False
    last_played: int = 0
    created_at: int = 0
    
    @property
    def files(self) -> List[Path]:
        """Get all files associated with this world"""
        return sorted(
            list(self.path.glob(f"{self.id}-*")) +
            list(self.path.glob(f"{self.id}_info-*"))
        )
    
    @property
    def is_valid(self) -> bool:
        """Check if world is valid and not deleted"""
        return not self.is_deleted and bool(self.files)
    
    @property
    def display_name(self) -> str:
        """Get a friendly display name with last played time"""
        if self.last_played:
            time_str = time.strftime('%Y-%m-%d %H:%M', time.localtime(self.last_played))
            return f"{self.name} (Last played: {time_str})"
        return self.name or f"World {self.id[:6]}"

class WorldManager:
    """Handles world file operations and metadata management"""
    METADATA_FILE = "enshrouded_user.json"
    
    def __init__(self, save_dir: Optional[Path] = None):
        self.save_dir = Path(save_dir) if save_dir else None
        self.worlds: Dict[str, WorldInfo] = {}
        self.metadata: Dict = {}
        self._world_list_cache: List[Tuple[str, str]] = []
        
    def set_save_directory(self, path: str | Path) -> None:
        """Set and validate the save directory"""
        path = Path(path)
        if not path.exists():
            raise ValueError(f"Save directory does not exist: {path}")
            
        metadata_file = path / self.METADATA_FILE
        if not metadata_file.exists():
            raise ValueError(f"Not a valid Enshrouded save directory (missing {self.METADATA_FILE})")
            
        self.save_dir = path
        self.metadata = self._read_metadata()
        self.scan_worlds()
    
    def _read_metadata(self) -> Dict:
        """Read and parse metadata file"""
        try:
            metadata_file = self.save_dir / self.METADATA_FILE
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Failed to read metadata: {e}")
            return {}
    
    def _read_index_file(self, path: Path) -> dict:
        """Read and parse world index file"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Failed to read index file {path}: {e}")
            return {}
    
    def _get_world_metadata(self, world_id: str) -> Tuple[str, int, int]:
        """Get world name and timestamps from metadata"""
        if "worlds" not in self.metadata:
            return "", 0, 0
            
        for world in self.metadata["worlds"]:
            if world.get("id") == world_id:
                return (
                    world.get("name", ""),
                    world.get("createdAt", 0),
                    world.get("lastPlayed", 0)
                )
        return "", 0, 0
    
    def scan_worlds(self) -> List[Tuple[str, str]]:
        """Scan save directory for worlds and return list of (display_name, id) tuples"""
        if not self.save_dir:
            raise RuntimeError("Save directory not set")
            
        self.worlds.clear()
        processed_ids = set()  # Track processed world IDs
        world_list = []
        
        # Find all world IDs by scanning for index files
        for index_file in self.save_dir.glob("*-index"):
            world_id = index_file.name.split('-')[0]
            if world_id == "characters" or world_id in processed_ids:  # Skip characters file and duplicates
                continue
                
            processed_ids.add(world_id)
            
            # Read index file
            index_data = self._read_index_file(index_file)
            is_deleted = index_data.get("deleted", False)
            
            # Get metadata for this world
            name, created_at, last_played = self._get_world_metadata(world_id)
            
            # Create world info
            world_info = WorldInfo(
                id=world_id,
                name=name,
                path=self.save_dir,
                index_data=index_data,
                is_deleted=is_deleted,
                last_played=last_played,
                created_at=created_at
            )
            
            if world_info.is_valid:
                self.worlds[world_id] = world_info
                world_list.append((world_info.display_name, world_id))
                
        self._world_list_cache = sorted(world_list, key=lambda x: x[0].lower())
        return self._world_list_cache
    
    def duplicate_world(self, source_id: str, target_id: str) -> Optional[Path]:
        """Copy world files and update metadata"""
        if not (source_id in self.worlds and target_id in self.worlds):
            logging.error(f"Invalid world IDs - source: {source_id}, target: {target_id}")
            return None

        source = self.worlds[source_id]
        target = self.worlds[target_id]

        try:
            # Move existing target files to backup
            timestamp = time.strftime('%Y%m%d%H%M%S')
            backup_dir = self.save_dir / f"{target_id}_backup_{timestamp}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            for file in target.files:
                shutil.move(str(file), backup_dir / file.name)
            logging.info(f"Backup of target world created at {backup_dir}")

            # Copy all source files to target
            for source_file in source.files:
                new_name = source_file.name.replace(source_id, target_id)
                target_file = self.save_dir / new_name
                shutil.copy2(source_file, target_file)

            # Update target's index file with new timestamp and any additional data
            target_index = self.save_dir / f"{target_id}-index"
            if target_index.exists():
                index_data = self._read_index_file(target_index)
                index_data["time"] = int(time.time())
                index_data["deleted"] = False
                index_data["latest"] = source.index_data.get("latest", 0)

                # Copy any additional fields from source index data to target index data
                for key, value in source.index_data.items():
                    if key not in ["id", "time", "deleted"]:
                        index_data[key] = value
                        logging.info(f"Copied {key}: {value}")

                target_index.write_text(json.dumps(index_data, indent=2))

            # Update metadata file
            if "worlds" in self.metadata:
                current_time = int(time.time())
                for world in self.metadata["worlds"]:
                    if world["id"] == target_id:
                        world["name"] = f"Copy of {source.name}"
                        world["lastPlayed"] = current_time
                        # Copy any additional fields from source metadata to target metadata
                        for key, value in source.index_data.items():
                            if key not in ["id", "time", "deleted"]:
                                world[key] = value
                                logging.info(f"Copied {key} to metadata: {value}")
                        break

                metadata_file = self.save_dir / self.METADATA_FILE
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(self.metadata, f, indent=2)

            logging.info(f"Successfully duplicated world {source_id} to {target_id}")
            return backup_dir

        except Exception as e:
            logging.error(f"Failed to duplicate world: {e}")
            return None

class WorldDuplicatorGUI:
    """GUI for world duplication"""
    def __init__(self, auto_confirm: bool = False):
        self.world_manager = WorldManager()
        self.auto_confirm = auto_confirm
        self.setup_gui()

        # Attempt to automatically detect the save directory
        default_dir = guess_save_directory()
        if default_dir:
            try:
                self.world_manager.set_save_directory(default_dir)
                self.folder_label.config(text=str(default_dir))
                self.refresh_world_lists()
                self.status_label.config(text="Detected save directory")
            except Exception as e:
                logging.error(f"Auto-detect failed: {e}")
        
    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("Enshrouded World Duplicator")
        self.root.geometry("1000x600")
        
        style = ttk.Style()
        style.configure('World.TLabelframe', padding=10)
        
        # Create main frame with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add folder selection
        folder_frame = ttk.Frame(main_frame)
        folder_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.folder_label = ttk.Label(folder_frame, text="No save folder selected", wraplength=800)
        self.folder_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(folder_frame, text="Select Save Folder", 
                  command=self.select_save_folder).pack(side=tk.RIGHT)
        
        # Create selection frames
        selection_frame = ttk.Frame(main_frame)
        selection_frame.pack(fill=tk.BOTH, expand=True)
        
        # Source frame
        source_frame = self.create_world_frame(selection_frame, "Source World")
        source_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Target frame
        target_frame = self.create_world_frame(selection_frame, "Target World (Will be replaced)")
        target_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.duplicate_button = ttk.Button(button_frame, text="Duplicate World",
                                         command=self.duplicate_world,
                                         state=tk.DISABLED)
        self.duplicate_button.pack()
        
        # Add status label
        self.status_label = ttk.Label(main_frame, text="", wraplength=800)
        self.status_label.pack(pady=(5, 0))
    
    def create_world_frame(self, parent, title):
        frame = ttk.LabelFrame(parent, text=title, padding="5", style='World.TLabelframe')
        
        # Create listbox with scrollbar
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set,
                            selectmode=tk.SINGLE, exportselection=False,
                            font=('TkDefaultFont', 10))
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=listbox.yview)
        
        # Store references
        setattr(self, f"{title.split()[0].lower()}_list", listbox)
        
        # Bind selection
        listbox.bind('<<ListboxSelect>>', self.check_selection)
        
        return frame
    
    def select_save_folder(self):
        """Handle save folder selection"""
        folder = filedialog.askdirectory(title="Select Enshrouded Save Folder")
        if not folder:
            return
            
        try:
            self.world_manager.set_save_directory(folder)
            self.folder_label.config(text=folder)
            self.refresh_world_lists()
            self.status_label.config(text="Save folder loaded successfully")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.status_label.config(text="Error loading save folder")
    
    def refresh_world_lists(self):
        """Update both world lists"""
        worlds = self.world_manager.scan_worlds()
        
        # Clear existing items
        self.source_list.delete(0, tk.END)
        self.target_list.delete(0, tk.END)
        
        # Add unique entries
        seen_names = set()
        for display_name, _ in worlds:
            if display_name not in seen_names:
                seen_names.add(display_name)
                self.source_list.insert(tk.END, display_name)
                self.target_list.insert(tk.END, display_name)
    
    def check_selection(self, _=None):
        """Enable/disable duplicate button based on selections"""
        source_sel = self.source_list.curselection()
        target_sel = self.target_list.curselection()
        
        self.duplicate_button.config(
            state=tk.NORMAL if source_sel and target_sel else tk.DISABLED
        )
    
    def duplicate_world(self):
        """Handle world duplication"""
        source_idx = self.source_list.curselection()[0]
        target_idx = self.target_list.curselection()[0]
        
        source_display = self.source_list.get(source_idx)
        target_display = self.target_list.get(target_idx)
        
        if source_display == target_display:
            messagebox.showwarning("Warning", "Source and target worlds must be different")
            return
        
        worlds = self.world_manager.scan_worlds()
        source_id = next(id for name, id in worlds if name == source_display)
        target_id = next(id for name, id in worlds if name == target_display)
        
        if self.auto_confirm or messagebox.askyesno(
            "Confirm", f"Replace '{target_display}' with a copy of '{source_display}'?"
        ):
            try:
                backup_dir = self.world_manager.duplicate_world(source_id, target_id)
                if backup_dir:
                    self.refresh_world_lists()
                    messagebox.showinfo(
                        "Success",
                        f"World duplicated successfully!\nBackup saved at: {backup_dir}"
                    )
                    if not self.auto_confirm and messagebox.askyesno(
                        "Delete Backup?", f"Delete backup at {backup_dir}?"
                    ):
                        try:
                            shutil.rmtree(backup_dir)
                            logging.info(f"Deleted backup at {backup_dir}")
                            self.status_label.config(
                                text="World duplicated successfully; backup deleted"
                            )
                        except Exception as e:
                            logging.error(f"Failed to delete backup: {e}")
                            self.status_label.config(
                                text=f"World duplicated; failed to delete backup: {e}"
                            )
                    else:
                        self.status_label.config(
                            text=f"World duplicated successfully; backup at {backup_dir}"
                        )
                else:
                    messagebox.showerror(
                        "Error",
                        "Failed to duplicate world. Check the log file."
                    )
                    self.status_label.config(text="Failed to duplicate world")
            except Exception as e:
                messagebox.showerror("Error", str(e))
                self.status_label.config(text=f"Error: {str(e)}")

def main():
    """Entry point for CLI or GUI mode."""
    parser = argparse.ArgumentParser(
        description="Duplicate Enshrouded worlds without launching the GUI"
    )
    parser.add_argument("--source", help="ID of the source world to copy")
    parser.add_argument(
        "--target", help="ID of the target world to replace with the copy"
    )
    parser.add_argument(
        "--save-dir",
        type=Path,
        default=guess_save_directory(),
        help="Path to Enshrouded save directory (default: auto-detected)",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Automatically answer yes to confirmation prompts",
    )

    args = parser.parse_args()

    if args.source and args.target:
        save_dir = args.save_dir
        if not save_dir:
            logging.error("Save directory not specified and could not be guessed")
            print("Error: save directory not specified and could not be guessed.")
            sys.exit(1)

        wm = WorldManager()
        try:
            wm.set_save_directory(save_dir)
        except Exception as e:
            logging.error(f"Failed to load save directory: {e}")
            print(f"Error: {e}")
            sys.exit(1)

        if not args.yes:
            root = tk.Tk()
            root.withdraw()
            proceed = messagebox.askyesno(
                "Confirm",
                f"Replace '{args.target}' with a copy of '{args.source}'?",
            )
            root.destroy()
            if not proceed:
                print("Operation cancelled.")
                sys.exit(0)

        backup_dir = wm.duplicate_world(args.source, args.target)
        if backup_dir:
            print(f"World duplicated successfully. Backup at {backup_dir}")
            if not args.yes:
                root = tk.Tk()
                root.withdraw()
                delete_backup = messagebox.askyesno(
                    "Delete Backup?", f"Delete backup at {backup_dir}?"
                )
                root.destroy()
                if delete_backup:
                    try:
                        shutil.rmtree(backup_dir)
                        logging.info(f"Deleted backup at {backup_dir}")
                        print("Backup deleted.")
                    except Exception as e:
                        logging.error(f"Failed to delete backup: {e}")
                        print(f"Failed to delete backup: {e}")
            sys.exit(0)
        else:
            print("Failed to duplicate world. Check the log for details.")
            sys.exit(1)

    elif args.source or args.target:
        print("Both --source and --target must be provided together.")
        sys.exit(1)

    app = WorldDuplicatorGUI(auto_confirm=args.yes)
    app.root.mainloop()

if __name__ == "__main__":
    main()
