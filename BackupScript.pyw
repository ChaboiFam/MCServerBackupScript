import os
import shutil
import time
import pyautogui
import pygetwindow as gw
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import json

# Define initial paths and settings
server_folder = ""
world_folder = ""
backup_folder = ""
minutes_until_backup = 20
backup_start_time = None
backup_started = False


# Function to handle Log Output checkbox state change and log the status
def on_log_output_toggle():
    if log_output_var.get():
        log_message("Log Output Enabled")
    else:
        log_message("Log Output Disabled")
        
# Function to handle checkbox state change and log the status
def on_checkbox_toggle():
    if send_messages_var.get():
        log_message("Server messages On")
    else:
        log_message("Server messages Off")

# Function to create a timestamped backup folder name
def get_timestamped_backup_name(base_name):
    now = datetime.now()
    timestamp = now.strftime("%m-%d-%Y %I-%M%p")  # 12-hour format
    return f"{base_name} {timestamp}"

# Function to send a command to the Minecraft server console
def send_command_to_server(message):
    if send_messages_var.get():  # Check if sending messages is enabled
        windows = gw.getWindowsWithTitle("Minecraft Server")
        if not windows:
            print("Minecraft Server window not found.")
            messagebox.showwarning("Server Not Found", "Minecraft Server window not found.")
            return False

        window = windows[0]
        window.activate()
        time.sleep(1)
        
        # Split the message into parts if it contains the delimiter
        parts = message.split(" | ")
        
        for part in parts:
            # Send each part to the Minecraft server
            pyautogui.typewrite(f"say {part}")
            pyautogui.press('enter')
    
    # Always log the message regardless of whether it was sent
    log_message(message)
    return True


# Function to run the backup process
def auto_backup_process():
    global backup_start_time, backup_started

    if not backup_started:
        return

    print(f"Waiting until next backup at: {backup_start_time + timedelta(minutes=minutes_until_backup)}")
    
    now = datetime.now()
    time_left = (backup_start_time + timedelta(minutes=minutes_until_backup)) - now
    if time_left.total_seconds() > 0:
        time.sleep(time_left.total_seconds())

    # Execute the backup process
    now = datetime.now()
    print(f"Backup process started at: {now}")

    # Send message to server
    if not send_command_to_server(f"Creating World Backup '{os.path.basename(world_folder)}' {datetime.now().strftime('%m-%d-%Y %I-%M%p')}. The server might lag."):
        messagebox.showwarning("Server Not Found", "Minecraft Server window not found. Skipping backup.")
        return  # Exit if the server window was not found

    # Create a backup folder with timestamp
    backup_name = get_timestamped_backup_name(os.path.basename(world_folder))
    backup_path = os.path.join(backup_folder, backup_name)

    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)

    # Run the backup process
    try:
        if not os.path.exists(world_folder):
            print(f"World folder does not exist: {world_folder}")
            return

        if not os.access(world_folder, os.R_OK):
            print(f"World folder is not accessible: {world_folder}")
            return

        print(f"Starting to copy files...")
        for root, dirs, files in os.walk(world_folder):
            for file in files:
                if file == "session.lock":
                    continue
                src_file = os.path.join(root, file)
                rel_path = os.path.relpath(src_file, world_folder)
                dest_file = os.path.join(backup_path, rel_path)
                dest_dir = os.path.dirname(dest_file)
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)
                shutil.copy2(src_file, dest_file)

        # Check if the backup was created successfully
        if os.path.exists(backup_path):
            success_message = f"Backup created successfully at {datetime.now().strftime('%m-%d-%Y %I-%M%p')}"
            send_command_to_server(success_message)
        else:
            raise Exception("Backup path does not exist after copy operation.")

    except Exception as e:
        failure_message = f"Backup failed! {datetime.now().strftime('%m-%d-%Y %I-%M%p')}"
        messagebox.showerror("Backup Failure", failure_message)
        send_command_to_server(failure_message)
        print(f"Backup failed with error: {e}")

    # Update the start time for the next backup
    backup_start_time = datetime.now()

    # Notify about the next backup
    time_left = (backup_start_time + timedelta(minutes=minutes_until_backup)) - datetime.now()
    next_backup_message = f"Next backup in {time_left.seconds // 60} minutes."
    send_command_to_server(next_backup_message)

    # Restart the timer for the next interval
    update_timer()

