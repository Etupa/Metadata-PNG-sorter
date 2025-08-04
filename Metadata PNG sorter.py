#!/usr/bin/env python3
import os
import shutil
import threading
from pathlib import Path
import tkinter as tk
from tkinter import Tk, StringVar, messagebox, filedialog, ttk
from tkinter.scrolledtext import ScrolledText
from PIL import Image
from collections import defaultdict

# ------------------ Core logic ------------------
def extract_text_chunks(png_path):
    try:
        img = Image.open(png_path)
    except Exception as e:
        print(f"[ERROR] Cannot open {png_path}: {e}")
        return {}
    info = {}
    if hasattr(img, "text"):
        info.update(img.text)
    if hasattr(img, "info"):
        for k, v in img.info.items():
            if isinstance(v, str):
                info.setdefault(k, v)
    if "parameters" in info:
        params = info["parameters"]
        info.setdefault("Prompt", parse_prompt_from_parameters(params))
    elif "prompt" in info:
        info.setdefault("Prompt", info["prompt"])
    return info

def parse_prompt_from_parameters(block):
    if not block:
        return ""
    for line in block.splitlines():
        if line.strip().lower().startswith("prompt:"):
            return line.split(":", 1)[1].strip()
    return block.splitlines()[0].strip()

def match_keywords(text, keywords):
    if not text:
        return []
    lower = text.lower()
    return [kw for kw in keywords if kw.lower() in lower]

def sort_images(
    source_dir,
    keywords,
    dest_dir,
    action="copy",                    # "copy" or "move"
    multi_match="duplicate",          # "first", "duplicate", or "skip"
    no_match_folder="no_match",
    log_callback=None,
    done_callback=None               # will be called on main thread after finishing
):
    def log(msg):
        if log_callback:
            log_callback(msg)

    if not os.path.exists(source_dir):
        log(f"[ERROR] Source directory not found: {source_dir}")
        if done_callback:
            done_callback(error=True, message=f"Source directory not found: {source_dir}")
        return

    # Ensure destination root exists
    os.makedirs(dest_dir, exist_ok=True)

    images = [
        os.path.join(source_dir, f)
        for f in os.listdir(source_dir)
        if f.lower().endswith(".png")
    ]
    if not images:
        log("No PNG images found in the selected folder.")
        if done_callback:
            done_callback(error=False, message="No PNG images found.")
        return

    summary = defaultdict(list)

    for path in images:
        try:
            info = extract_text_chunks(path)
            prompt_text = (
                info.get("Prompt")
                or info.get("prompt")
                or info.get("description")
                or ""
            )
            matched = match_keywords(prompt_text, keywords)
        except Exception as e:
            log(f"ERROR extracting/matching for {os.path.basename(path)}: {e}")
            summary[no_match_folder].append(path)
            target_dir = os.path.join(dest_dir, no_match_folder)
            os.makedirs(target_dir, exist_ok=True)
            shutil.copy2(path, target_dir)
            continue

        if not matched:
            summary[no_match_folder].append(path)
            target_dir = os.path.join(dest_dir, no_match_folder)
            os.makedirs(target_dir, exist_ok=True)
            if action == "copy":
                shutil.copy2(path, target_dir)
            else:
                shutil.move(path, target_dir)
            log(f"No match: {os.path.basename(path)}")
        else:
            if multi_match == "first":
                kw = matched[0]
                summary[kw].append(path)
                target_dir = os.path.join(dest_dir, kw)
                os.makedirs(target_dir, exist_ok=True)
                if action == "copy":
                    shutil.copy2(path, target_dir)
                else:
                    shutil.move(path, target_dir)
                log(f"{kw}: {os.path.basename(path)}")

            elif multi_match == "duplicate":
                if action == "move":
                    # copy to all but last, then move original to last
                    for kw in matched[:-1]:
                        summary[kw].append(path)
                        target_dir = os.path.join(dest_dir, kw)
                        os.makedirs(target_dir, exist_ok=True)
                        shutil.copy2(path, target_dir)
                    last_kw = matched[-1]
                    summary[last_kw].append(path)
                    target_dir = os.path.join(dest_dir, last_kw)
                    os.makedirs(target_dir, exist_ok=True)
                    shutil.move(path, target_dir)
                else:  # copy
                    for kw in matched:
                        summary[kw].append(path)
                        target_dir = os.path.join(dest_dir, kw)
                        os.makedirs(target_dir, exist_ok=True)
                        shutil.copy2(path, target_dir)
                log(f"{','.join(matched)}: {os.path.basename(path)}")

            elif multi_match == "skip":
                if len(matched) == 1:
                    kw = matched[0]
                    summary[kw].append(path)
                    target_dir = os.path.join(dest_dir, kw)
                    os.makedirs(target_dir, exist_ok=True)
                    if action == "copy":
                        shutil.copy2(path, target_dir)
                    else:
                        shutil.move(path, target_dir)
                    log(f"{kw}: {os.path.basename(path)}")
                else:
                    summary[no_match_folder].append(path)
                    target_dir = os.path.join(dest_dir, no_match_folder)
                    os.makedirs(target_dir, exist_ok=True)
                    if action == "copy":
                        shutil.copy2(path, target_dir)
                    else:
                        shutil.move(path, target_dir)
                    log(f"Multi-match skipped: {os.path.basename(path)}")

    log("\nSummary:")
    for k, lst in summary.items():
        log(f"  {k}: {len(lst)} file(s)")

    if done_callback:
        done_callback(error=False, message="Sorting complete.")

