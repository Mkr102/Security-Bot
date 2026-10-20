import telebot
import subprocess
import ctypes
import json
import socket
import time
import sys
import os
import shutil
import traceback
import urllib.request
import tkinter as tk
from tkinter import messagebox, ttk

def get_dynamic_install_info():
     brand = "Security"
     try:
         import wmi
         c = wmi.WMI()
         for bios in c.Win32_ComputerSystem():
             manufacturer = bios.Manufacturer.strip()
             clean_brand = "".join(c for c in manufacturer if c.isalnum())
             if clean_brand:
                brand = clean_brand
                break
     except Exception:
         pass

     install_dir = os.path.join(r"C:", brand)
     app_name = f"{brand}Service"
     return install_dir, app_name

INITIAL_DIR, DEFAULT_APP = get_dynamic_install_info()
INSTALL_DIR = INITIAL_DIR
CONFIG_FILE = os.path.join(INSTALL_DIR, "service_config.json")
LOG_FILE = os.path.join(INSTALL_DIR, "error_log.txt")

def log_error(err_msg):
     try:
         os.makedirs(INSTALL_DIR, exist_ok=True)
         with open(LOG_FILE, "a", encoding="utf-8") as f:
              timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
              f.write(f"[{timestamp}] ERROR:\n{err_msg}\n{'-'*50}\n")
     except Exception:
         pass


def run_ps(cmd):
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = subprocess.SW_HIDE
    args = ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", cmd]
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        startupinfo=si,
        creationflags=subprocess.CREATE_NO_WINDOW)

