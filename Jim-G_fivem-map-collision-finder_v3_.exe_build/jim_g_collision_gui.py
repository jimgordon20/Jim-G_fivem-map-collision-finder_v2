import os
import hashlib
import fnmatch
from collections import defaultdict
from datetime import datetime
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Tuple, List, Dict, Any


try:
    from ttkthemes import ThemedTk
    THEMED_TK_AVAILABLE = True
except ImportError:
    THEMED_TK_AVAILABLE = False
    

ALL_MAP_RELATED_FILES = {
    "*.ymap": "Map Data (Map Placement/Details)",
    "light_ymaps": "Light Map Files (lodlights*.ymap / vw_*.ymap)",
    "*.ybn": "Bounds/Collision Data",
    "*.ymt": "Meta/Config Files",
    "*.ytd": "Textures Dictionary",
    "*.ydr": "Drawable (3D Models)",
    "*.ydd": "Drawable Dictionary (Model Container)",
    "*.ytyp": "Types/Manifest (Map/MLO Definitions)",
    "*.ycd": "Clip Dictionary (Animations)",
    "*.ynv": "Navigation Mesh (AI Navigation)",
    "*.ypt": "Particle Effects (FX)"
}

def get_file_hash(file_path):
    """Calculates the MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception:
        return None

def find_collisions(directory: str, file_patterns: List[str], lightmap_exclusion: bool, progress_callback: Callable[[int, str], None] = None) -> Tuple[Dict[str, Any], List[str], List[str]]:
    """
    Scans the directory for files matching the patterns and finds collisions, reporting progress.
    """
    file_list = []
    lightmap_patterns = ('lodlights*.ymap', 'vw_*.ymap')
    files_to_search_list = file_patterns[:] 
    ignored_patterns_list = [p for p in ALL_MAP_RELATED_FILES if p not in files_to_search_list and p != "light_ymaps"]
    if lightmap_exclusion:
        ignored_patterns_list.append("light_ymaps_ignored")
    elif "*.ymap" in files_to_search_list:
        files_to_search_list.append("light_ymaps")
    if progress_callback:
        progress_callback(5, "Collecting file paths...")
    for root, _, filenames in os.walk(directory):
        resource_path_parts = os.path.relpath(root, directory).split(os.path.sep)
        resource_name = resource_path_parts[0] if resource_path_parts and resource_path_parts[0] != '.' else "ROOT_DIR"     
        for filename in filenames:
            filename_lower = filename.lower()           
            is_lightmap = lightmap_exclusion and filename_lower.endswith('.ymap') and any(fnmatch.fnmatch(filename_lower, pattern) for pattern in lightmap_patterns)
            if is_lightmap:
                continue
            matched = any(fnmatch.fnmatch(filename_lower, pattern) for pattern in file_patterns)
            if matched:
                file_list.append({
                    'path': os.path.join(root, filename), 
                    'filename_lower': filename_lower,
                    'resource': resource_name
                })
    total_files = len(file_list)
    if total_files == 0:
        if progress_callback:
            progress_callback(100, "No relevant files found.")
        return defaultdict(lambda: {'conflicts': defaultdict(list), 'duplicates': defaultdict(list)}), files_to_search_list, ignored_patterns_list
    file_info_dict = defaultdict(list)
    current_progress = 0
    
    for file_data in file_list:
        file_hash = get_file_hash(file_data['path']) 
        
        if file_hash:
            file_key = file_data['filename_lower']
            relative_path = os.path.relpath(file_data['path'], directory) 
            file_info_dict[file_key].append({
                "path": relative_path, 
                "hash": file_hash,
                "resource": file_data['resource']
            })

        current_progress += 1
        if progress_callback:
            percentage = 10 + int((current_progress / total_files) * 80)
            progress_callback(percentage, f"Hashing files: {current_progress}/{total_files}")
    if progress_callback:
        progress_callback(95, "Analyzing results...")
    categorized_results = defaultdict(lambda: {'conflicts': defaultdict(list), 'duplicates': defaultdict(list)})
    for filename, infos in file_info_dict.items():
        if len(infos) > 1:
            file_extension = os.path.splitext(filename)[1].upper()
            unique_hashes = set(info['hash'] for info in infos)
            if len(unique_hashes) > 1:
                categorized_results[file_extension]['conflicts'][filename].extend(infos)
            else:
                categorized_results[file_extension]['duplicates'][filename].extend(infos)

    return categorized_results, files_to_search_list, ignored_patterns_list

def generate_html_report(directory, categorized_results, total_conflicts, total_duplicates, files_to_search, ignored_patterns):
    """Generates the HTML report with the dark-themed CSS."""
    searched_patterns_report = [p for p in files_to_search if p != 'light_ymaps']
    if "light_ymaps_ignored" not in ignored_patterns:
        searched_patterns_report.append("*.ymap (including lights)")
    patterns_ignored_report = [p for p in ignored_patterns if p != 'light_ymaps_ignored']
    if "light_ymaps_ignored" in ignored_patterns:
        patterns_ignored_report.append("lodlights*.ymap/vw_*.ymap")
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jim-G FiveM Map Collision Report</title>
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            background-color: #1e1e1e; 
            color: #d4d4d4; 
            padding-bottom: 50px;
        }}
        .container {{ 
            max-width: 1800px;
            margin: 20px auto; 
            padding: 0 40px;
        }}
        .header {{ 
            background-color: #252526; 
            color: #4ec9b0; 
            padding: 40px 50px;
            border-radius: 8px; 
            margin-bottom: 30px; 
            box-shadow: 0 6px 15px rgba(0, 0, 0, 0.4); 
        }}
        .header h1 {{ margin: 0; font-size: 2.4em; }}
        .header p {{ margin: 5px 0; font-size: 0.95em; }}
        .summary {{ 
            display: flex; 
            justify-content: space-around; 
            background-color: #333333; 
            padding: 20px; 
            border-radius: 8px; 
            margin-bottom: 40px; 
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3); 
        }}
        .summary div {{ padding: 0 20px; text-align: center; }}
        .conflict-count {{ font-size: 1.8em; font-weight: bold; color: #f44747; }}
        .duplicate-count {{ font-size: 1.8em; font-weight: bold; color: #ffeb95; }}
        h2 {{ border-bottom: 2px solid #3c3c3c; padding-bottom: 10px; margin-top: 50px; color: #569cd6; font-size: 2.0em; }}
        h3 {{ color: #dcdcaa; margin-top: 35px; font-size: 1.5em; }}
        .report-section {{ 
            background-color: #2d2d30; 
            padding: 30px;
            border-radius: 8px; 
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.4); 
            margin-bottom: 40px; 
        }}

        table {{ width: 100%; border-collapse: separate; border-spacing: 0 10px; margin-top: 20px; }}
        th, td {{ 
            padding: 22px;
            text-align: left; 
            border: none; 
            word-break: break-word; 
            font-size: 1.1em;
        }} 
        th {{ background-color: #3c3c3c; color: #d4d4d4; font-weight: 600; text-transform: uppercase; }}
        tr {{ background-color: #252526; transition: background-color 0.2s; }}
        tr:hover {{ background-color: #3a3a3d; }}
        .conflict-type {{ background-color: #3a1a1a; border-left: 5px solid #f44747; padding: 15px; margin-top: 20px; margin-bottom: 20px; font-weight: bold; color: #f44747; border-radius: 4px; }}
        .duplicate-type {{ background-color: #3a3a1a; border-left: 5px solid #ffeb95; padding: 15px; margin-top: 20px; margin-bottom: 20px; font-weight: bold; color: #ffeb95; border-radius: 4px; }}
        .resolution-status {{ text-align: center; width: 60px; }}
        .resolution-box {{ display: none; }}
        .resolution-status label {{
            display: inline-block;
            width: 24px;
            height: 24px;
            text-align: center;
            line-height: 24px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 1.2em;
            font-weight: bold;
            transition: all 0.1s ease-in-out;
            background-color: #3c3c3c;
        }}
        .resolution-box + label::before {{
            content: '✗'; 
            color: #f44747;
            
        }}
        .resolution-box:checked + label::before {{ 
            content: '✓'; 
            color: #4ec9b0;
        }}
        .resolution-box:focus + label {{
            box-shadow: 0 0 0 2px #007acc;
        }}
        .copy-btn {{
            background-color: #569cd6;
            color: white;
            border: none;
            padding: 8px 12px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 0.9em;
            margin: 4px 2px;
            cursor: pointer;
            border-radius: 4px;
            transition: background-color 0.3s ease;
        }}
        .copy-btn:hover {{
            background-color: #4c8cd2;
        }}
        
    </style>
</head>
<body>
    
    <div class="container">
        <div class="header">
            <h1>Jim-G FiveM Map Collision Report</h1>
            <p>Scan Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <p>Target Directory: {directory}</p>
            <p>File Patterns Searched: {', '.join(searched_patterns_report)}</p>
            <p>File Patterns Ignored: {', '.join(patterns_ignored_report)}</p>
        </div>

        <div class="summary">
            <div>Total Critical Conflicts: <span class="conflict-count">{total_conflicts}</span></div>
            <div>Total Redundant Duplicates: <span class="duplicate-count">{total_duplicates}</span></div>
        </div>

        <div class="report-section">
        <h2>Detailed Report</h2>
        """ 
    if not categorized_results:
        html += "<p>No collisions or duplicates found! ✨</p>"
    checkbox_id_counter = 0
    for ext, data in sorted(categorized_results.items()):
        if not data['conflicts'] and not data['duplicates']:
            continue
        html += f"<h3>--- {ext} Collisions ---</h3>"
        if data['conflicts']:
            html += """
            <div class="conflict-type">CRITICAL CONFLICTS (Same Name, Different Content)</div>
            <table>
                <tr>
                    <th class="resolution-status">Status</th>
                    <th>Colliding File</th>
                    <th>Resource</th>
                    <th>Full Path</th>
                    <th>Copy Path</th>
                </tr>
            """
            for filename, items in data['conflicts'].items():
                is_first_entry = True
                checkbox_id_counter += 1
                checkbox_name = f"conflict_{checkbox_id_counter}"
                for item in items:
                    full_path_js = item['path'].replace('\\', '/')  
                    html += f"""
                    <tr>
                        <td class="resolution-status">
                            {'<input type="checkbox" id="{name}" name="{name}" class="resolution-box" data-filename="{fn}"><label for="{name}"></label>'.format(name=checkbox_name, fn=filename) if is_first_entry else ''}
                        </td>
                        <td style="font-weight: bold;">{"<br>" if not is_first_entry else ""}{filename if is_first_entry else ""}</td>
                        <td>{item['resource']}</td>
                        <td>{item['path']}</td>
                        <td><button class="copy-btn" onclick="copyPathToClipboard('{full_path_js}')">Copy Dir</button></td>
                    </tr>
                    """
                    is_first_entry = False
            html += "</table>"
        if data['duplicates']:
            html += """
            <div class="duplicate-type">REDUNDANT DUPLICATES (Same Name, Identical Content)</div>
            <table>
                <tr>
                    <th class="resolution-status">Status</th>
                    <th>Duplicate File</th>
                    <th>Resource</th>
                    <th>Full Path</th>
                    <th>Copy Path</th>
                </tr>
            """
            for filename, items in data['duplicates'].items():
                is_first_entry = True
                checkbox_id_counter += 1
                checkbox_name = f"duplicate_{checkbox_id_counter}"
                
                for item in items:
                    full_path_js = item['path'].replace('\\', '/')
                    
                    html += f"""
                    <tr>
                        <td class="resolution-status">
                            {'<input type="checkbox" id="{name}" name="{name}" class="resolution-box" data-filename="{fn}"><label for="{name}"></label>'.format(name=checkbox_name, fn=filename) if is_first_entry else ''}
                        </td>
                        <td style="font-weight: bold;">{"<br>" if not is_first_entry else ""}{filename if is_first_entry else ""}</td>
                        <td>{item['resource']}</td>
                        <td>{item['path']}</td>
                        <td><button class="copy-btn" onclick="copyPathToClipboard('{full_path_js}')">Copy Dir</button></td>
                    </tr>
                    """
                    is_first_entry = False
            html += "</table>"
    html += f"""
        </div>
    </div>
    
    <script>
        function copyPathToClipboard(relativePath) {{
            const lastSeparatorIndex = relativePath.lastIndexOf('/');
            let directoryPath = relativePath.substring(0, lastSeparatorIndex + 1);
            directoryPath = directoryPath.replace(/\\//g, '\\\\');
            
            if (directoryPath.startsWith('.')) {{ directoryPath = directoryPath.substring(1); }}
            if (directoryPath.startsWith('\\\\')) {{ directoryPath = directoryPath.substring(1); }}

            if (navigator.clipboard && window.isSecureContext) {{
                navigator.clipboard.writeText(directoryPath).then(() => {{
                    // Visual feedback (optional)
                    alert('Copied directory path to clipboard: ' + directoryPath);
                }}).catch(err => {{
                    console.error('Could not copy text: ', err);
                    alert('Failed to copy. Directory path: ' + directoryPath);
                }});
            }} else {{
                const textArea = document.createElement("textarea");
                textArea.value = directoryPath;
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                try {{
                    document.execCommand('copy');
                    alert('Copied directory path to clipboard: ' + directoryPath);
                }} catch (err) {{
                    console.error('Fallback: Oops, unable to copy', err);
                    alert('Failed to copy. Directory path: ' + directoryPath);
                }}
                document.body.removeChild(textArea);
            }}
        }}
    </script>
    
    </body>
</html>
    """
    return html