# ------------------- GUI -------------------
def start_sort():
    src = source_var.get().strip()
    dst = dest_var.get().strip()
    kw = [k.strip() for k in keywords_var.get().split(",") if k.strip()]
    act = action_var.get()
    multi = multi_var.get()

    if not src or not dst or not kw:
        messagebox.showerror("Error", "Please set source, destination, and keywords.")
        return

    if not Path(src).is_dir():
        messagebox.showerror("Error", f"Source folder does not exist:\n{src}")
        return
    Path(dst).mkdir(parents=True, exist_ok=True)  # create if missing

    log_box.config(state="normal")
    log_box.delete(1.0, tk.END)
    log_box.config(state="disabled")

    def log_callback(msg):
        log_box.config(state="normal")
        log_box.insert(tk.END, msg + "\n")
        log_box.see(tk.END)
        log_box.config(state="disabled")

    def done_callback(error, message):
        # must run on main thread; schedule via after
        def finalize():
            if error:
                messagebox.showerror("Error", message)
            else:
                messagebox.showinfo("Done", message)
        root.after(0, finalize)

    threading.Thread(
        target=sort_images,
        args=(src, kw, dst, act, multi, "no_match"),
        kwargs={"log_callback": log_callback, "done_callback": done_callback},
        daemon=True,
    ).start()

def choose_source():
    path = filedialog.askdirectory(title="Select Source Folder")
    if path:
        source_var.set(path)

def choose_dest():
    path = filedialog.askdirectory(title="Select Destination Folder")
    if path:
        dest_var.set(path)

# ------------------- GUI setup -------------------
root = Tk()
root.title("Metadata PNG sorter")
root.geometry("600x500")
root.minsize(500, 400)

# Variables
source_var = StringVar()
dest_var = StringVar()
keywords_var = StringVar()
action_var = StringVar(value="copy")
multi_var = StringVar(value="duplicate")

# Container
container = ttk.Frame(root, padding=8)
container.pack(fill="both", expand=True)

# Row 0: Source
ttk.Label(container, text="Source Folder:").grid(row=0, column=0, sticky="w")
src_row = ttk.Frame(container)
src_row.grid(row=1, column=0, sticky="ew", pady=(0, 6))
src_row.columnconfigure(0, weight=1)
ttk.Entry(src_row, textvariable=source_var).grid(row=0, column=0, sticky="ew")
ttk.Button(src_row, text="Browse", command=choose_source).grid(row=0, column=1, padx=4)

# Row 1: Destination
ttk.Label(container, text="Destination Folder:").grid(row=2, column=0, sticky="w")
dst_row = ttk.Frame(container)
dst_row.grid(row=3, column=0, sticky="ew", pady=(0, 6))
dst_row.columnconfigure(0, weight=1)
ttk.Entry(dst_row, textvariable=dest_var).grid(row=0, column=0, sticky="ew")
ttk.Button(dst_row, text="Browse", command=choose_dest).grid(row=0, column=1, padx=4)

# Row 2: Keywords
ttk.Label(container, text="Keywords (comma separated):").grid(row=4, column=0, sticky="w")
ttk.Entry(container, textvariable=keywords_var).grid(row=5, column=0, sticky="ew", pady=(0,6))

# Row 3: Action
ttk.Label(container, text="Action:").grid(row=6, column=0, sticky="w")
ttk.OptionMenu(container, action_var, action_var.get(), "copy", "move").grid(row=7, column=0, sticky="w", pady=(0,6))

# Row 4: Multiple matches
ttk.Label(container, text="If multiple matches:").grid(row=8, column=0, sticky="w")
ttk.OptionMenu(container, multi_var, multi_var.get(), "duplicate", "first", "skip").grid(row=9, column=0, sticky="w", pady=(0,6))

# Start button
ttk.Button(container, text="Start Sorting", command=start_sort).grid(row=10, column=0, pady=10, sticky="ew")

# Log box
log_box = ScrolledText(container, width=70, height=15, state="disabled")
log_box.grid(row=11, column=0, sticky="nsew", pady=(0,4))

# Make log expand
container.rowconfigure(11, weight=1)
container.columnconfigure(0, weight=1)

root.mainloop()