# Function to update the countdown timer in the GUI
def update_timer():
    global backup_started, backup_start_time, minutes_until_backup

    if not backup_started:
        return

    now = datetime.now()
    time_left = backup_start_time + timedelta(minutes=minutes_until_backup) - now

    if time_left.total_seconds() <= 0:
        timer_label.config(text="Next Backup in: 00h 00m 00s")
        # Trigger the backup process when the timer expires
        threading.Thread(target=auto_backup_process, daemon=True).start()
    else:
        total_seconds = int(time_left.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours > 0:
            timer_label.config(text=f"Next Backup in: {hours}h {minutes:02}m {seconds:02}s")
        elif minutes > 0:
            timer_label.config(text=f"Next Backup in: {minutes:02}m {seconds:02}s")
        else:
            timer_label.config(text=f"Next Backup in: {seconds:02}s")

        root.after(1000, update_timer)  # Update every second


# Function to start the backup process in a separate thread
def start_auto_backup():
    global backup_start_time, backup_started

    # Check if paths are set
    if not server_folder or not world_folder or not backup_folder:
        messagebox.showwarning("Missing Information", "Please select all required folders.")
        return

    try:
        minutes = int(minutes_entry.get())
        if not 1 <= minutes <= 1440:  # Updated range to 1440
            raise ValueError("Minutes must be between 1 and 1440.")
        global minutes_until_backup
        minutes_until_backup = minutes
    except ValueError as ve:
        messagebox.showerror("Timer Error", f"Invalid Range. Choose from 1-1440. Error: {ve}")
        return

    backup_start_time = datetime.now()  # Initialize the backup start time
    backup_started = True  # Indicate that backup has started

    # Send separate messages to the Minecraft server
    backup_message = f"Autobackup on | Backup in {minutes_until_backup} minutes."
    if not send_command_to_server(backup_message):
        return  # Exit if the server window was not found

    # Start the timer update loop
    update_timer()

# Function to cancel the auto backup process
def cancel_auto_backup():
    global backup_started
    backup_started = False
    send_command_to_server("Auto Backup canceled.")

# Function to perform a manual backup
def manual_backup():
    # Check if paths are set
    if not server_folder or not world_folder or not backup_folder:
        messagebox.showwarning("Missing Information", "Please select all required folders.")
        return

    now = datetime.now()
    backup_name = get_timestamped_backup_name(os.path.basename(world_folder))
    backup_path = os.path.join(backup_folder, backup_name)

    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)

    try:
        if not os.path.exists(world_folder):
            print(f"World folder does not exist: {world_folder}")
            return

        if not os.access(world_folder, os.R_OK):
            print(f"World folder is not accessible: {world_folder}")
            return

        print(f"Starting to copy files...")
        for root, dirs, files in os.walk(world_folder):
            for file in files:
                if file == "session.lock":
                    continue
                src_file = os.path.join(root, file)
                rel_path = os.path.relpath(src_file, world_folder)
                dest_file = os.path.join(backup_path, rel_path)
                dest_dir = os.path.dirname(dest_file)
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)
                shutil.copy2(src_file, dest_file)

        # Check if the backup was created successfully
        if os.path.exists(backup_path):
            success_message = f"Manual Backup created successfully at {datetime.now().strftime('%m-%d-%Y %I-%M%p')}"
            send_command_to_server(success_message)
        else:
            raise Exception("Backup path does not exist after copy operation.")

    except Exception as e:
        failure_message = f"Manual Backup failed! {datetime.now().strftime('%m-%d-%Y %I-%M%p')}"
        messagebox.showerror("Backup Failure", failure_message)
        send_command_to_server(failure_message)
        print(f"Backup failed with error: {e}")

    log_message(f"Manual Backup created successfully at {datetime.now().strftime('%m-%d-%Y %I-%M%p')}")

# Function to select server folder and update the label
def select_server_folder():
    global server_folder
    server_folder = filedialog.askdirectory(title="Select Server Folder")
    update_folder_label(server_folder_label, server_folder)

# Function to select world folder and update the label
def select_world_folder():
    global world_folder
    world_folder = filedialog.askdirectory(title="Select World Folder")
    update_folder_label(world_folder_label, world_folder)