def _generate_lua_report(directory, categorized_results, total_conflicts, total_duplicates, files_to_search, ignored_patterns):
    lua_output_lines = []
    patterns_searched_for_report = [p for p in files_to_search if p != 'light_ymaps']
    if "light_ymaps_ignored" not in (ignored_patterns if ignored_patterns else []):
        patterns_searched_for_report.append("*.ymap (including lights)")
    patterns_ignored_for_report = [p for p in ignored_patterns if p != 'light_ymaps_ignored']
    if "light_ymaps_ignored" in (ignored_patterns if ignored_patterns else []):
        patterns_ignored_for_report.append("lodlights*.ymap/vw_*.ymap")
    lua_output_lines.append(f'-- ###################################################')
    lua_output_lines.append(f'-- #       JIM-G FIVEM MAP COLLISION REPORT (LUA)    #')
    lua_output_lines.append(f'-- ###################################################')
    lua_output_lines.append(f'-- Scan Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    lua_output_lines.append(f'-- Target Directory: {directory}')
    lua_output_lines.append(f'-- File Patterns Searched: {", ".join(patterns_searched_for_report) if patterns_searched_for_report else "NONE"}')
    lua_output_lines.append(f'-- File Patterns Ignored: {", ".join(patterns_ignored_for_report) if patterns_ignored_for_report else "NONE"}')
    lua_output_lines.append(f'\n')
    is_first_category = True
    separator = "--############################################################################################################################################################################################################################################################--"
    for ext, data in sorted(categorized_results.items()):
        if not data['conflicts'] and not data['duplicates']: continue
        if not is_first_category: lua_output_lines.append(separator)
        is_first_category = False
        header = f"-- --- {ext} Collisions ---" 
        lua_output_lines.append(header)
        if data['conflicts']:
            conflict_line = " -- [CRITICAL CONFLICTS] (Same Name, Different Content)"
            lua_output_lines.append(conflict_line)
            for filename, items in data['conflicts'].items():
                lua_output_lines.append(f"  -- - File: {filename}")
                for item in items:
                    lua_output_lines.append(f"    - Resource: {item['resource']:<25} Path: {item['path']}")
        if data['duplicates']:
            duplicate_line = " -- [Redundant Duplicates] (Same Name, Identical Content)"
            lua_output_lines.append(duplicate_line)
            for filename, items in data['duplicates'].items():
                lua_output_lines.append(f"  -- - File: {filename}")
                for item in items:
                    lua_output_lines.append(f"    - Resource: {item['resource']:<25} Path: {item['path']}")
    lua_output_lines.append(f'\n') 
    lua_output_lines.append(f'-- --- Final Summary ---')
    lua_output_lines.append(f'-- Total Critical Conflicts Found: {total_conflicts}')
    lua_output_lines.append(f'-- Total Redundant Duplicates Found: {total_duplicates}')
    lua_output_lines.append(f'-- ###################################################')
    return '\n'.join(lua_output_lines)

class ConflictCheckerApp:
    def __init__(self, master):
        self.master = master
        master.title("Jim-G FiveM Collision Finder")
        self.scan_dir = tk.StringVar(value="")
        self.output_file = tk.StringVar(value=os.path.join(os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__), "collision_report.html"))
        self.format_var = tk.StringVar(value="html")
        self.file_vars = {}      
        master.geometry("600x700")
        master.resizable(False, False)
        if THEMED_TK_AVAILABLE:
            master.set_theme("black") 
            style = ttk.Style()
            style.configure('TLabel', foreground='#d4d4d4') 
            style.configure('TLabelframe', foreground='#569cd6', font=('Segoe UI', 10, 'bold')) 
            style.configure('TCheckbutton', foreground='#d4d4d4')
            style.configure('TRadiobutton', foreground='#d4d4d4')
            style.configure('TEntry', fieldbackground='#1e1e1e', foreground='#d4d4d4', borderwidth=1, bordercolor='#3c3c3c')
            style.configure('Modern.TButton', 
                            font=('Segoe UI', 10, 'bold'),
                            foreground='#ffffff', 
                            background='#569cd6', 
                            bordercolor='#569cd6', 
                            borderwidth=0,
                            relief='flat',
                            padding=(15, 10)
                           )
            style.map('Modern.TButton', 
                      background=[('active', '#4c8cd2'), ('pressed', '#3a76b7')],
                      foreground=[('active', '#ffffff')]
                     )
            style.configure("TProgressbar", 
                            troughcolor='#333333', 
                            background='#4ec9b0',
                            thickness=10,
                            borderwidth=0)
            status_fg = '#4ec9b0'
        else:
            status_fg = '#569cd6'
        main_frame = ttk.Frame(master, padding="15 15 15 15")
        main_frame.pack(fill='both', expand=True)
        dir_frame = ttk.LabelFrame(main_frame, text="1. Select FiveM Resources Folder", padding="10")
        dir_frame.pack(fill='x', pady=10)
        ttk.Label(dir_frame, text="Target Directory:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        dir_entry = ttk.Entry(dir_frame, textvariable=self.scan_dir, width=50)
        dir_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        dir_frame.grid_columnconfigure(1, weight=1)
        browse_btn = ttk.Button(dir_frame, text="Browse...", command=self.select_directory, style='Modern.TButton')
        browse_btn.grid(row=0, column=2, padx=5, pady=5)
        type_frame = ttk.LabelFrame(main_frame, text="2. Select File Types to Scan", padding="10")
        type_frame.pack(fill='x', pady=10)
        canvas = tk.Canvas(type_frame, height=200, borderwidth=0, highlightthickness=0)
        v_scrollbar = ttk.Scrollbar(type_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, padding="5")
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=v_scrollbar.set)       
        canvas.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        row = 0
        for pattern, description in ALL_MAP_RELATED_FILES.items():
            default_value = False if pattern == "light_ymaps" else True
            self.file_vars[pattern] = tk.BooleanVar(value=default_value)
            text = f"Ignore Light Maps ({description})" if pattern == "light_ymaps" else f"Search for {pattern} ({description})"
            cb = ttk.Checkbutton(scrollable_frame, text=text, variable=self.file_vars[pattern])
            cb.grid(row=row, column=0, sticky='w', pady=2)
            row += 1
        button_frame = ttk.Frame(type_frame)
        button_frame.pack(fill='x', pady=(10, 0))
        ttk.Button(button_frame, text="Select All", command=lambda: self.set_all_checkboxes(True), style='Modern.TButton').pack(side='left', fill='x', expand=True, padx=5)
        ttk.Button(button_frame, text="Deselect All", command=lambda: self.set_all_checkboxes(False), style='Modern.TButton').pack(side='left', fill='x', expand=True, padx=5)
        output_frame = ttk.LabelFrame(main_frame, text="3. Output Settings", padding="10")
        output_frame.pack(fill='x', pady=10)
        ttk.Label(output_frame, text="Report Format:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        ttk.Radiobutton(output_frame, text="HTML (Recommended)", variable=self.format_var, value="html", command=self.update_output_file_name).grid(row=0, column=1, sticky='w', padx=5, pady=5)
        ttk.Radiobutton(output_frame, text="Lua (.lua)", variable=self.format_var, value="lua", command=self.update_output_file_name).grid(row=0, column=2, sticky='w', padx=5, pady=5)
        ttk.Label(output_frame, text="Output File Path:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        output_entry = ttk.Entry(output_frame, textvariable=self.output_file, width=50)
        output_entry.grid(row=1, column=1, columnspan=2, sticky='ew', padx=5, pady=5)
        output_frame.grid_columnconfigure(1, weight=1)
        save_btn = ttk.Button(output_frame, text="Save As...", command=self.select_output_file, style='Modern.TButton')
        save_btn.grid(row=1, column=3, padx=5, pady=5)
        self.progress_bar = ttk.Progressbar(main_frame, orient="horizontal", mode='determinate', style="TProgressbar")
        self.progress_bar.pack(fill='x', pady=(10, 0))
        self.progress_bar.config(value=0) 
        run_btn = ttk.Button(main_frame, text="Start Collision Check", command=self.run_checker, style='Modern.TButton')
        run_btn.pack(fill='x', pady=(5, 20))
        self.status_bar = ttk.Label(main_frame, text="Ready. Select a directory and start the scan.", anchor='w', foreground=status_fg)
        self.status_bar.pack(fill='x', side='bottom', pady=5)
        
        self.run_button = run_btn

    def set_all_checkboxes(self, value):
        """Sets all file type checkboxes to True or False."""
        for pattern, var in self.file_vars.items():
            if pattern == 'light_ymaps':
                var.set(not value) 
                continue
            var.set(value)

    def select_directory(self):
        """Opens a file dialog to select the resource directory."""
        initial_dir = os.path.expanduser("~") 
        directory = filedialog.askdirectory(initialdir=initial_dir, title="Select FiveM Resources Folder")
        if directory:
            self.scan_dir.set(directory)

    def update_output_file_name(self):
        """Updates the default output file name based on the selected format."""
        current_path = self.output_file.get()
        base, ext = os.path.splitext(current_path)
        
        new_ext = f".{self.format_var.get()}"
            
        if ext.lower() in ['.html', '.lua'] or base.endswith("collision_report"):
            self.output_file.set(base + new_ext)
        elif not ext: 
            self.output_file.set(current_path + new_ext)

    def select_output_file(self):
        """Opens a file dialog to choose the output file path and name."""
        file_format = self.format_var.get()
        if file_format == "html":
            filetypes = [("HTML file", "*.html")]
        else:
            filetypes = [("Lua Script", "*.lua")]
            
        initial_file = os.path.basename(self.output_file.get())
        initial_dir = os.path.dirname(self.output_file.get())
            
        filepath = filedialog.asksaveasfilename(
            defaultextension=f".{file_format}",
            filetypes=filetypes,
            initialfile=initial_file,
            initialdir=initial_dir
        )
        if filepath:
            self.output_file.set(filepath)

    def update_progress(self, percentage, message):
        """Helper function for real-time progress updates."""
        self.progress_bar.config(value=percentage)
        self.status_bar.config(text=f"[{percentage}%] {message}")
        self.master.update_idletasks()

    def run_checker(self):
        """Validates inputs and starts the collision check."""
        target_dir = self.scan_dir.get()
        output_path = self.output_file.get()
        output_format = self.format_var.get()

        if not target_dir or not os.path.isdir(target_dir):
            messagebox.showerror("Error", "Please select a valid FiveM Resources Folder.")
            return
        self.run_button.config(state=tk.DISABLED)
        self.progress_bar.config(value=0)
        self.status_bar.config(text="Starting scan...", foreground='#ff9900')
        self.master.update()
        selected_patterns = [p for p, v in self.file_vars.items() if p != 'light_ymaps' and v.get()]
        lightmap_exclusion = self.file_vars['light_ymaps'].get()
        
        try:
            categorized_results, files_to_search_list, ignored_patterns_list = find_collisions(
                target_dir, 
                selected_patterns, 
                lightmap_exclusion,
                progress_callback=self.update_progress
            )
            total_conflicts = sum(len(data['conflicts']) for ext, data in categorized_results.items())
            total_duplicates = sum(len(data['duplicates']) for ext, data in categorized_results.items())
            self.update_progress(98, "Generating report file...")
            if output_format == 'html':
                report_content = generate_html_report(target_dir, categorized_results, total_conflicts, total_duplicates, files_to_search_list, ignored_patterns_list)
            else: 
                report_content = _generate_lua_report(target_dir, categorized_results, total_conflicts, total_duplicates, files_to_search_list, ignored_patterns_list)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            self.progress_bar.config(value=100)
            self.run_button.config(state=tk.NORMAL)
            messagebox.showinfo(
                "Scan Complete",
                f"Scan finished successfully!\n\n"
                f"Total Critical Conflicts Found: {total_conflicts}\n"
                f"Total Redundant Duplicates Found: {total_duplicates}\n"
                f"Report saved to:\n{output_path}"
            )
            self.status_bar.config(text=f"Scan complete. Found {total_conflicts} critical conflicts.", foreground='#4caf50')
        except Exception as e:
            error_message = f"An unexpected error occurred during the scan:\n{e}"
            messagebox.showerror("Error", error_message)
            self.status_bar.config(text="Scan failed. Check error log.", foreground='#f44336')
            self.run_button.config(state=tk.NORMAL)
            self.progress_bar.config(value=0)
if __name__ == "__main__":
    if THEMED_TK_AVAILABLE:
        root = ThemedTk(theme="black") 
    else:
        root = tk.Tk()
        root.config(bg='#2d2d30')
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('.', background='#2d2d30', foreground='#d4d4d4')
        style.map('TButton', background=[('active', '!focus', '#444444')], foreground=[('active', '#ffffff')])
        messagebox.showwarning("Theme Warning", "ttkthemes not installed. The GUI may appear with a fallback theme. For the intended dark, modern GUI, install it with 'pip install ttkthemes'.")
    
    app = ConflictCheckerApp(root)
    root.mainloop()