import os
import json
import shutil
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import time
from uuid import uuid4
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='world_duplicator.log'
)

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

    def create_world_copy(self, source_id: str) -> Optional[str]:
        """Create a copy of a world with a new unique ID"""
        if source_id not in self.worlds:
            logging.error(f"Invalid source world ID: {source_id}")
            return None

        new_id = uuid4().hex
        source = self.worlds[source_id]

        try:
            # Copy all source files to new files with the generated ID
            for source_file in source.files:
                new_name = source_file.name.replace(source_id, new_id)
                target_file = self.save_dir / new_name
                shutil.copy2(source_file, target_file)

            # Update the new world's index file with fresh metadata
            new_index = self.save_dir / f"{new_id}-index"
            index_data = {}
            if new_index.exists():
                index_data = self._read_index_file(new_index)
                index_data["time"] = int(time.time())
                index_data["deleted"] = False
                index_data["latest"] = source.index_data.get("latest", 0)

                for key, value in source.index_data.items():
                    if key not in ["id", "time", "deleted"]:
                        index_data[key] = value

                new_index.write_text(json.dumps(index_data, indent=2))

            # Insert new world metadata entry
            if "worlds" in self.metadata:
                current_time = int(time.time())
                source_meta = next(
                    (w for w in self.metadata["worlds"] if w.get("id") == source_id),
                    {},
                )
                new_meta = dict(source_meta)
                new_meta["id"] = new_id
                new_meta["name"] = f"Copy of {source.name}"
                new_meta["createdAt"] = current_time
                new_meta["lastPlayed"] = current_time

                for key, value in source.index_data.items():
                    if key not in ["id", "time", "deleted"]:
                        new_meta[key] = value

                self.metadata["worlds"].append(new_meta)
                metadata_file = self.save_dir / self.METADATA_FILE
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(self.metadata, f, indent=2)

            # Refresh internal world list
            self.scan_worlds()
            logging.info(f"Created world copy {new_id} from {source_id}")
            return new_id

        except Exception as e:
            logging.error(f"Failed to create world copy: {e}")
            return None

    def duplicate_world(self, source_id: str, target_id: str) -> bool:
        """Copy world files and update metadata"""
        if not (source_id in self.worlds and target_id in self.worlds):
            logging.error(f"Invalid world IDs - source: {source_id}, target: {target_id}")
            return False
            
        source = self.worlds[source_id]
        target = self.worlds[target_id]
        
        try:
            # Remove existing target files
            for file in target.files:
                file.unlink(missing_ok=True)
            
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
            return True
            
        except Exception as e:
            logging.error(f"Failed to duplicate world: {e}")
            return False

class WorldDuplicatorGUI:
    """GUI for world duplication"""
    def __init__(self):
        self.world_manager = WorldManager()
        self.setup_gui()
        
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
        
        # Create selection frame
        selection_frame = ttk.Frame(main_frame)
        selection_frame.pack(fill=tk.BOTH, expand=True)

        # Source frame only
        source_frame = self.create_world_frame(selection_frame, "Source World")
        source_frame.pack(fill=tk.BOTH, expand=True)

        # Action button
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        self.duplicate_button = ttk.Button(
            button_frame,
            text="Duplicate to New World",
            command=self.duplicate_to_new_world,
            state=tk.DISABLED,
        )
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
            self.refresh_world_list()
            self.status_label.config(text="Save folder loaded successfully")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.status_label.config(text="Error loading save folder")
    
    def refresh_world_list(self):
        """Update world list"""
        worlds = self.world_manager.scan_worlds()

        # Clear existing items
        self.source_list.delete(0, tk.END)

        # Add unique entries
        seen_names = set()
        for display_name, _ in worlds:
            if display_name not in seen_names:
                seen_names.add(display_name)
                self.source_list.insert(tk.END, display_name)

    def check_selection(self, _=None):
        """Enable/disable duplicate button based on selection"""
        source_sel = self.source_list.curselection()

        self.duplicate_button.config(
            state=tk.NORMAL if source_sel else tk.DISABLED
        )

    def duplicate_to_new_world(self):
        """Handle duplication into a new world"""
        source_idx = self.source_list.curselection()[0]

        source_display = self.source_list.get(source_idx)

        worlds = self.world_manager.scan_worlds()
        source_id = next(id for name, id in worlds if name == source_display)

        if messagebox.askyesno("Confirm",
                             f"Create a new copy of '{source_display}'?"):
            try:
                new_id = self.world_manager.create_world_copy(source_id)
                if new_id:
                    messagebox.showinfo("Success", "World duplicated successfully!")
                    self.refresh_world_list()
                    self.status_label.config(text="World duplicated successfully")
                else:
                    messagebox.showerror("Error",
                                       "Failed to duplicate world. Check the log file.")
                    self.status_label.config(text="Failed to duplicate world")
            except Exception as e:
                messagebox.showerror("Error", str(e))
                self.status_label.config(text=f"Error: {str(e)}")

def main():
    app = WorldDuplicatorGUI()
    app.root.mainloop()

if __name__ == "__main__":
    main()