# Function to select backup folder and update the label
def select_backup_folder():
    global backup_folder
    backup_folder = filedialog.askdirectory(title="Select Backup Folder")
    update_folder_label(backup_folder_label, backup_folder)

# Function to save the current configuration to a JSON file
def save_config():
    config = {
        'server_folder': server_folder,
        'world_folder': world_folder,
        'backup_folder': backup_folder,
        'minutes_until_backup': minutes_until_backup,
        'log_output_enabled': log_output_var.get(),
        'send_messages_enabled': send_messages_var.get()
    }
    filename = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")],
                                           title="Save Config As")
    if filename:
        with open(filename, 'w') as config_file:
            json.dump(config, config_file, indent=4)

# Function to load the configuration from a JSON file
def load_config():
    global server_folder, world_folder, backup_folder, minutes_until_backup
    filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")],
                                          title="Open Config File")
    if filename:
        with open(filename, 'r') as config_file:
            config_data = json.load(config_file)
            server_folder = config_data.get('server_folder', '')
            world_folder = config_data.get('world_folder', '')
            backup_folder = config_data.get('backup_folder', '')
            minutes_until_backup = config_data.get('minutes_until_backup', 20)
            
            # Update labels and entries with the loaded data
            update_folder_label(server_folder_label, server_folder)
            update_folder_label(world_folder_label, world_folder)
            update_folder_label(backup_folder_label, backup_folder)
            
            minutes_entry.delete(0, tk.END)
            minutes_entry.insert(0, str(minutes_until_backup))

            # Set checkbox states
            log_output_var.set(config_data.get('log_output_enabled', True))
            send_messages_var.set(config_data.get('send_messages_enabled', True))
            
            # Update the checkboxes
            on_log_output_toggle()  # Update the log output checkbox state
            on_checkbox_toggle()   # Update the send messages checkbox state
            
