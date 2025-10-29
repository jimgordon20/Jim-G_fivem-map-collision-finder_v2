import os
import argparse
import hashlib
import fnmatch
from collections import defaultdict
from datetime import datetime
import sys

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class DummyColor:
        def __getattr__(self, name): return ""
    Fore = DummyColor()
    Style = DummyColor()

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, **kwargs):
        return iterable

ALL_MAP_RELATED_FILES = {
    "*.ymap": "Map Data (Map Placement/Details) (Highly Recommended)",
    "light_ymaps": "Light Map Files (lodlights*.ymap / vw_*.ymap) (Recommended)",
    "*.ybn": "Bounds/Collision Data (Highly Recommended)",
    "*.ymt": "Meta/Config Files (Recommended)",
    "*.ytd": "Textures Dictionary (Recommended)",
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
    except IOError:
        return None

def get_files_to_search_interactively():
    """
    Asks the user, one by one, which file types to search for based on the new order.
    Returns a tuple: (list of patterns to SEARCH for, list of patterns to IGNORE).
    """
    search_patterns = []
    light_map_ignored = False
    print(Fore.YELLOW + "--- File Type Selection ---")
    print("For each file type, enter '1' for YES (Search) or '2' for NO (Ignore).")
    print(Fore.YELLOW + "Press ENTER to accept the default recommendation (if provided)." + Style.RESET_ALL)
    print("-" * 35)
    for pattern, description in ALL_MAP_RELATED_FILES.items():
        is_recommended = "Highly Recommended" in description or "Recommended" in description    
        while True:
            default_choice = "1" if is_recommended else "2"
            prompt = f"Search for {Fore.YELLOW}{pattern}{Style.RESET_ALL} ({description})? (1) YES / (2) NO: "
            choice = input(prompt).strip()
            if not choice:
                choice = default_choice
                print(f"  -> Default selected: {Fore.CYAN}{choice}{Style.RESET_ALL}")
            if choice == '1':
                if pattern != "light_ymaps":
                    search_patterns.append(pattern)
                    print(f"  -> {Fore.GREEN}Searching{Style.RESET_ALL} for {pattern}.")
                else:
                    print(f"  -> {Fore.GREEN}Searching{Style.RESET_ALL} all *.ymap files.")
                break
            elif choice == '2':
                if pattern != "light_ymaps":
                    print(f"  -> {Fore.RED}Ignoring{Style.RESET_ALL} {pattern}.")
                else:
                    light_map_ignored = True
                    print(f"  -> {Fore.RED}Ignoring{Style.RESET_ALL} Light Map Files (lodlights* / vw_*).")
                break
            else:
                print(Fore.RED + "Invalid input. Please enter '1' or '2'.")
    ignored_patterns = [p for p in ALL_MAP_RELATED_FILES if p not in search_patterns and p != "light_ymaps"]
    if light_map_ignored:
        ignored_patterns.append("light_ymaps_ignored")
    print(Fore.YELLOW + "\n" + "=" * 50)
    print(Fore.YELLOW + "--- FINAL SCAN CONFIGURATION ---")
    searched_for_display = [p for p in ALL_MAP_RELATED_FILES if p in search_patterns and p != 'light_ymaps']
    if "*.ymap" in search_patterns and "light_ymaps_ignored" not in ignored_patterns:
        if "*.ymap" in searched_for_display:
            searched_for_display.remove("*.ymap")
        searched_for_display.append("*.ymap (including Light Maps)")
    elif "*.ymap" in search_patterns and "light_ymaps_ignored" in ignored_patterns:
        pass
    print(Fore.GREEN + "\nFile Types to SEARCH FOR:")
    if searched_for_display:
        for p in searched_for_display:
             base_pattern = p.split(' ')[0] 
             description = ALL_MAP_RELATED_FILES.get(base_pattern, '')
             if 'Light Maps' in p:
                 description = "Map Data / Light Map Files"
             print(f"  - {p} ({description})")
    else:
        print(Fore.RED + "  - NONE (The scan will find nothing!)")
    ignored_for_display = [p for p in ignored_patterns if p != "light_ymaps_ignored"]
    if "light_ymaps_ignored" in ignored_patterns:
        ignored_for_display.append("lodlights*.ymap / vw_*.ymap")
    print(Fore.RED + "\nFile Types to IGNORE:")
    if ignored_for_display:
        for p in ignored_for_display:
             if p.startswith('lodlights'):
                print(f"  - {p}")
             else:
                print(f"  - {p} ({ALL_MAP_RELATED_FILES.get(p, 'Custom Rule')})")
    else:
        print(Fore.GREEN + "  - NONE")
    print(Fore.YELLOW + "=" * 50)
    input(Fore.YELLOW + "\nPress ENTER to start the collision search...")
    return search_patterns, ignored_patterns

def _generate_html_report(directory, categorized_results, total_conflicts, total_duplicates, files_to_search, ignored_patterns):
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
        function copyPathToClipboard(fullPath) {{
            const lastSeparatorIndex = fullPath.lastIndexOf('/');
            let directoryPath = fullPath.substring(0, lastSeparatorIndex + 1);
            directoryPath = directoryPath.replace(/\\//g, '\\\\');
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

def find_collisions(directory, files_to_search=None, ignored_patterns=None, output_file=None, output_format="lua"):
    """
    Finds file collisions in a directory, categorizing them by type and content hash.
    """
    file_info_dict = defaultdict(list)
    files_to_process = []
    ignore_light_ymaps = "light_ymaps_ignored" in (ignored_patterns if ignored_patterns else [])
    print("Finding all relevant map files...")
    for foldername, _, filenames in os.walk(directory):
        for filename in filenames:
            filename_lower = filename.lower()
            if files_to_search and any(fnmatch.fnmatch(filename_lower, pattern) for pattern in files_to_search):
                is_light_ymap = ignore_light_ymaps and filename_lower.endswith('.ymap') and (filename_lower.startswith('lodlights') or filename_lower.startswith('vw_'))
                if is_light_ymap:
                    continue      
                file_path = os.path.normpath(os.path.join(foldername, filename))
                files_to_process.append(file_path)
    print(f"Found {len(files_to_process)} files. Now hashing them to check for conflicts...")
    for file_path in tqdm(files_to_process, desc="Hashing files", unit="file", file=sys.stdout):
        filename = os.path.basename(file_path)
        file_hash = get_file_hash(file_path)
        relative_path = os.path.relpath(file_path, directory)
        resource_parts = relative_path.split(os.sep)
        resource_name = resource_parts[0] if resource_parts else "UNKNOWN_RESOURCE"
        if file_hash:
            file_key = filename.lower()
            file_info_dict[file_key].append({
                "path": file_path,
                "hash": file_hash,
                "resource": resource_name
            })
    print("\nProcessing results...")
    categorized_results = defaultdict(lambda: {'conflicts': defaultdict(list), 'duplicates': defaultdict(list)})
    total_conflicts = 0
    total_duplicates = 0
    for filename, infos in file_info_dict.items():
        if len(infos) > 1:
            file_extension = os.path.splitext(filename)[1].upper()
            unique_hashes = set(info['hash'] for info in infos)
            if len(unique_hashes) > 1:
                categorized_results[file_extension]['conflicts'][filename].extend(infos)
                total_conflicts += len(unique_hashes)
            else:
                categorized_results[file_extension]['duplicates'][filename].extend(infos)
                total_duplicates += 1
    is_first_category = True
    print(Fore.WHITE + "\n--- Detailed Console Report ---")
    for ext, data in sorted(categorized_results.items()):
        if not data['conflicts'] and not data['duplicates']:
            continue   
        if not is_first_category: print("-" * 50)
        is_first_category = False
        header = f"--- {ext} Collisions ---" 
        print(Style.BRIGHT + header)
        if data['conflicts']:
            print(Fore.RED + Style.BRIGHT + "[CRITICAL CONFLICTS] (Same Name, Different Content)")
            for filename, items in data['conflicts'].items():
                print(f"  - File: {Fore.YELLOW}{filename}{Style.RESET_ALL}")
                for item in items:
                    print(f"    - Resource: {item['resource']:<25} Path: {item['path']}")
        if data['duplicates']:
            print(Fore.YELLOW + Style.BRIGHT + "[Redundant Duplicates] (Same Name, Identical Content)")
            for filename, items in data['duplicates'].items():
                print(f"  - File: {Fore.YELLOW}{filename}{Style.RESET_ALL}")
                for item in items:
                    print(f"    - Resource: {item['resource']:<25} Path: {item['path']}")
    summary_header = "\n--- Scan Complete ---"
    conflict_summary = f"Total Critical Conflicts Found: {Fore.RED}{total_conflicts}{Style.RESET_ALL}"
    duplicate_summary = f"Total Redundant Duplicates Found: {Fore.YELLOW}{total_duplicates}{Style.RESET_ALL}"
    print(summary_header)
    print(conflict_summary)
    print(duplicate_summary)
    if output_file:
        if output_format == "html":
            file_content = _generate_html_report(directory, categorized_results, total_conflicts, total_duplicates, files_to_search, ignored_patterns)
        else:
            file_content = _generate_lua_report(directory, categorized_results, total_conflicts, total_duplicates, files_to_search, ignored_patterns)
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(file_content)
            print(Fore.GREEN + f"\nResults also written to '{output_file}' ({output_format.upper()} Report Format).")
        except IOError as e:
            print(Fore.RED + f"Error writing to output file: {e}")

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
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Find map collisions in a directory, checking file content and categorizing by type.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("directory", help="The directory to scan for map collisions (e.g., your 'resources' folder).")
    parser.add_argument("--output", help="Output file to write the list of collisions to.")
    parser.add_argument("--format", choices=['lua', 'html'], default='lua', help="Output file format (lua or html). Default is lua.")
    args = parser.parse_args()
    files_to_search, ignored_patterns = get_files_to_search_interactively()
    if not os.path.isdir(args.directory):
        print(Fore.RED + f"Error: Directory not found at '{args.directory}'")
    else:
        find_collisions(args.directory, files_to_search=files_to_search, ignored_patterns=ignored_patterns, output_file=args.output, output_format=args.format)