def get_auto_service_name():

    try:

        import wmi

        c = wmi.WMI()

        for bios in c.Win32_ComputerSystem():

            manufacturer = bios.Manufacturer.strip()

            clean_brand = "".join(c for c in manufacturer if c.isalnum())

            if clean_brand:

                return f"{clean_brand}Service"

    except Exception:

        pass

    return "SecurityService"


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def perform_uninstall():
    app_name = "DellService"
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                app_name = json.load(f).get("app_name", "DellService")
        except Exception:
            pass

    run_ps(f"Unregister-ScheduledTask -TaskName '{app_name}' -Confirm:$false -ErrorAction SilentlyContinue")
    run_ps("Unregister-ScheduledTask -TaskName 'DellSystemService' -Confirm:$false -ErrorAction SilentlyContinue")
    run_ps("Remove-NetFirewallRule -DisplayName 'PhoneVerifyLock' -ErrorAction SilentlyContinue")

    cleanup_cmd = (
        f"Stop-Process -Name '{app_name}' -Force -ErrorAction SilentlyContinue; "
        f"Start-Sleep -Seconds 2; "
        f"Remove-Item -Path '{INSTALL_DIR}' -Recurse -Force -ErrorAction SilentlyContinue"
    )
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = subprocess.SW_HIDE
    subprocess.Popen(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", cleanup_cmd],
        startupinfo=si,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    sys.exit()

# Professional Modern GUI Window
def show_professional_wizard(is_installed=False, default_name="DellService", default_id="", default_token=""):
    result = {"action": None}

    root = tk.Tk()
    root.title("Dell Security Service Suite" if is_installed else "Dell Security Service Setup")
    root.geometry("480x350")
    root.resizable(False, False)
    root.attributes("-topmost", True)

    root.update_idletasks()
    x = (root.winfo_screenwidth() - 480) // 2
    y = (root.winfo_screenheight() - 350) // 2
    root.geometry(f"480x350+{x}+{y}")

    # Styling
    style = ttk.Style()
    style.theme_use("clam")

    header_frame = tk.Frame(root, bg="#0078D7", height=60)
    header_frame.pack(fill=tk.X)
    
    title_text = "Manage Security Service" if is_installed else "Install Security Service"
    tk.Label(header_frame, text=title_text, bg="#0078D7", fg="white", font=("Segoe UI", 13, "bold")).pack(pady=15)

    body_frame = tk.Frame(root, padx=25, pady=20)
    body_frame.pack(fill=tk.BOTH, expand=True)

    tk.Label(body_frame, text="Service Name:", font=("Segoe UI", 9, "bold")).anchor(tk.W)
    tk.Label(body_frame, text="Service Name:", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", pady=8)
    entry_name = ttk.Entry(body_frame, width=32, font=("Segoe UI", 10))
    entry_name.insert(0, default_name)
    entry_name.grid(row=0, column=1, pady=8)

    tk.Label(body_frame, text="User No. :", font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky="w", pady=8)
    entry_id = ttk.Entry(body_frame, width=32, font=("Segoe UI", 10))
    entry_id.insert(0, str(default_id))
    entry_id.grid(row=1, column=1, pady=8)

    tk.Label(body_frame, text="User ID :", font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky="w", pady=8)
    entry_token = ttk.Entry(body_frame, width=32, font=("Segoe UI", 10))
    entry_token.insert(0, default_token)
    entry_token.grid(row=2, column=1, pady=8)

    btn_frame = tk.Frame(root, bg="#F0F0F0", height=60, padx=20)
    btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

    def validate_and_get():
        raw_name = entry_name.get().strip()
        raw_id = entry_id.get().strip()
        raw_token = entry_token.get().strip()

        clean_name = "".join(c for c in raw_name if c.isalnum() or c in ("_", "-"))
        if not clean_name:
            clean_name = "DellService"

        if not raw_id.lstrip("-").isdigit():
            messagebox.showerror("Error", "TG ID sirf numbers mein honi chahiye!", parent=root)
            return None

        if ":" not in raw_token or len(raw_token) < 20:
            messagebox.showerror("Error", "Sahiya Telegram Bot Token darj karein!", parent=root)
            return None

        return {"app_name": clean_name, "tg_id": int(raw_id), "tg_token": raw_token}

    def on_install():
        data = validate_and_get()
        if data:
            result["action"] = "save"
            result.update(data)
            root.destroy()

    def on_repair():
        data = validate_and_get()
        if data:
            result["action"] = "repair"
            result.update(data)
            root.destroy()

    def on_uninstall():
        if messagebox.askyesno("Confirm Uninstall", "Kya aap sach mein is software ko poori tarah uninstall karna chahte hain?", parent=root):
            root.destroy()
            perform_uninstall()

    def on_cancel():
        root.destroy()
        sys.exit()

    # Dynamic Buttons based on installation state
    if is_installed:
        tk.Button(btn_frame, text="Update Config", command=on_install, bg="#0078D7", fg="white", font=("Segoe UI", 9, "bold"), width=11, relief=tk.FLAT).pack(side=tk.LEFT, pady=12, padx=2)
        tk.Button(btn_frame, text="Repair Service", command=on_repair, bg="#5BC0DE", fg="white", font=("Segoe UI", 9, "bold"), width=11, relief=tk.FLAT).pack(side=tk.LEFT, pady=12, padx=2)
        tk.Button(btn_frame, text="Uninstall", command=on_uninstall, bg="#D9534F", fg="white", font=("Segoe UI", 9, "bold"), width=9, relief=tk.FLAT).pack(side=tk.LEFT, pady=12, padx=2)
        tk.Button(btn_frame, text="Exit", command=on_cancel, font=("Segoe UI", 9), width=8, relief=tk.FLAT).pack(side=tk.RIGHT, pady=12, padx=2)
    else:
        tk.Button(btn_frame, text="Install Now", command=on_install, bg="#5CB85C", fg="white", font=("Segoe UI", 10, "bold"), width=15, relief=tk.FLAT).pack(side=tk.LEFT, pady=12, padx=10)
        tk.Button(btn_frame, text="Cancel", command=on_cancel, font=("Segoe UI", 9), width=12, relief=tk.FLAT).pack(side=tk.RIGHT, pady=12, padx=10)

    root.protocol("WM_DELETE_WINDOW", on_cancel)
    root.mainloop()

    if not result["action"]:
        sys.exit()
    return result

def load_or_setup_environment():
    os.makedirs(INSTALL_DIR, exist_ok=True)
    existing_cfg = {}
    is_installed = False

    if os.path.exists(CONFIG_FILE):
        is_installed = True
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                existing_cfg = json.load(f)
        except Exception as e:
            log_error(f"Config read error: {e}")

    if getattr(sys, 'frozen', False):
        current_exe = os.path.abspath(sys.executable)
        is_external = os.path.dirname(current_exe).lower() != INSTALL_DIR.lower()
    else:
        current_exe = os.path.abspath(__file__)
        is_external = False

# Agar bahar se run kiya hai ya config nahi hai, toh Wizard khulega
    if not is_installed or is_external:
        auto_name = get_auto_service_name()
        
        cfg = show_professional_wizard(
            is_installed=is_installed,
            default_name=existing_cfg.get("app_name", auto_name),
            default_id=existing_cfg.get("tg_id", ""),
            default_token=existing_cfg.get("tg_token", "")
        )
        
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4)
            
        app_name = cfg["app_name"]
        
        if getattr(sys, 'frozen', False):
            target_exe = os.path.join(INSTALL_DIR, f"{app_name}.exe")
            if current_exe.lower() != os.path.abspath(target_exe).lower():
                try:
                    run_ps(f"Stop-Process -Name '{app_name}' -Force -ErrorAction SilentlyContinue")
                    time.sleep(1)
                    shutil.copy2(current_exe, target_exe)
                except Exception as e:
                    log_error(f"Copy exe error: {e}")
                    target_exe = current_exe
            run_cmd = f'"{target_exe}"'
        else:
            pythonw_path = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
            if not os.path.exists(pythonw_path):
                pythonw_path = sys.executable
            run_cmd = f'"{pythonw_path}" "{current_exe}"'

        create_task_ps = (
            f"$action = New-ScheduledTaskAction -Execute {run_cmd}; "
            f"$trigger = New-ScheduledTaskTrigger -AtLogOn; "
            f"$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable; "
            f"Register-ScheduledTask -TaskName '{app_name}' -Action $action -Trigger $trigger -Settings $settings -RunLevel Highest -Force"
        )
        run_ps(create_task_ps)

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        messagebox.showinfo("Success", f"'{app_name}' successfully configured and deployed!", parent=root)
        root.destroy()
        
        if is_external and getattr(sys, 'frozen', False):
            os.startfile(target_exe)
            sys.exit()
            
        return cfg
    else:
        return existing_cfg

def set_sharing_lock(lock=True):
    ensure_rule = (
        "if (-not (Get-NetFirewallRule -DisplayName 'PhoneVerifyLock' -ErrorAction SilentlyContinue)) { "
        "New-NetFirewallRule -DisplayName 'PhoneVerifyLock' -Direction Inbound -Action Block -Protocol TCP -LocalPort 445,139 -Profile Any "
        "}"
    )
    run_ps(ensure_rule)
    if lock:
        run_ps("Enable-NetFirewallRule -DisplayName 'PhoneVerifyLock'")
        run_ps("Get-SmbSession | Remove-SmbSession -Force -ErrorAction SilentlyContinue")
    else:
        run_ps("Disable-NetFirewallRule -DisplayName 'PhoneVerifyLock'")

def get_host_details():
    try:
        host_name = socket.gethostname()
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        host_ip = s.getsockname()[0]
        s.close()
        return f"🖥️ *Host PC Name:* `{host_name}`\n🌐 *Host PC IP:* `{host_ip}`\n"
    except Exception:
        return "🖥️ *Host PC Details:* Error retrieving info\n"

def get_open_apps():
    try:
        cmd = "Get-Process | Where-Object {$_.MainWindowTitle} | Select-Object ProcessName | ConvertTo-Json"
        result = run_ps(cmd)
        if not result.stdout.strip():
            return "🟢 No main user applications are currently running."
        data = json.loads(result.stdout)
        if isinstance(data, dict):
            data = [data]
        app_list = "💻 *Currently Open Applications:*\n"
        for index, app in enumerate(data, 1):
            app_list += f"{index}. `{app.get('ProcessName', 'Unknown')}`\n"
        return app_list
    except Exception as e:
        log_error(f"get_open_apps error: {e}")
        return "❌ Error scanning active applications."

def get_advanced_network_report():
    try:
        cmd_sessions = "Get-SmbSession | Select-Object ClientComputerName, UserName | ConvertTo-Json"
        res_sessions = run_ps(cmd_sessions)
        cmd_files = "Get-SmbOpenFile | Select-Object ClientComputerName, Path, ShareName | ConvertTo-Json"
        res_files = run_ps(cmd_files)
        report = "⚠️ *Connected Network Devices & Active Data Access:*\n\n"
        if not res_sessions.stdout.strip():
            return report + "🟢 No external devices are currently connected to your drives/printer."
        sessions_data = json.loads(res_sessions.stdout)
        if isinstance(sessions_data, dict):
            sessions_data = [sessions_data]
        report += "👥 *Active Connected Devices:*\n"
        for index, session in enumerate(sessions_data, 1):
            client = session.get("ClientComputerName", "Unknown")
            user = session.get("UserName", "Unknown")
            report += f"{index}. Device Name/IP: `{client}` (Logged in as: `{user}`)\n"
        report += "\n📂 *Live Data / Files Being Accessed Right Now:*\n"
        if res_files.stdout.strip():
            files_data = json.loads(res_files.stdout)
            if isinstance(files_data, dict):
                files_data = [files_data]
            for index, file_info in enumerate(files_data, 1):
                device = file_info.get("ClientComputerName", "Unknown")
                file_path = file_info.get("Path", "Unknown")
                share_name = file_info.get("ShareName", "Unknown")
                report += f"{index}. From Device `{device}` looking inside share `[{share_name}]` -> File: `{file_path}`\n"
        else:
            report += "🟢 Connected, but not reading/opening any files at this exact split second.\n"
        return report
    except Exception as e:
        log_error(f"get_advanced_network_report error: {e}")
        return "❌ Error retrieving active network data tracking."

def main():
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

    config = load_or_setup_environment()
    API_TOKEN = config["tg_token"]
    ALLOWED_CHAT_ID = int(config["tg_id"])

    bot = telebot.TeleBot(API_TOKEN)

    @bot.message_handler(commands=['lock'])
    def lock_command(message):
        if int(message.chat.id) == ALLOWED_CHAT_ID:
            set_sharing_lock(True)
            bot.reply_to(message, "🔒 *LOCKED!* Drives & Printer sharing blocked.", parse_mode="Markdown")

    @bot.message_handler(commands=['unlock'])
    def unlock_command(message):
        if int(message.chat.id) == ALLOWED_CHAT_ID:
            set_sharing_lock(False)
            bot.reply_to(message, "🔓 *UNLOCKED!* Drives & Printer sharing allowed.", parse_mode="Markdown")

    @bot.message_handler(commands=['uninstall'])
    def remote_uninstall_command(message):
        if int(message.chat.id) == ALLOWED_CHAT_ID:
            bot.reply_to(message, "🗑️ *Remote Uninstalling...* Software is being removed.", parse_mode="Markdown")
            perform_uninstall()

    # REMOTE OVER-THE-AIR UPDATE FEATURE (`/update [direct_link]`)
    @bot.message_handler(commands=['update'])
    def remote_update_command(message):
        if message.chat.id == ALLOWED_CHAT_ID:
            args = message.text.split()
            if len(args) < 2:
                bot.reply_to(message, "⚠️ Usage: `/update <Direct_Download_Link_to_New_Exe>`", parse_mode="Markdown")
                return
            
            download_url = args[1]
            bot.reply_to(message, "🔄 *Downloading update...* Please wait.", parse_mode="Markdown")
            
            try:
                temp_update_path = os.path.join(INSTALL_DIR, "update_temp.exe")
                urllib.request.urlretrieve(download_url, temp_update_path)
                
                current_exe = sys.executable if getattr(sys, 'frozen', False) else __file__
                
                # PowerShell batch script jo old exe ko replace karke restart karega
                update_script = (
                    f"Start-Sleep -Seconds 3; "
                    f"Copy-Item -Path '{temp_update_path}' -Destination '{current_exe}' -Force; "
                    f"Start-Process '{current_exe}';"
                )
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                si.wShowWindow = subprocess.SW_HIDE
                subprocess.Popen(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", update_script], startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
                
                bot.reply_to(message, "✅ *Update downloaded successfully!* Restarting service...", parse_mode="Markdown")
                sys.exit()
            except Exception as e:
                log_error(f"Remote update failed: {e}")
                bot.reply_to(message, f"❌ Update failed: {e}", parse_mode="Markdown")

    @bot.message_handler(commands=['status'])
    def check_status(message):
        if int(message.chat.id) == ALLOWED_CHAT_ID:
            try:
                cmd = "(Get-NetFirewallRule -DisplayName 'PhoneVerifyLock' -ErrorAction SilentlyContinue).Enabled"
                result = run_ps(cmd)
                fw_state = result.stdout.strip()
                sharing_state = "🔒 LOCKED" if fw_state == "True" else ("🔓 UNLOCKED" if fw_state == "False" else "⚠️ Not Found")
                fw_status = f"🛡️ *Sharing Status:* `{sharing_state}`\n\n"
                full_report = "📊 *System Status Report*\n\n" + get_host_details() + "\n" + fw_status + get_open_apps() + "\n" + get_advanced_network_report()
                bot.reply_to(message, full_report, parse_mode="Markdown")
            except Exception as e:
                bot.reply_to(message, f"❌ Error: {e}")

    set_sharing_lock(True)

    for _ in range(12):
        try:
            bot.send_message(ALLOWED_CHAT_ID, f"🚨 *{config.get('app_name', 'DellService')} Online!* PC started securely.", parse_mode="Markdown")
            break
        except Exception:
            time.sleep(5)

    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            log_error(f"Polling crashed: {e}")
            time.sleep(10)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        log_error(traceback.format_exc())
