import os
import json
import shutil
import datetime
import sqlparse
import tkinter as tk
from tkinter import messagebox, scrolledtext
from pathlib import Path

# Configuration
SQL_ROOT = "SQL"
CONF_DIR = "SQL_confirmed"
REJ_DIR = "SQL_rejected"
LOG_FILE = "sql_validation_log.csv"

# Ensure root-level folders exist
os.makedirs(CONF_DIR, exist_ok=True)
os.makedirs(REJ_DIR, exist_ok=True)

# Prepare logging file header
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", encoding="utf-8") as logf:
        logf.write("timestamp,category,filename,status,reason\n")

# Gather test case files
def collect_testcases():
    collected = []
    for category in os.listdir(SQL_ROOT):
        cat_path = os.path.join(SQL_ROOT, category)
        if os.path.isdir(cat_path):
            for fname in os.listdir(cat_path):
                if fname.lower().endswith('.json'):
                    fpath = os.path.join(cat_path, fname)
                    collected.append((category, fpath))
    return collected

testcases = collect_testcases()
index = 0
current_category = None
current_path = None
current_tc = None

# Move file and log
def move_file(category, filepath, status, reason=""):
    root_dir = CONF_DIR if status == 'confirmed' else REJ_DIR
    target_dir = os.path.join(root_dir, category)
    os.makedirs(target_dir, exist_ok=True)
    fname = os.path.basename(filepath)
    dest = os.path.join(target_dir, fname)
    shutil.move(filepath, dest)
    ts = datetime.datetime.now().isoformat()
    with open(LOG_FILE, "a", encoding="utf-8") as logf:
        logf.write(f"{ts},{category},{fname},{status},{reason}\n")

# Custom dialog for larger text input
def prompt_text(title, prompt, initial_text="", width=600, height=600):
    dialog = tk.Toplevel()
    dialog.title(title)
    dialog.geometry(f"{width}x{height}")
    dialog.transient(root)
    dialog.grab_set()

    lbl = tk.Label(dialog, text=prompt)
    lbl.pack(anchor='nw', padx=10, pady=(10,5))

    text_area = scrolledtext.ScrolledText(dialog, wrap=tk.WORD)
    text_area.pack(fill=tk.BOTH, expand=True, padx=10)
    text_area.insert(tk.END, initial_text)

    btn_frame = tk.Frame(dialog)
    btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

    result = {'value': None}

    def on_ok():
        result['value'] = text_area.get(1.0, tk.END).strip()
        dialog.destroy()

    def on_cancel():
        dialog.destroy()

    ok_btn = tk.Button(btn_frame, text="OK", width=12, command=on_ok)
    ok_btn.pack(side=tk.LEFT, padx=5)
    cancel_btn = tk.Button(btn_frame, text="Cancel", width=12, command=on_cancel)
    cancel_btn.pack(side=tk.LEFT, padx=5)

    dialog.update_idletasks()
    dialog.wait_visibility()
    dialog.wait_window()
    return result['value']

# GUI setup
root = tk.Tk()
root.title("SQL Test Case Validator")
root.geometry("1000x700")

counter_var = tk.StringVar()

counter_frame = tk.Frame(root)
counter_frame.pack(fill=tk.X)
tk.Label(counter_frame, textvariable=counter_var, anchor='w', padx=10).pack(side=tk.LEFT)

top_frame = tk.Frame(root)
top_frame.pack(fill=tk.BOTH, expand=True)
btm_frame = tk.Frame(root)
btm_frame.pack(fill=tk.X)

# Input section
tk.Label(top_frame, text="Input:").pack(anchor='nw', padx=10, pady=(10,0))
input_text = scrolledtext.ScrolledText(top_frame, wrap=tk.WORD, height=5)
input_text.pack(fill=tk.X, padx=10, pady=(0,10))

# Output section
tk.Label(top_frame, text="Output:").pack(anchor='nw', padx=10, pady=(0,0))
output_text = scrolledtext.ScrolledText(top_frame, wrap=tk.WORD, height=10)
output_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))

# Handlers
def update_counter():
    counter_var.set(f"Test cases remaining: {len(testcases) - index}")

def load_current():
    global index, current_category, current_path, current_tc
    if index >= len(testcases):
        messagebox.showinfo("Done", "All test cases processed.")
        root.quit()
        return
    current_category, current_path = testcases[index]
    with open(current_path, 'r', encoding='utf-8') as f:
        current_tc = json.load(f)

    input_text.config(state='normal')
    input_text.delete(1.0, tk.END)
    input_text.insert(tk.END, current_tc.get('input', ''))
    input_text.config(state='disabled')

    output = current_tc.get('output', {})
    raw_sql = output.get('sql', '')
    formatted_sql = sqlparse.format(raw_sql, reindent=True, keyword_case='upper')
    output_text.config(state='normal')
    output_text.delete(1.0, tk.END)
    output_text.insert(tk.END, formatted_sql)
    output_text.config(state='disabled')

    update_counter()

def confirm():
    global index
    move_file(current_category, current_path, 'confirmed')
    index += 1
    load_current()

def reject():
    reason = prompt_text("Rejection Reason", "Enter reason for rejection:")
    if not reason:
        return
    move_file(current_category, current_path, 'rejected', reason)
    global index
    index += 1
    load_current()

def change_input():
    new_input = prompt_text("Edit Input", "Modify test case input:", initial_text=current_tc.get('input', ''))
    if new_input is None:
        return
    current_tc['input'] = new_input
    with open(current_path, 'w', encoding='utf-8') as f:
        json.dump(current_tc, f, indent=2)
    move_file(current_category, current_path, 'confirmed')
    global index
    index += 1
    load_current()

# Buttons
btn_confirm = tk.Button(btm_frame, text="Confirm", command=confirm, bg='lightgreen')
btn_confirm.pack(side=tk.LEFT, padx=5, pady=5)
btn_reject = tk.Button(btm_frame, text="Reject", command=reject, bg='salmon')
btn_reject.pack(side=tk.LEFT, padx=5, pady=5)
btn_edit = tk.Button(btm_frame, text="Change Input", command=change_input, bg='lightblue')
btn_edit.pack(side=tk.LEFT, padx=5, pady=5)

# Start
load_current()
root.mainloop()