# Function to log messages in the log window and to a text file with a timestamp and formatting
def log_message(message):
    log_text.config(state=tk.NORMAL)  # Enable editing
    log_text.insert(tk.END, f"{message}\n")  # Append the message
    log_text.config(state=tk.DISABLED)  # Disable editing
    log_text.yview(tk.END)  # Scroll to the end

    # Check if log output is enabled
    if log_output_var.get():
        log_exists = os.path.exists("log.txt")
        
        with open("log.txt", "a") as log_file:
            if not log_exists:
                log_file.write(f"Log started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            else:
                log_file.write(f"\n\n---\nLog continued at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            log_file.write(message + '\n')

# Function to update folder path labels
def update_folder_label(label, path):
    if path:
        label.config(text=f"Folder: {path}", fg="black")
    else:
        label.config(text="Folder: Not Selected", fg="red")

# Create the main window
root = tk.Tk()
root.title("Minecraft Backup Script")
root.geometry("1280x720")

# Define the relative path to the icon
icon_path = os.path.join('Icon', 'hammer.ico')

# Set the window icon
root.iconbitmap(icon_path)

# Define a common font size for buttons
button_font = ("Arial", 12)  # Adjust the size (12) as needed

# Create the frame for buttons
frame = tk.Frame(root)
frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.Y)

# Define a larger font for buttons
button_font = ("Arial", 12)

# Add a button to load a config
load_config_button = tk.Button(frame, text="Load Config", command=load_config, bg="lightblue", fg="black", width=20, height=2, font=button_font)
load_config_button.grid(row=6, column=1, padx=10, pady=5)

# Add a button to save a config
save_config_button = tk.Button(frame, text="Save Config", command=save_config, bg="lightgreen", fg="black", width=20, height=2, font=button_font)
save_config_button.grid(row=6, column=2, padx=10, pady=5)

# Server folder
server_folder_button = tk.Button(frame, text="Browse Server Folder", command=select_server_folder, bg="tan", fg="black", width=20, height=1, font=button_font)
server_folder_button.grid(row=0, column=1, padx=10, pady=5)
server_folder_label = tk.Label(frame, text="Server Folder: Not Selected", fg="red")
server_folder_label.grid(row=0, column=2, padx=10, pady=5)

# World folder
world_folder_button = tk.Button(frame, text="Browse World Folder", command=select_world_folder, bg="tan", fg="black", width=20, height=1, font=button_font)
world_folder_button.grid(row=1, column=1, padx=10, pady=5)
world_folder_label = tk.Label(frame, text="World Folder: Not Selected", fg="red")
world_folder_label.grid(row=1, column=2, padx=10, pady=5)

# Backup folder
backup_folder_button = tk.Button(frame, text="Browse Backup Folder", command=select_backup_folder, bg="tan", fg="black", width=20, height=1, font=button_font)
backup_folder_button.grid(row=2, column=1, padx=10, pady=5)
backup_folder_label = tk.Label(frame, text="Backup Folder: Not Selected", fg="red")
backup_folder_label.grid(row=2, column=2, padx=10, pady=5)

# Label for minutes until backup
minutes_label = tk.Label(frame, text="Minutes until Backup:", font=button_font)
minutes_label.grid(row=3, column=1, padx=10, pady=5, sticky="e")

# Entry for minutes until backup
minutes_entry = tk.Entry(frame, font=button_font, width=5)
minutes_entry.grid(row=3, column=2, padx=10, pady=5)

# Start Auto Backup button (Green)
start_backup_button = tk.Button(root, text="Start Auto Backup", command=start_auto_backup, bg="green", fg="white", width=20, height=2, font=button_font)
start_backup_button.pack(pady=20)

# Cancel Auto Backup button (Red)
cancel_backup_button = tk.Button(root, text="Cancel Auto Backup", command=cancel_auto_backup, bg="red", fg="white", width=20, height=2, font=button_font)
cancel_backup_button.pack(pady=10)

# Manual Backup button (Yellow)
manual_backup_button = tk.Button(root, text="Manual Backup", command=manual_backup, bg="yellow", fg="black", width=20, height=2, font=button_font)
manual_backup_button.pack(pady=10)

# Timer display
timer_label = tk.Label(root, text="Next Backup in: 00:00 Minutes", font=("Arial", 16))
timer_label.pack(pady=20)

# Log window
log_frame = tk.Frame(root)
log_frame.pack(pady=10, fill=tk.BOTH, expand=True)

log_text = tk.Text(log_frame, height=10, width=80, state=tk.DISABLED)  # Set initial state to disabled
log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

log_scrollbar = tk.Scrollbar(log_frame, command=log_text.yview)
log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
log_text.config(yscrollcommand=log_scrollbar.set)

# Define a larger font for checkboxes
checkbox_font = ("Arial", 12)

# Add a checkbox to enable or disable log output
log_output_var = tk.BooleanVar(value=True)  # Default value is checked (True)
log_output_checkbox = tk.Checkbutton(frame, text="Log Output", variable=log_output_var, command=on_log_output_toggle, font=checkbox_font)
log_output_checkbox.grid(row=5, column=1, columnspan=2, padx=10, pady=5)

# Add a checkbox to enable or disable sending messages to the server
send_messages_var = tk.BooleanVar(value=True)  # Default value is checked (True)
send_messages_checkbox = tk.Checkbutton(frame, text="Send Messages to Server", variable=send_messages_var, command=on_checkbox_toggle, font=checkbox_font)
send_messages_checkbox.grid(row=4, column=1, columnspan=2, padx=10, pady=5)


root.mainloop()

#	||======================================================================================||
#	||    _______           _______  ______   _______ _________ _______  _______  _______ 	||
#	||  (  ____ \|\     /|(  ___  )(  ___ \ (  ___  )\__   __/(  ____ \(  ___  )(       )	||
#	||  | (    \/| )   ( || (   ) || (   ) )| (   ) |   ) (   | (    \/| (   ) || () () |	||
#	||  | |      | (___) || (___) || (__/ / | |   | |   | |   | (__    | (___) || || || |	||
#	||  | |      |  ___  ||  ___  ||  __ (  | |   | |   | |   |  __)   |  ___  || |(_)| |	||
#	||  | |      | (   ) || (   ) || (  \ \ | |   | |   | |   | (      | (   ) || |   | |	||
#	||  | (____/\| )   ( || )   ( || )___) )| (___) |___) (___| )      | )   ( || )   ( |	||
#	||  (_______/|/     \||/     \||/ \___/ (_______)\_______/|/       |/     \||/     \|	||
#	||         																				||
#	|| =====================================================================================||
# 										Version: 2.0
# 								Last Updated: [8.18.2024]
# 			Description: Automatically makes a backup of your MC Server world folder.
#
