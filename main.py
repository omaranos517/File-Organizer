import os
import shutil
import threading
import traceback
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

DEFAULT_SOURCE = Path.home() / "Downloads"

# File extension categories
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".svg", ".webp", ".heic", ".raw"}
VIDEO_EXT = {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".mpeg", ".mpg", ".3gp"}
AUDIO_EXT = {".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a"}
SETUP_EXT = {".exe", ".msi", ".dmg", ".pkg", ".deb"}
DOC_EXT = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt"}
COMPRESSED_EXT = {".zip", ".rar", ".7z", ".tar", ".gz"}

# Helper function to format size
def format_size(bytes_size):
    """Convert size to human readable format"""
    for unit in ['B','KB','MB','GB','TB']:
        if bytes_size < 1024:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.2f} PB"


# Enhanced UI with dark mode support
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("File Organizer - Downloads Manager")
        if os.path.exists("icon.ico"):
            self.iconbitmap("icon.ico")
        self.geometry("900x800")
        self.resizable(True, True)
        
        # Theme variables
        self.dark_mode = tk.BooleanVar(value=False)
        self.colors = {
            'light': {
                'bg': '#f0f0f0',
                'fg': '#2c3e50',
                'secondary_bg': '#ffffff',
                'accent': '#3498db',
                'danger': '#e74c3c',
                'success': '#2ecc71',
                'text_box_bg': '#f8f9fa',
                'frame_bg': '#e9ecef'
            },
            'dark': {
                'bg': '#2c3e50',
                'fg': '#ecf0f1',
                'secondary_bg': '#34495e',
                'accent': '#3498db',
                'danger': '#e74c3c',
                'success': '#2ecc71',
                'text_box_bg': '#2d3436',
                'frame_bg': '#34495e'
            }
        }
        
        # Setup style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Variables
        self.source_var = tk.StringVar(value=str(DEFAULT_SOURCE))
        self.images_var = tk.StringVar(value="")
        self.audio_var = tk.StringVar(value="")
        self.setup_var = tk.StringVar(value="")
        self.docs_var = tk.StringVar(value="")
        self.compressed_var = tk.StringVar(value="")
        self.others_var = tk.StringVar(value="")
        self.mode_var = tk.StringVar(value="move")
        self.running = False

        self._build_ui()
        self.apply_theme()
        self.scan_sizes()

    def apply_theme(self):
        """Apply the current theme to all widgets"""
        theme = 'dark' if self.dark_mode.get() else 'light'
        colors = self.colors[theme]
        
        self.configure(bg=colors['bg'])
        
        # Configure styles
        self.style.configure('Title.TLabel', 
                            font=('Arial', 14, 'bold'),
                            background=colors['bg'],
                            foreground=colors['fg'])
        
        self.style.configure('TFrame', background=colors['bg'])
        self.style.configure('TLabelframe', background=colors['bg'], foreground=colors['fg'])
        self.style.configure('TLabelframe.Label', background=colors['bg'], foreground=colors['fg'])
        
        self.style.configure('Action.TButton',
                            font=('Arial', 10, 'bold'),
                            padding=(10, 5))
        
        self.style.configure('Accent.TButton',
                            background=colors['accent'],
                            foreground="white",
                            font=('Arial', 10, 'bold'),
                            padding=(15, 5))
        
        self.style.configure('Stop.TButton',
                            background=colors['danger'],
                            foreground="white",
                            font=('Arial', 10, 'bold'),
                            padding=(15, 5))
        
        self.style.configure('Success.TButton',
                            background=colors['success'],
                            foreground="white",
                            font=('Arial', 10, 'bold'),
                            padding=(10, 5))
        
        self.style.map('Accent.TButton',
                      background=[('active', '#2980b9')])
        
        self.style.map('Stop.TButton',
                      background=[('active', '#c0392b')])
        
        # Update all widgets
        self._update_widget_colors(self, colors)

    def _update_widget_colors(self, widget, colors):
        """Recursively update widget colors"""
        if isinstance(widget, tk.Text):
            widget.config(bg=colors['text_box_bg'], fg=colors['fg'], 
                         insertbackground=colors['fg'], selectbackground=colors['accent'])
        elif isinstance(widget, tk.Label) and not isinstance(widget, ttk.Label):
            widget.config(bg=colors['bg'], fg=colors['fg'])
        elif isinstance(widget, (tk.Frame, ttk.Frame)):
            try:
                widget.config(bg=colors['bg'])
            except:
                pass
        
        for child in widget.winfo_children():
            self._update_widget_colors(child, colors)

    def _build_ui(self):
        # Create menu bar
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        # Theme menu
        theme_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Theme", menu=theme_menu)
        theme_menu.add_checkbutton(label="Dark Mode", variable=self.dark_mode, 
                                  command=self.toggle_theme)
        
        # Create Notebook for tabs
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Main settings tab
        main_tab = ttk.Frame(notebook, padding=15)
        notebook.add(main_tab, text="Main Settings")
        
        # Logs tab
        log_tab = ttk.Frame(notebook, padding=15)
        notebook.add(log_tab, text="Progress & Logs")

        # Build main tab interface
        self._build_main_tab(main_tab)
        
        # Build logs tab interface
        self._build_log_tab(log_tab)

    def toggle_theme(self):
        """Toggle between light and dark themes"""
        self.apply_theme()

    def _build_main_tab(self, parent):
        # Application title
        title_label = ttk.Label(parent, 
                               text="File Organizer - Downloads Manager",
                               style='Title.TLabel')
        title_label.pack(pady=(0, 15))
        
        # Source folder frame
        source_frame = ttk.LabelFrame(parent, text="Source Folder", padding=10)
        source_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(source_frame, text="Folder Path:").grid(row=0, column=0, sticky=tk.W, pady=5)
        src_entry = ttk.Entry(source_frame, textvariable=self.source_var, width=50)
        src_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        ttk.Button(source_frame, text="Browse", command=self.open_source, width=8).grid(row=0, column=2, padx=5, pady=5)
        
        source_frame.columnconfigure(1, weight=1)
        
        # Statistics frame
        stats_frame = ttk.LabelFrame(parent, text="File Statistics", padding=10)
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.stats_box = tk.Text(stats_frame, height=8, width=80, state=tk.DISABLED, 
                                font=('Consolas', 9))
        self.stats_box.pack(fill=tk.BOTH, expand=True)
        
        # Mini progress bar for main tab
        mini_progress_frame = ttk.Frame(parent)
        mini_progress_frame.pack(fill=tk.X, pady=(5, 10))
        
        ttk.Label(mini_progress_frame, text="Quick Progress:").pack(side=tk.LEFT)
        self.mini_progress = ttk.Progressbar(mini_progress_frame, orient=tk.HORIZONTAL, 
                                            length=300, mode='determinate')
        self.mini_progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
        self.mini_counter = ttk.Label(mini_progress_frame, text="0/0")
        self.mini_counter.pack(side=tk.RIGHT)
        
        # Destination folders frame
        dest_frame = ttk.LabelFrame(parent, text="Destination Folders", padding=10)
        dest_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create scrollable frame
        canvas = tk.Canvas(dest_frame, height=250)
        scrollbar = ttk.Scrollbar(dest_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Add UI elements to scrollable frame
        destinations = [
            ("Images/Videos:", self.images_var, IMAGE_EXT | VIDEO_EXT),
            ("Audio Files:", self.audio_var, AUDIO_EXT),
            ("Setup Files:", self.setup_var, SETUP_EXT),
            ("Documents:", self.docs_var, DOC_EXT),
            ("Compressed Files:", self.compressed_var, COMPRESSED_EXT),
            ("Other Files:", self.others_var, "All other files and folders")
        ]
        
        for i, (label, var, exts) in enumerate(destinations):
            ttk.Label(scrollable_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=5)
            ttk.Entry(scrollable_frame, textvariable=var, width=50).grid(row=i, column=1, sticky=tk.EW, padx=5, pady=5)
            ttk.Button(scrollable_frame, text="Select...", 
                      command=lambda v=var: self.choose_dest(v), width=8).grid(row=i, column=2, padx=5, pady=5)
            
            # Add tooltip showing file types
            tip_text = f"Will move: {', '.join(exts)}" if isinstance(exts, set) else exts
            tip = tk.Label(scrollable_frame, text="ⓘ", foreground="blue", cursor="hand2")
            tip.grid(row=i, column=3, padx=(5, 0))
            self._create_tooltip(tip, tip_text)
        
        scrollable_frame.columnconfigure(1, weight=1)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Options frame
        options_frame = ttk.Frame(parent)
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(options_frame, text="Operation Mode:").pack(side=tk.LEFT)
        ttk.Radiobutton(options_frame, text="Move Files", variable=self.mode_var, value="move").pack(side=tk.LEFT, padx=(15, 5))
        ttk.Radiobutton(options_frame, text="Copy Files", variable=self.mode_var, value="copy").pack(side=tk.LEFT, padx=(5, 15))
        
        # Button frame
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X)
        
        self.start_btn = ttk.Button(button_frame, text="Start Organizing", command=self.start, style='Accent.TButton')
        self.start_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        self.stop_btn = ttk.Button(button_frame, text="Stop", command=self.stop, style='Stop.TButton', state=tk.DISABLED)
        self.stop_btn.pack(side=tk.RIGHT)
        
        ttk.Button(button_frame, text="Rescan Statistics", command=self.scan_sizes, style='Success.TButton').pack(side=tk.LEFT)

    def _build_log_tab(self, parent):
        # Log frame
        log_frame = ttk.LabelFrame(parent, text="Operation Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_box = tk.Text(log_frame, height=15, state=tk.DISABLED, 
                              font=('Consolas', 9))
        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_box.yview)
        self.log_box.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Progress bar frame
        progress_frame = ttk.Frame(parent)
        progress_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(progress_frame, text="Progress:").pack(side=tk.LEFT)
        
        self.progress = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, length=500, mode='determinate')
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
        
        self.counter_label = ttk.Label(progress_frame, text="0/0")
        self.counter_label.pack(side=tk.RIGHT)

    def _create_tooltip(self, widget, text):
        """Create a text tooltip for a widget"""
        tooltip = tk.Toplevel(widget)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_withdraw()
        
        label = ttk.Label(tooltip, text=text, background="#ffffe0", relief="solid", borderwidth=1, 
                         wraplength=300, padding=(5, 2))
        label.pack()
        
        def enter(event):
            x = widget.winfo_rootx() + widget.winfo_width() + 5
            y = widget.winfo_rooty() + widget.winfo_height() // 2
            tooltip.wm_geometry(f"+{x}+{y}")
            tooltip.wm_deiconify()
        
        def leave(event):
            tooltip.wm_withdraw()
        
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)

    def scan_sizes(self):
        source = Path(self.source_var.get())
        if not source.exists():
            self.stats_box.config(state=tk.NORMAL)
            self.stats_box.delete('1.0', tk.END)
            self.stats_box.insert(tk.END, "Source folder does not exist\n")
            self.stats_box.config(state=tk.DISABLED)
            return

        total_size = 0
        total_files = 0
        stats = {
            "Documents": 0,
            "Audio": 0,
            "Setup Files": 0,
            "Images": 0,
            "Videos": 0,
            "Compressed": 0,
            "Other": 0,
        }
        count = {
            "Documents": 0,
            "Audio": 0,
            "Setup Files": 0,
            "Images": 0,
            "Videos": 0,
            "Compressed": 0,
            "Other": 0,
        }

        for root, dirs, files in os.walk(source):
            for file in files:
                try:
                    f = Path(root) / file
                    size = f.stat().st_size
                    total_size += size
                    total_files += 1

                    ext = f.suffix.lower()
                    if ext in DOC_EXT:
                        stats["Documents"] += size
                        count["Documents"] += 1
                    elif ext in AUDIO_EXT:
                        stats["Audio"] += size
                        count["Audio"] += 1
                    elif ext in SETUP_EXT:
                        stats["Setup Files"] += size
                        count["Setup Files"] += 1
                    elif ext in IMAGE_EXT:
                        stats["Images"] += size
                        count["Images"] += 1
                    elif ext in VIDEO_EXT:
                        stats["Videos"] += size
                        count["Videos"] += 1
                    elif ext in COMPRESSED_EXT:
                        stats["Compressed"] += size
                        count["Compressed"] += 1
                    else:
                        stats["Other"] += size
                        count["Other"] += 1
                except Exception:
                    continue

        # Display results
        self.stats_box.config(state=tk.NORMAL)
        self.stats_box.delete('1.0', tk.END)
        self.stats_box.insert(tk.END, f"Total Size: {format_size(total_size)} ({total_files} files)\n\n")
        for cat, size in stats.items():
            percent = (size/total_size*100) if total_size > 0 else 0
            self.stats_box.insert(
                tk.END, 
                f"{cat}: {format_size(size)} ({count[cat]} files, {percent:.1f}%)\n"
            )
        self.stats_box.config(state=tk.DISABLED)

    
    def open_source(self):
        path = filedialog.askdirectory(initialdir=self.source_var.get() or str(DEFAULT_SOURCE))
        if path:
            self.source_var.set(path)
            self.scan_sizes()

    def choose_dest(self, var):
        path = filedialog.askdirectory()
        if path:
            var.set(path)

    def log(self, text):
        self.log_box.config(state=tk.NORMAL)
        self.log_box.insert(tk.END, text + "\n")
        self.log_box.see(tk.END)
        self.log_box.config(state=tk.DISABLED)

    def start(self):
        if self.running:
            return
        src = Path(self.source_var.get())
        if not src.exists() or not src.is_dir():
            messagebox.showerror("Error", "Source folder does not exist")
            return
        if not all([self.images_var.get(), self.audio_var.get(), self.setup_var.get(), 
                   self.docs_var.get(), self.compressed_var.get(), self.others_var.get()]):
            messagebox.showerror("Error", "Please select all destination folders")
            return

        # Disable/enable buttons
        self.running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.progress['value'] = 0
        self.mini_progress['value'] = 0
        self.log_box.config(state=tk.NORMAL)
        self.log_box.delete('1.0', tk.END)
        self.log_box.config(state=tk.DISABLED)

        # Start thread
        t = threading.Thread(target=self._worker, args=(src,))
        t.daemon = True
        t.start()

    def stop(self):
        if not self.running:
            return
        self.running = False
        self.log("Stopping... (will stop after current file)")
        self.stop_btn.config(state=tk.DISABLED)

    def _worker(self, src: Path):
        try:
            items = list(src.iterdir())  # Get files + folders
            total = len(items)
            if total == 0:
                self.log("No items in source folder.")
                self._finish()
                return

            self.progress['maximum'] = total
            self.mini_progress['maximum'] = total
            processed = 0

            for f in items:
                if not self.running:
                    break
                try:
                    if f.is_dir():
                        # Folders go to Others
                        dest = Path(self.others_var.get())
                        target = dest / f.name
                        if target.exists():
                            i = 1
                            while (dest / f"{f.name}({i})").exists():
                                i += 1
                            target = dest / f"{f.name}({i})"

                        if self.mode_var.get() == 'move':
                            shutil.move(str(f), str(target))
                            self.log(f"Moved folder: {f.name} -> {target}")
                        else:
                            shutil.copytree(str(f), str(target))
                            self.log(f"Copied folder: {f.name} -> {target}")

                    else:
                        # Process files
                        ext = f.suffix.lower()
                        if ext in IMAGE_EXT or ext in VIDEO_EXT:
                            dest = Path(self.images_var.get())
                        elif ext in DOC_EXT:
                            dest = Path(self.docs_var.get())
                        elif ext in AUDIO_EXT:
                            dest = Path(self.audio_var.get())
                        elif ext in SETUP_EXT:
                            dest = Path(self.setup_var.get())
                        elif ext in COMPRESSED_EXT:
                            dest = Path(self.compressed_var.get())
                        else:
                            dest = Path(self.others_var.get())

                        target = dest / f.name
                        if target.exists():
                            base, suf = f.stem, f.suffix
                            i = 1
                            while (dest / f"{base}({i}){suf}").exists():
                                i += 1
                            target = dest / f"{base}({i}){suf}"

                        if self.mode_var.get() == 'move':
                            shutil.move(str(f), str(target))
                            self.log(f"Moved: {f.name} -> {target}")
                        else:
                            shutil.copy2(str(f), str(target))
                            self.log(f"Copied: {f.name} -> {target}")

                except Exception as e:
                    self.log(f"Error processing {f.name}: {e}")
                    traceback.print_exc()

                processed += 1
                percent = (processed / total) * 100
                self.progress['value'] = processed
                self.mini_progress['value'] = processed
                self.counter_label.config(text=f"{processed}/{total} ({percent:.1f}%)")
                self.mini_counter.config(text=f"{processed}/{total}")

            if not self.running:
                self.log("Operation stopped before completion.")
            else:
                self.log(f"Operation completed: {processed} items processed.")

        except Exception as e:
            self.log(f"Error: {e}")
            traceback.print_exc()
        finally:
            self._finish()

    def _finish(self):
        self.running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.scan_sizes()  # Update statistics after completion


if __name__ == '__main__':
    app = App()
    app.mainloop()