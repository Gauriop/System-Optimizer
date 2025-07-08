import tkinter as tk
from tkinter import messagebox
import psutil
import random

# Store process names and paths
process_path_map = {}

# ---------- Round Robin Logic ----------
def simulate_round_robin():
    rr_text.delete(1.0, tk.END)
    
    # Get the indices of selected processes from the Listbox
    selected_indices = process_list.curselection()
    
    if len(selected_indices) != 5:
        messagebox.showerror("❌ Error", "Please select exactly 5 processes.")
        return
    
    # Prepare the list of selected processes and assign random burst time
    selected_processes = []
    for index in selected_indices:
        line = process_list.get(index)
        pname = line.split(" ➜")[0].strip()
        bt = random.randint(1, 10)  # Random burst time
        selected_processes.append({"name": pname, "bt": bt})
    
    if not selected_processes:
        rr_text.insert(tk.END, "No processes selected.")
        return

    tq = 4  # Time quantum
    time = 0
    queue = selected_processes.copy()
    ct_map = {}
    remaining_bt = {p['name']: p['bt'] for p in queue}

    while queue:
        p = queue.pop(0)
        pname = p['name']
        exec_time = min(tq, remaining_bt[pname])
        time += exec_time
        remaining_bt[pname] -= exec_time
        if remaining_bt[pname] == 0:
            ct_map[pname] = time
        else:
            queue.append(p)

    rr_text.insert(tk.END, f"{'Process':<25}{'BT':<10}{'CT':<10}{'TAT':<10}{'WT':<10}\n")
    rr_text.insert(tk.END, "-"*65 + "\n")
    for p in selected_processes:
        pname = p['name']
        bt = p['bt']
        ct = ct_map.get(pname, 0)
        tat = ct - 0
        wt = tat - bt
        rr_text.insert(tk.END, f"{pname:<25}{bt:<10}{ct:<10}{tat:<10}{wt:<10}\n")

# ---------- System Stats Update ----------
def update_stats():
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent

    cpu_label.config(text=f"🖥 CPU Usage: {cpu:.1f}%")
    ram_label.config(text=f"🧠 RAM Usage: {ram:.1f}%")
    disk_label.config(text=f"💾 Disk Usage: {disk:.1f}%")

    show_top_ram_process()

    if ram > 80 and not update_stats.alert_shown:
        messagebox.showwarning("🚨 High RAM Usage!", "Top RAM usage exceeded 80%!")
        update_stats.alert_shown = True
    elif ram <= 80:
        update_stats.alert_shown = False

    window.after(1000, update_stats)

update_stats.alert_shown = False

# ---------- Show Top RAM Processes ----------
def get_top_5_ram_processes():
    top_proc = []
    for proc in psutil.process_iter(['name', 'memory_percent']):
        try:
            name = proc.info['name']
            mem = proc.info['memory_percent']
            if name and mem > 0:
                top_proc.append({"name": name, "memory_percent": mem})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return sorted(top_proc, key=lambda x: x['memory_percent'], reverse=True)[:5]

def show_top_ram_process():
    top5 = get_top_5_ram_processes()
    top_ram_text.delete(1.0, tk.END)
    if top5:
        top_ram_text.insert(tk.END, "Top 5 RAM Apps:\n")
        for i, proc in enumerate(top5, start=1):
            top_ram_text.insert(tk.END, f"{i}. {proc['name']} - {proc['memory_percent']:.2f}%\n")
    else:
        top_ram_text.insert(tk.END, "Top 5 RAM Apps:\nNone\n")

# ---------- Show Process List ----------
def show_processes():
    process_list.delete(0, tk.END)
    process_path_map.clear()
    added = set()
    for proc in psutil.process_iter(['name', 'exe']):
        try:
            name = proc.info['name']
            path = proc.info['exe']
            if name and name not in added:
                display_text = f"{name}  ➜  {path if path else '[Path Unknown]'}"
                process_list.insert(tk.END, display_text)
                process_path_map[name] = path
                added.add(name)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

