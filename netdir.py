import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import subprocess
import string
import threading
import re

def get_available_drives():
    used = []
    try:
        result = subprocess.run("wmic logicaldisk get name", shell=True, capture_output=True, text=True)
        for line in result.stdout.splitlines():
            line = line.strip()
            if line and line.endswith(":"):
                used.append(line[0].upper())
    except Exception as e:
        print("获取已用驱动器失败:", e)
    all_drives = list(string.ascii_uppercase)
    return [d for d in all_drives if d not in used]

def check_network_path(path):
    match = re.match(r'\\\\([^\\]+)\\.*', path)
    if not match:
        return False, "网络路径格式错误"
    host = match.group(1)
    try:
        result = subprocess.run(f"ping -n 1 {host}", shell=True, capture_output=True, text=True)
        if "无法访问" in result.stdout or "请求超时" in result.stdout or result.returncode != 0:
            return False, f"{host} 不可达"
        return True, ""
    except Exception as e:
        return False, str(e)

def refresh_drive_list():
    available_drives = get_available_drives()
    drive_combobox['values'] = available_drives
    if available_drives:
        drive_combobox.current(0)
    else:
        drive_var.set('')

def map_network_drive(event=None):
    drive = drive_var.get().strip()
    ip3 = ip3_var.get().strip()
    ip4 = ip4_var.get().strip()
    folder = folder_var.get().strip()
    username = user_var.get().strip()
    password = pass_var.get().strip()

    if folder == folder_placeholder:
        folder = ""
    if username == user_placeholder:
        username = ""
    if password == pass_placeholder:
        password = ""
    if ip3 == ip3_placeholder:
        ip3 = ""
    if ip4 == ip4_placeholder:
        ip4 = ""

    if not drive or not ip3 or not ip4 or not folder:
        messagebox.showerror("错误", "驱动器、IP 地址和共享文件夹不能为空")
        return

    if not username and not password:
        if not messagebox.askyesno("匿名访问", "未填写用户名和密码，将以匿名身份访问，是否继续？"):
            return

    path = f"\\\\192.168.{ip3}.{ip4}\\{folder}"

    reachable, msg = check_network_path(path)
    if not reachable:
        messagebox.showerror("网络不可达", msg)
        return

    def run_mapping():
        cmd = f'net use {drive}: "{path}"'
        if username and password:
            cmd += f' /user:{username} {password}'
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                messagebox.showinfo("成功", f"{drive}: 映射成功！")
                refresh_drive_list()
                subprocess.run('explorer.exe shell:MyComputerFolder', shell=True)
            else:
                messagebox.showerror("失败", result.stderr.strip() or result.stdout.strip())
        except subprocess.TimeoutExpired:
            messagebox.showerror("超时", "映射超时，请检查网络路径是否可达")
        except Exception as e:
            messagebox.showerror("异常", str(e))

    threading.Thread(target=run_mapping, daemon=True).start()

# ---------------- GUI ----------------
root = tk.Tk()
root.title("安杜兰内网NAS快速映射工具")
# 获取屏幕宽高
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# 窗口大小
window_width = 520
window_height = 280

# 计算窗口左上角坐标，使窗口居中
x = (screen_width - window_width) // 2
y = (screen_height - window_height) // 2

root.geometry(f"{window_width}x{window_height}+{x}+{y}")

root.grid_columnconfigure(1, weight=1)

tk.Label(root, text="驱动器盘符:").grid(row=0, column=0, padx=10, pady=10, sticky='e')
tk.Label(root, text="NAS 地址:").grid(row=1, column=0, padx=10, pady=10, sticky='e')
tk.Label(root, text="用户名:").grid(row=2, column=0, padx=10, pady=10, sticky='e')
tk.Label(root, text="密码:").grid(row=3, column=0, padx=10, pady=10, sticky='e')

drive_var = tk.StringVar()
available_drives = get_available_drives()
drive_combobox = ttk.Combobox(root, textvariable=drive_var, values=available_drives, state="readonly", width=8)
drive_combobox.grid(row=0, column=1, padx=10, pady=10, sticky='w')
if available_drives:
    drive_combobox.current(0)

ip3_var = tk.StringVar()
ip4_var = tk.StringVar()
folder_var = tk.StringVar()
folder_placeholder = "请输入共享文件夹名称"
ip3_placeholder = "IP3"
ip4_placeholder = "IP4"

frame_ip = tk.Frame(root)
frame_ip.grid(row=1, column=1, padx=10, pady=10, sticky='w')

tk.Label(frame_ip, text="192.168.").grid(row=0, column=0, sticky='w')
ip3_entry = tk.Entry(frame_ip, textvariable=ip3_var, width=4)
ip3_entry.grid(row=0, column=1, sticky='w', padx=(0,2))
tk.Label(frame_ip, text=".").grid(row=0, column=2, sticky='w', padx=(0,2))
ip4_entry = tk.Entry(frame_ip, textvariable=ip4_var, width=4)
ip4_entry.grid(row=0, column=3, sticky='w', padx=(0,6))
tk.Label(frame_ip, text="\\").grid(row=0, column=4, sticky='w', padx=(0,6))
folder_entry = tk.Entry(frame_ip, textvariable=folder_var, width=22)
folder_entry.grid(row=0, column=5, sticky='w')

def add_placeholder(entry, var, placeholder, is_password=False):
    var.set(placeholder)
    entry.config(fg="gray")
    if is_password:
        entry.config(show="")

    def on_focus_in(event):
        if var.get() == placeholder:
            entry.delete(0, tk.END)
            entry.config(fg="black")
            if is_password:
                entry.config(show="*")
            entry.icursor(0)

    def on_focus_out(event):
        if not var.get():
            var.set(placeholder)
            entry.config(fg="gray")
            if is_password:
                entry.config(show="")

    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)

add_placeholder(folder_entry, folder_var, folder_placeholder)
add_placeholder(ip3_entry, ip3_var, ip3_placeholder)
add_placeholder(ip4_entry, ip4_var, ip4_placeholder)

user_var = tk.StringVar()
user_placeholder = "请输入分配给您的用户名"
user_entry = tk.Entry(root, textvariable=user_var, width=28)
user_entry.grid(row=2, column=1, padx=10, pady=10, sticky='w')
add_placeholder(user_entry, user_var, user_placeholder)

pass_var = tk.StringVar()
pass_placeholder = "请输入密码"
pass_entry = tk.Entry(root, textvariable=pass_var, width=28)
pass_entry.grid(row=3, column=1, padx=10, pady=10, sticky='w')
add_placeholder(pass_entry, pass_var, pass_placeholder, is_password=True)

tk.Button(root, text="开始映射", command=map_network_drive, bg="lightblue", width=12)\
  .grid(row=4, column=1, padx=10, pady=20, sticky='w')

for widget in (drive_combobox, ip3_entry, ip4_entry, folder_entry, user_entry, pass_entry, root):
    widget.bind("<Return>", map_network_drive)

root.mainloop()