def kill_process():
    """Terminate selected processes with better error handling"""
    try:
        selected_indices = process_list.curselection()

        if not selected_indices:
            messagebox.showwarning("⚠️ Warning", "Please select at least one process to terminate.")
            return

        # Confirm action
        result = messagebox.askyesno("🔥 Confirm Termination", 
                                     f"Are you sure you want to terminate {len(selected_indices)} process(es)?\n\nThis action cannot be undone.")
        if not result:
            return

        successful = 0
        failed = 0
        protected_processes = []

        critical_processes = [
            'System', 'Registry', 'csrss.exe', 'winlogon.exe', 
            'services.exe', 'lsass.exe', 'svchost.exe', 'explorer.exe'
        ]

        for index in selected_indices:
            selected_line = process_list.get(index)
            selected_name = selected_line.split(" ➜")[0].strip()

            if selected_name in critical_processes:
                protected_processes.append(selected_name)
                continue

            try:
                terminated = False
                for proc in psutil.process_iter(['name', 'pid']):
                    if proc.info['name'] == selected_name:
                        proc.terminate()
                        terminated = True
                        successful += 1
                        break

                if not terminated:
                    failed += 1

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired) as e:
                failed += 1
                print(f"Failed to terminate {selected_name}: {e}")
            except Exception as e:
                failed += 1
                print(f"Unexpected error terminating {selected_name}: {e}")

        # Show result
        message = f"Termination Results:\n✅ Successfully terminated: {successful}\n❌ Failed: {failed}"
        if protected_processes:
            message += f"\n🛡️ Protected (not terminated): {', '.join(protected_processes)}"

        messagebox.showinfo("📊 Results", message)

        show_processes()


    except Exception as e:
        messagebox.showerror("❌ Error", f"An error occurred: {str(e)}")



# ---------- GUI ----------
window = tk.Tk()
window.title("System Resource Optimizer")
window.geometry("800x800")
window.configure(bg="black")

font_main = ("Helvetica Neue", 13)
font_title = ("Helvetica Neue", 16, "bold")
fg_text = "#00ffcc"
bg_button = "#222222"

# Title
tk.Label(window, text="System Resource Optimizer", font=font_title, bg="black", fg="#00ffff").pack(pady=10)

# Resource Labels
cpu_label = tk.Label(window, text="CPU Usage: ", font=font_main, bg="black", fg=fg_text)
cpu_label.pack()
ram_label = tk.Label(window, text="RAM Usage: ", font=font_main, bg="black", fg=fg_text)
ram_label.pack()
disk_label = tk.Label(window, text="Disk Usage: ", font=font_main, bg="black", fg=fg_text)
disk_label.pack()

# Top RAM Text Box
top_ram_text = tk.Text(window, height=6, width=70, bg="#111111", fg="#eeeeee", font=("Courier", 10))
top_ram_text.pack(pady=5)

# Process List (with multi-selection)
process_list = tk.Listbox(window, width=90, height=10, font=("Courier", 10), bg="#111111", fg="#eeeeee", selectbackground="#444444", selectmode=tk.MULTIPLE)
process_list.pack(pady=5)

# Buttons
btn_frame = tk.Frame(window, bg="black")
btn_frame.pack(pady=5)
tk.Button(btn_frame, text="🔄 Refresh Process List", command=show_processes, width=25, bg=bg_button, fg="orange").grid(row=0, column=0, padx=10)
tk.Button(btn_frame, text="❌ Kill Selected App", command=kill_process, width=25, bg="#661111", fg="orange").grid(row=0, column=1, padx=10)

# Round Robin Button
tk.Button(window, text="🌀 Simulate RR with BT/CT/TAT/WT", command=simulate_round_robin, bg="#113366", fg="white", width=40).pack(pady=10)

# Round Robin Output Box
rr_text = tk.Text(window, height=15, width=90, bg="#000000", fg="#00FF00", font=("Courier", 10))
rr_text.pack(pady=5)

# ---------- Start ----------
update_stats()
show_processes()
window.mainloop()