import importlib
import importlib.util
import inspect
from typing import Dict, List, Optional, Type, Any
import os
import traceback
import threading
from tkinter import messagebox, ttk, filedialog
import sys
import pandas as pd
from functools import wraps
import webbrowser
import ctypes
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, PhotoImage
from pygments import lex
from pygments.lexers import PythonLexer
from pygments.styles import get_style_by_name
from pygments.token import Token
import subprocess
import logging
# from migrate_logging.Script_Loader import ScriptLoader


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def handle_errors(func):
    def wrapper(self, *args, **kwargs):
        try:
            result = func(self, *args, **kwargs)
            GUI = self.GUI_instance
            GUI.status_label.after(3000, lambda: GUI.update_status(
                "✅ Test completed successfully.", GUI.success_color))
            return result
        except Exception as e:
            GUI = self.GUI_instance
            error_message = f"An error occurred:\n{e}"
            GUI.master.after(0, lambda: GUI.update_status("❌ Error occurred during test.", "red"))
            GUI.master.after(0, lambda: GUI.log_error(error_message))

    return wrapper




def validate_script_selected(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        selected_script = self.command_var.get()
        if not selected_script:
            self.update_status("❌ No Script Selected.", self.error_color)
            messagebox.showerror("Validation Error", "No Script Selected.")
            return
        return func(self, *args, **kwargs)

    return wrapper

class ScriptLoader:
    def __init__(self, scripts_folder="Scripts"):
        self.scripts_folder = scripts_folder
        self.loaded_scripts = {}

    def load_scripts(self,use_docker=False):
        """Load all Python scripts from the Scripts folder"""
        scripts = {}

        # Create Scripts folder if it doesn't exist
        if not os.path.exists(self.scripts_folder):
            os.makedirs(self.scripts_folder)
            print(f"Created '{self.scripts_folder}' folder. Please add your script files there.")
            return scripts

        # Get all .py files in the Scripts folder
        script_files = [f for f in os.listdir(self.scripts_folder) if f.endswith('.py')]

        for script_file in script_files:
            try:
                script_path = os.path.join(self.scripts_folder, script_file)
                script_name = script_file[:-3]  # Remove .py extension

                # Load the module
                spec = importlib.util.spec_from_file_location(script_name, script_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Get script metadata
                display_name = getattr(module, 'SCRIPT_NAME', script_name)
                description = getattr(module, 'SCRIPT_DESCRIPTION', 'No description')
                is_docker = getattr(module, 'is_docker', False)


                # Store the module and metadata
                scripts[display_name] = {
                    'module': module,
                    'file_name': script_file,
                    'description': description,
                    'main_function': getattr(module, 'main', None),
                    'is_docker' : is_docker
                }


                print(f"✅ Loaded script: {display_name}")

            except Exception as e:
                print(f"❌ Error loading {script_file}: {e}")

        self.loaded_scripts = scripts
        return scripts

    def get_script_function(self, script_name):
        """Get the main function from a loaded script"""
        if script_name in self.loaded_scripts:
            return self.loaded_scripts[script_name]['main_function']
        return None

    def refresh_scripts(self):
        """Refresh the loaded scripts"""
        logging.info("🔄 Refreshing scripts...")
        return self.load_scripts()

class TextRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, message):
        self.text_widget.config(state="normal")
        self.text_widget.insert("end", message)
        self.text_widget.see("end")
        self.text_widget.config(state="disabled")

    def flush(self):
        pass  # Required for compatibility with sys
    
class TextLogHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record) + '\n'
        level = record.levelname

        self.text_widget.config(state="normal")
        self.text_widget.insert("end", msg, level)
        self.text_widget.see("end")
        self.text_widget.config(state="disabled")
        
class AliasFormatter(logging.Formatter):
    def format(self, record):
        if "ThreadPoolExecutor" in record.threadName:
            # e.g., ThreadPoolExecutor_0_3 → User 3
            try:
                user_id = record.threadName.split("_")[-1]
                record.threadName = f"User {user_id}"
            except Exception:
                pass
        return super().format(record)

class GUI:

    def __init__(self, master, **kwargs):
        # Tkinter Master
        self.master = master
        self.master.title("GUI Automation")
        self.master.geometry("1420x820")  # Increased width to accommodate side-by-side layout
        self.master.configure(bg="#1E1E2E")  # Dark background


        # Set app icon if available
        icon_path = resource_path("assets/icon.ico")
        try:
            self.master.iconbitmap(icon_path)
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("gui.automation.tool.1.0")

            # Force Windows to update taskbar icon:
            hwnd = ctypes.windll.user32.GetParent(self.master.winfo_id())
            hicon = ctypes.windll.user32.LoadImageW(
                0,
                os.path.abspath(icon_path),
                1,  # IMAGE_ICON
                0,
                0,
                0x00000010  # LR_LOADFROMFILE
            )
            ctypes.windll.user32.SendMessageW(hwnd, 0x80, 0, hicon)  # ICON_SMALL
            ctypes.windll.user32.SendMessageW(hwnd, 0x80, 1, hicon)  # ICON_BIG

        except Exception:
            pass

        # Initialize Script Loader
        self.script_loader = ScriptLoader()

        # Test case Runner
        self.test_runner = None

        # Sys CLI
        self.error_text = tk.Text()

        # UI Color - Dark Mode Theme
        self.settings_ui = {
            "font_main": ("Arial", 10, "bold"),  # Font Style
            "bg_color": "#1E1E2E",  # Dark blue-gray background
            "entry_bg": "#2A2A3C",  # Slightly lighter input background
            "label_color": "#F8F8F2",  # Brighter white for better readability
            "primary_color": "#8BE9FD",  # Bright cyan for better visibility
            "hover_color": "#BD93F9",  # Brighter purple
            "button_color": "#6A5ACD",  # Slate blue
            "accent_color": "#FF79C6",  # Bright pink for better contrast
            "accent_hover": "#FF92D0",  # Lighter pink for hover
            "error_color": "#FF5555",  # Brighter red
            "success_color": "#50FA7B",  # Brighter green
            "warning_color": "#F1FA8C",  # Brighter yellow
            "text_color": "#F8F8F2"  # Brighter white text for better contrast
        }

        for key, value in self.settings_ui.items():
            setattr(self, key, value)


        #Override Title Bar
        # self.master.overrideredirect(True)  # Remove default title bar
        # self.create_custom_title_bar()

        # Top menu toggle bar
        top_menu = tk.Frame(self.master, bg=self.bg_color)
        top_menu.pack(fill="x")

        #Issue Blocked Typing dropdown
        self._after_id = None
        # Tab-like button style for menu
        self.active_tab = tk.StringVar(value="Dashboard")

        def create_tab_button(name, icon, command):
            def on_enter(e): btn.config(bg=self.hover_color)

            def on_leave(e):
                if self.active_tab.get() != name:
                    btn.config(bg=self.entry_bg)

            def on_click():
                self.active_tab.set(name)
                update_tab_colors()
                command()

            btn = tk.Button(top_menu, text=f"{icon} {name}", font=self.font_main,
                            bg=self.entry_bg, fg=self.label_color,
                            activebackground=self.hover_color, activeforeground=self.label_color,
                            relief="flat", bd=0, padx=15, pady=5,
                            cursor="hand2", command=on_click)
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)
            return btn

        def update_tab_colors():
            for name, button in tab_buttons.items():
                if self.active_tab.get() == name:
                    button.config(bg=self.button_color)
                else:
                    button.config(bg=self.entry_bg)

        tab_buttons = {
            "Dashboard": create_tab_button("Dashboard", "📊", self.show_dashboard),
            "Code Editor": create_tab_button("Code Editor", "📝", self.show_editor)
        }

        for btn in tab_buttons.values():
            btn.pack(side="left", padx=5, pady=7)

        update_tab_colors()

        # Create a main container with 2-column grid layout
        self.dashboard_frame = tk.Frame(master, bg=self.bg_color)
        self.dashboard_frame.pack(fill="both", expand=True)

        self.create_dashboard(self.dashboard_frame)

        # Create left frame (for controls) and right frame (for error log)
        self.left_frame = tk.Frame(self.main_container, bg=self.bg_color)
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=5)

        self.right_frame = tk.Frame(self.main_container, bg=self.bg_color)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=10)


        # Editor Frame
        self.editor_frame = tk.Frame(master, bg=self.bg_color)
        self.editor_tab = CodeEditorTab(self.editor_frame)
        self.editor_frame.pack_forget()  # Start hidden

        # Configure the grid to make both columns expandable
        self.main_container.grid_columnconfigure(0, weight=3)  # Left column takes 60% of space
        self.main_container.grid_columnconfigure(1, weight=2)  # Right column takes 40% of space
        self.main_container.grid_rowconfigure(0, weight=1)

        # Script Selection
        # Option Script - Fixed from set to list
        # Script Selection
        script_frame = tk.LabelFrame(self.left_frame, text="🧪 Select Script", font=("Arial", 11, "bold"),
                                     bg=self.bg_color, fg=self.primary_color, padx=8, pady=8, bd=2, relief="groove")
        script_frame.pack(pady=7, fill="x")

        #Form Frame
        form_frame = tk.LabelFrame(self.left_frame, text="Script Configuration",font=("Arial", 11, "bold"),
                                     bg=self.bg_color, fg=self.primary_color, padx=8, pady=8, bd=2, relief="groove")
        form_frame.pack(pady=17, fill="x")
        
        
        
        # Control frame for script selection and refresh
        control_frame = tk.Frame(script_frame, bg=self.bg_color)
        control_frame.pack(fill="x", pady=5)

        tk.Label(control_frame, text="Choose a script to run:", font=self.font_main,
                 bg=self.bg_color, fg=self.primary_color, anchor="w").pack(anchor="w")

        #Checkbox is_docker
        self.use_docker = tk.BooleanVar()
        self.use_docker.set(False)
        docker_checkbox = tk.Checkbutton(
            script_frame,
            text="Use Webdriver Remote Selenium-hub with Docker",
            variable=self.use_docker,
            font=("Arial", 10, "bold"),
            bg=self.bg_color,
            fg=self.label_color,
            activebackground=self.bg_color,
            activeforeground=self.primary_color,
            selectcolor="#2A2A3C",  # Darker background for selected checkbox
            command=self.refresh_scripts
        )
        docker_checkbox.pack()
        
       # Worker Conf 
        tk.Label(
            form_frame,
            text="Total Workers:",
            font=self.font_main,
            bg=self.bg_color,
            fg=self.label_color
        ).grid(row=0, column=0, sticky="w", pady=5)

        self.workers_count = tk.StringVar(value="2")
        tk.Entry(
            form_frame,
            textvariable=self.workers_count,
            font=self.font_main,
            bg=self.entry_bg,
            fg=self.label_color,
            insertbackground=self.label_color,
            relief="flat"
        ).grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        # Setting Headless
        self.headless_mode = tk.BooleanVar(value=True)
        tk.Checkbutton(
            form_frame,
            text="Run Browser in Headless Mode",
            variable=self.headless_mode,
            font=("Arial", 10, "bold"),
            bg=self.bg_color,
            fg=self.label_color,
            activebackground=self.bg_color,
            activeforeground=self.primary_color,
            selectcolor=self.entry_bg
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=5)

        # Delay label
        tk.Label(
            form_frame,
            text="Delay (seconds):",
            font=self.font_main,
            bg=self.bg_color,
            fg=self.label_color
        ).grid(row=2, column=0, sticky="w", pady=5)

        self.delay_seconds = tk.StringVar(value="3")
        tk.Entry(
            form_frame,
            textvariable=self.delay_seconds,
            font=self.font_main,
            bg=self.entry_bg,
            fg=self.label_color,
            insertbackground=self.label_color,
            relief="flat"
        ).grid(row=2, column=1, sticky="ew", padx=5, pady=5)

        # Make column 1 expand properly
        form_frame.grid_columnconfigure(1, weight=1)



        # Script dropdown frame
        dropdown_frame = tk.Frame(script_frame, bg=self.bg_color)
        dropdown_frame.pack(fill="x", pady=5)

        # Load scripts and populate dropdown
        self.command_var = tk.StringVar()
        self.loaded_scripts = self.script_loader.load_scripts()
        self.command_options = list(self.loaded_scripts.keys())

        # Style for combobox
        style = ttk.Style()
        style.theme_use('default')
        style.configure('TCombobox',
                        fieldbackground=self.entry_bg,
                        background=self.primary_color,
                        foreground=self.label_color,
                        arrowcolor=self.primary_color)

        style.map('TCombobox',
                  fieldbackground=[('readonly', self.entry_bg)],
                  foreground=[('readonly', self.primary_color)],
                  selectbackground=[('readonly', self.entry_bg)],
                  selectforeground=[('readonly', self.primary_color)])

        style.theme_use("default")

        # Vertical scrollbar style
        style.configure("Custom.Vertical.TScrollbar",
                        background="#44475A",
                        troughcolor="#1E1E2E",
                        bordercolor="#1E1E2E",
                        lightcolor="#44475A",
                        darkcolor="#44475A",
                        arrowcolor="#F8F8F2"
                        )

        # Horizontal scrollbar style
        style.configure("Custom.Horizontal.TScrollbar",
                        background="#44475A",
                        troughcolor="#1E1E2E",
                        bordercolor="#1E1E2E",
                        lightcolor="#44475A",
                        darkcolor="#44475A",
                        arrowcolor="#F8F8F2"
                        )

        # Combobox with dynamic script list
        self.command_menu = ttk.Combobox(dropdown_frame, textvariable=self.command_var, state="normal",
                                         font=self.font_main)
        self.command_menu['values'] = self.command_options
        self.command_menu.pack(side="left", fill="x", expand=True)

        self.command_menu.bind('<KeyRelease>', self.filter_dropdown)

        # Refresh button
        self.refresh_btn = tk.Button(dropdown_frame, text="Refresh List 🔄", font=("Arial", 10, "bold"),
                                     bg=self.warning_color, fg="#282A36", relief="raised",
                                     padx=10, pady=5, command=self.refresh_scripts)
        self.refresh_btn.pack(side="right", padx=(5, 0))
        self.refresh_btn.bind("<Enter>", lambda e: self.refresh_btn.config(bg="#FFE135"))
        self.refresh_btn.bind("<Leave>", lambda e: self.refresh_btn.config(bg=self.warning_color))

        # Script info label
        self.script_info_label = tk.Label(script_frame, text="Select a script to see description",
                                          font=("Arial", 10), bg=self.bg_color, fg=self.label_color,
                                          wraplength=400, justify="left")
        self.script_info_label.pack(pady=(5, 0), anchor="w")

        # Bind combobox selection event
        self.command_menu.bind('<<ComboboxSelected>>', self.on_script_selected)

        # Button Frame
        button_frame = tk.Frame(self.left_frame, bg=self.bg_color)
        button_frame.pack(pady=20)

        # ---- Start Button ----
        self.start_btn = tk.Button(button_frame, text="🚀 Start Test", font=("Arial", 11, "bold"),
                                   bg="#8BE9FD", fg="#282A36", relief="raised", padx=20, pady=10,
                                   command=self._start)
        self.start_btn.pack(side="left", padx=10)
        self.start_btn.bind("<Enter>", lambda e: self.start_btn.config(bg="#BD93F9"))  # Brighter purple
        self.start_btn.bind("<Leave>", lambda e: self.start_btn.config(bg="#8BE9FD"))  # Bright cyan

        # ---- Clear Log Button ----
        self.clear_btn = tk.Button(button_frame, text="🧹 Clear Log", font=("Arial", 11, "bold"),
                                   bg="#FF79C6", fg="#F8F8F2", relief="raised", padx=20, pady=10,
                                   command=self.clear_log)
        self.clear_btn.pack(side="left", padx=10)
        self.clear_btn.bind("<Enter>", lambda e: self.clear_btn.config(bg="#FF92D0"))  # Lighter pink
        self.clear_btn.bind("<Leave>", lambda e: self.clear_btn.config(bg="#FF79C6"))  # Bright pink

        # ---- Status Label and Author Frame ----
        status_author_frame = tk.Frame(self.left_frame, bg=self.bg_color)
        status_author_frame.pack(pady=10, fill="x")

        # Status Label - Left side
        self.status_label = tk.Label(status_author_frame, text="✅ Status: Ready", font=("Arial", 10, "bold"),
                                     fg=self.success_color, bg=self.bg_color, pady=10, bd=1, relief="solid")

        self.status_label.pack(side="left", fill="x", expand=True, padx=(0, 5))

        # Author frame - Right side
        author_frame = tk.Frame(status_author_frame, bg=self.bg_color, bd=1, relief="solid", padx=5, pady=5)
        author_frame.pack(side="right", padx=(5, 0))

        author_label = tk.Label(author_frame, text="Author:",
                                font=("Arial", 10, "bold"), bg=self.bg_color, fg="#F8F8F2")
        author_label.pack(side="left")

        # GitHub link with hand cursor - direct browser open
        github_link = tk.Label(author_frame, text="MasEylan", font=("Arial", 10, "underline"),
                               bg=self.bg_color, fg="#8BE9FD", cursor="hand2")
        github_link.pack(side="left", padx=(5, 0))
        github_link.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/Maseylan"))
        github_link.bind("<Enter>", lambda e: github_link.config(fg="#BD93F9"))
        github_link.bind("<Leave>", lambda e: github_link.config(fg="#8BE9FD"))


        # Terminal Text
        terminal_font = ("Consolas", 10)  # Larger font

        # ---- Error Output Frame ----
        self.error_frame = tk.LabelFrame(self.right_frame, text="🚨 Terminal Log", font=("Arial", 11, "bold"),
                                         bg=self.bg_color, fg=self.accent_color)
        self.error_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Create a container frame to hold both scrollbars and text widget
        text_container = tk.Frame(self.error_frame, bg=self.bg_color)
        text_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Horizontal scrollbar
        scrollbar_x = ttk.Scrollbar(
            text_container, orient="horizontal",
            style="Custom.Horizontal.TScrollbar"
        )
        scrollbar_x.pack(side="bottom", fill="x")

        # Vertical scrollbar
        scrollbar_y = ttk.Scrollbar(
            text_container, orient="vertical",
            style="Custom.Vertical.TScrollbar"
        )
        scrollbar_y.pack(side="right", fill="y")

        # Text widget with wrap disabled - styled as CLI terminal
        self.error_text = tk.Text(
            text_container,
            font=("Consolas", 11),  # Increased font size from 10 to 11
            wrap="none",
            bg="#282A36",  # Slightly lighter black for better contrast
            fg="#F8F8F2",  # Brighter white
            insertbackground="#F8F8F2",  # cursor color
            selectbackground="#44475A",  # Lighter selection background
            selectforeground="#F8F8F2",  # Bright white selection text
            padx=10,
            pady=10,
            xscrollcommand=scrollbar_x.set,
            yscrollcommand=scrollbar_y.set
        )
        self.error_text.tag_config("INFO", foreground="green")
        self.error_text.tag_config("DEBUG", foreground="red")
        self.error_text.tag_config("WARNING", foreground="red")
        self.error_text.tag_config("ERROR", foreground="red")
        self.error_text.tag_config("CRITICAL", foreground="red", underline=1)
        #Pack self.error_text
        self.error_text.pack(side="left", fill="both", expand=True)

        # Configure scrollbars to control the Text widget
        scrollbar_x.config(command=self.error_text.xview)
        scrollbar_y.config(command=self.error_text.yview)

        self.error_text.insert("1.0", "System initialized. Ready for commands...\n")
        self.error_text.config(state="disabled")

        # Redirect stdout and stderr
        sys.stdout = TextRedirector(self.error_text)
        sys.stderr = TextRedirector(self.error_text)
        # Setup logging
        log_handler = TextLogHandler(self.error_text)
        log_formatter = AliasFormatter('[%(threadName)s] %(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        log_handler.setFormatter(log_formatter)

        logger = logging.getLogger()
        logger.setLevel(logging.INFO)  # Set to INFO to capture all messages
        logger.addHandler(log_handler)

        # Display initial status
        if self.command_options:
            self.update_status(f"✅ Loaded {len(self.command_options)} script(s)", self.success_color)

    def create_dashboard(self, parent):
        # Everything previously under self.main_container...
        self.main_container = tk.Frame(parent, bg=self.bg_color)
        self.main_container.pack(fill="both", expand=True)

    def open_code_editor(self):
        editor_window = tk.Toplevel(self.master)
        editor_window.title("📝 Python Code Editor")
        editor_window.geometry("1000x700")
        editor_window.configure(bg=self.bg_color)

        editor_tab = CodeEditorTab(editor_window)

    def show_dashboard(self):
        self.editor_frame.pack_forget()
        self.dashboard_frame.pack(fill="both", expand=True)

    def show_editor(self):
        self.dashboard_frame.pack_forget()
        self.editor_frame.pack(fill="both", expand=True)


    def on_script_selected(self, event):
        """Handle script selection to show description"""
        selected_script = self.command_var.get()
        if selected_script in self.loaded_scripts:
            description = self.loaded_scripts[selected_script]['description']
            file_name = self.loaded_scripts[selected_script]['file_name']
            self.script_info_label.config(text=f"📄 {file_name}: {description}")
        else:
            self.script_info_label.config(text="No description available")

    def filter_dropdown(self, event=None):
        typed = self.command_var.get().lower()
        keywords = typed.split()

        if keywords:
            values = [
                v for v in self.command_options
                if all(word in v.lower() for word in keywords)
            ]
        else:
            values = self.command_options

        self.command_menu['values'] = values

        # Cancel previous scheduled dropdown opening if any
        if self._after_id:
            self.master.after_cancel(self._after_id)

        # Schedule dropdown to open after 300ms of no typing
        self._after_id = self.master.after(600, self.open_dropdown)

    def open_dropdown(self):
        # Open the dropdown without stealing focus by only generating Down key if widget is focused
        if self.command_menu.focus_get() == self.command_menu:
            self.command_menu.event_generate('<Down>')
        self._after_id = None

    def refresh_scripts(self):
        """Refresh the script list based on Docker checkbox"""
        # self.update_status("🔄 Refreshing scripts...", self.warning_color)

        use_docker = self.use_docker.get()
        all_scripts = self.script_loader.refresh_scripts()

        self.loaded_scripts = {
            name: info for name, info in all_scripts.items()
            if use_docker == info['is_docker']
        }

        self.command_options = list(self.loaded_scripts.keys())
        self.command_menu['values'] = self.command_options

        # current_selection = self.command_var.get()
        # if current_selection not in self.command_options:
        #     self.command_var.set("")
        #     self.script_info_label.config(text="Select a script to see description")
        #
        # if self.command_options:
        #     self.update_status(f"✅ Refreshed: {len(self.command_options)} script(s)", self.success_color)
        # else:
        #     self.update_status("⚠️ No scripts found matching current mode", self.warning_color)

        # Filter based on Docker mode
        if use_docker:
            filtered_scripts = {
                name: info for name, info in all_scripts.items()
                if getattr(info["module"], "is_docker", False) is True
            }
        else:
            filtered_scripts = {
                name: info for name, info in all_scripts.items()
                if not getattr(info["module"], "is_docker", False)
            }

        self.loaded_scripts = filtered_scripts
        self.command_options = list(filtered_scripts.keys())

        # Update combobox
        self.command_menu['values'] = self.command_options

        # Clear current selection if it no longer exists
        current_selection = self.command_var.get()
        if current_selection not in self.command_options:
            self.command_var.set("")
            self.script_info_label.config(text="Select a script to see description")

        # Update status
        if self.command_options:
            self.update_status(f"✅ Refreshed: {len(self.command_options)} script(s)", self.success_color)
        else:
            self.update_status("⚠️ No scripts found matching current mode", self.warning_color)

    def open_scripts_folder(self):
        """Open the Scripts folder in file explorer"""
        scripts_path = os.path.abspath(self.script_loader.scripts_folder)
        try:
            if os.name == 'nt':  # Windows
                os.startfile(scripts_path)
            elif os.name == 'posix':  # macOS and Linux
                os.system(f'open "{scripts_path}"' if sys.platform == 'darwin' else f'xdg-open "{scripts_path}"')
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {e}")

    def clear_log(self):
        """Clear the log/terminal output"""
        self.error_text.config(state="normal")
        self.error_text.delete("1.0", tk.END)
        self.error_text.insert("1.0", "Log cleared. Ready for new commands...\n")
        self.error_text.config(state="disabled")
        self.update_status("🧹 Log cleared", self.success_color)

    def _start(self):
        """
        Main entry point for starting tests - uses decorator-based validation
        Sending Variable To This Function before Validation
        """

        # Clear error log
        self.error_text.config(state="normal")
        self.error_text.delete("1.0", tk.END)
        self.error_text.insert("1.0", "Running test...\n")
        self.error_text.config(state="disabled")

        # Now run the implementation with all validations
        self._validate_and_start()

    @validate_script_selected
    def _validate_and_start(self):
        """Implementation of _start after validation checks pass"""
        selected_script = self.command_var.get()
        
        #Load Form 
        self.workers = int(self.workers_count.get())
        self.headless = self.headless_mode.get()
        self.delay = float(self.delay_seconds.get())
        self.docker = self.use_docker.get()

        # Get script function from loaded scripts
        script_func = self.script_loader.get_script_function(selected_script)

        if script_func is None:
            self.update_status("❌ Script function not found or invalid.", self.error_color)
            messagebox.showerror("Error", f"The script '{selected_script}' does not have a valid 'main' function.")
            return

        # Add debug information
        self.error_text.config(state="normal")
        self.error_text.insert(tk.END, f"Executing script: {selected_script}\n")
        self.error_text.insert(tk.END, f"File: {self.loaded_scripts[selected_script]['file_name']}\n")
        self.error_text.insert(tk.END, "-" * 50 + "\n")
        self.error_text.config(state="disabled")

        def _run_test():
            try:
                self.update_status("🔄 Starting test...", self.warning_color)

                # Pass GUI instance to script if it accepts it
                try:
                    # Try to call with GUI instance
                    script_func(self)
                except TypeError:
                    # If that fails, try without parameters
                    script_func()

                self.update_status("✅ Test completed successfully.", self.success_color)
            except Exception as error:
                self.update_status("❌ Test failed.", self.error_color)
                error_msg = str(error)
                error_text = traceback.format_exc()

                self.error_text.config(state="normal")
                self.error_text.insert(tk.END, f"ERROR: {error_msg}\n\n")
                self.error_text.insert(tk.END, error_text)
                self.error_text.config(state="disabled")

                self.master.after(0, lambda: messagebox.showerror("Error", f"An error occurred:\n{error_msg}"))

        self.update_status("🔄 Preparing to run script...", self.warning_color)
        threading.Thread(target=_run_test, daemon=True).start()

    def update_status(self, message, color):
        self.status_label.config(text=message, fg=color)

    def show_error(self, message):
        self.master.after(0, lambda: messagebox.showerror("Selenium Error", message))

    def log_error(self, message):
        if hasattr(self, 'error_text'):
            self.error_text.config(state='normal')
            self.error_text.insert(tk.END, f"{message}\n")
            self.error_text.config(state='disabled')
            self.error_text.see(tk.END)

class CodeEditorTab:
    def __init__(self, parent):
        self.parent = parent
        self.scripts_folder = "Scripts"
        self.setup_ui()

    def setup_ui(self):
        #Scrollbar styled
        style = ttk.Style()
        style.theme_use('default')


        # Scrollbar style (vertical and horizontal)
        style.element_create("custom.Vertical.Scrollbar.trough", "from", "default")
        style.element_create("custom.Vertical.Scrollbar.thumb", "from", "default")
        style.element_create("custom.Horizontal.Scrollbar.trough", "from", "default")
        style.element_create("custom.Horizontal.Scrollbar.thumb", "from", "default")

        style.layout("Custom.Vertical.TScrollbar",
                     [('Vertical.Scrollbar.trough',
                       {'children': [('Vertical.Scrollbar.thumb', {'unit': '1', 'sticky': 'nswe'})],
                        'sticky': 'ns'})])

        style.layout("Custom.Horizontal.TScrollbar",
                     [('Horizontal.Scrollbar.trough',
                       {'children': [('Horizontal.Scrollbar.thumb', {'unit': '1', 'sticky': 'nswe'})],
                        'sticky': 'we'})])

        style.configure("Custom.Vertical.TScrollbar",
                        background="#44475A", troughcolor="#1E1E2E", bordercolor="#1E1E2E",
                        arrowcolor="#F8F8F2", relief="flat")

        style.configure("Custom.Horizontal.TScrollbar",
                        background="#44475A", troughcolor="#1E1E2E", bordercolor="#1E1E2E",
                        arrowcolor="#F8F8F2", relief="flat")
        #-======================Styled Scrollbar

        # Style the notebook and tabs
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TNotebook", background="#1E1E2E", borderwidth=0)
        style.configure("TNotebook.Tab", background="#44475A", foreground="#F8F8F2", padding=[10, 5], font=("Segoe UI", 10))
        style.map("TNotebook.Tab",
                  background=[("selected", "#6A5ACD")],
                  foreground=[("selected", "#FFFFFF")])

        # Main layout: menu + editor area
        main_frame = tk.Frame(self.parent, bg="#1E1E2E")
        main_frame.pack(fill="both", expand=True)

        # Left menu with listbox and buttons - fixed width to prevent overlap
        self.menu_frame = tk.Frame(main_frame, bg="#2A2A3C", width=200)
        self.menu_frame.pack(side="left", fill="y", padx=5, pady=5)
        self.menu_frame.pack_propagate(False)  # Maintain fixed width

        # Scripts list frame with search bar
        listbox_frame = tk.Frame(self.menu_frame, bg="#2A2A3C", bd=0, highlightthickness=1,
                                 highlightbackground="#44475A")
        listbox_frame.pack(side="top", fill="both", expand=True, padx=5, pady=5)

        #Icon for list file
        # icon_path = resource_path("assets/python_icon.png")
        # if not icon_path :
        #     pass
        # elif not os.path.exists(icon_path):
        #     print("Icon file not found at:", icon_path)
        # self.python_icon = tk.PhotoImage(file=icon_path)

        # Search entry field
        search_var = tk.StringVar()
        self.search_var = search_var  # Save for later access

        search_entry = tk.Entry(listbox_frame, textvariable=search_var,
                                bg="#1E1E2E", fg="#F8F8F2", insertbackground="#F8F8F2",
                                highlightthickness=1, highlightbackground="#44475A",
                                relief="flat", font=("Segoe UI", 12))
        search_entry.pack(fill="x", padx=5, pady=(5, 2))

        def on_focus_in(e):
            if search_entry.get() == "🔍 Search...":
                search_var.set("")

        def on_focus_out(e):
            if not search_entry.get():
                search_var.set("🔍 Search...")

        search_entry.bind("<FocusIn>", on_focus_in)
        search_entry.bind("<FocusOut>", on_focus_out)
        search_entry.bind("<KeyRelease>", self.filter_scripts)

        # Treeview widget
        self.scripts_listbox = ttk.Treeview(listbox_frame,
                                            style="Custom.Treeview",
                                            show="tree",
                                            selectmode="browse")
        style.configure("Custom.Treeview",
                        background="#2A2A3C",
                        foreground="#F8F8F2",
                        fieldbackground="#2A2A3C",
                        borderwidth=0,
                        rowheight=26,
                        font=("Segoe UI", 11))

        style.map("Custom.Treeview",
                  background=[("selected", "#6A5ACD")],
                  foreground=[("selected", "#FFFFFF")])
        self.scripts_listbox.pack(side="left", fill="both", expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", style="Vertical.TScrollbar",
                                  command=self.scripts_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.scripts_listbox.configure(yscrollcommand=scrollbar.set)

        # Bind selection event
        self.scripts_listbox.bind("<<TreeviewSelect>>", self.on_file_select)

        # Buttons under listbox - fixed container
        button_container = tk.Frame(self.menu_frame, bg="#2A2A3C")
        button_container.pack(side="bottom", fill="x", pady=10)

        # Button styling helper
        button_style = {
            "bg": "#6A5ACD",
            "fg": "#F8F8F2",
            "relief": "flat",
            "padx": 10,
            "pady": 5,
            "font": ("Arial", 9)
        }

        #Bind Ctrl F and Ctrl R
        self.parent.bind_all("<Control-f>", self.show_find_dialog)
        self.parent.bind_all("<Control-r>", self.show_replace_dialog)

        self.new_btn = tk.Button(button_container, text="🆕 New", command=self.new_file, **button_style)
        self.new_btn.pack(fill="x", padx=5, pady=2)

        self.rename_btn = tk.Button(button_container, text="✏️ Rename", command=self.rename_file, **button_style)
        self.rename_btn.pack(fill="x", padx=5, pady=2)

        self.open_btn = tk.Button(button_container, text="📂 Open", command=self.open_file, **button_style)
        self.open_btn.pack(fill="x", padx=5, pady=2)

        self.save_btn = tk.Button(button_container, text="💾 Save", command=self.save_file, **button_style)
        self.save_btn.pack(fill="x", padx=5, pady=2)

        self.saveas_btn = tk.Button(button_container, text="📝 Save As", command=self.save_as_file, **button_style)
        self.saveas_btn.pack(fill="x", padx=5, pady=2)

        # Separator between menu and editor
        separator = tk.Frame(main_frame, bg="#44475A", width=1)
        separator.pack(side="left", fill="y", padx=2)

        # Editor container with notebook - takes remaining space
        editor_container = tk.Frame(main_frame, bg="#1E1E2E")
        editor_container.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        self.notebook = ttk.Notebook(editor_container)
        # Message when no file is opened
        self.no_tab_frame = tk.Frame(editor_container, bg="#1E1E2E")
        self.no_tab_label = tk.Label(self.no_tab_frame,
                                     text="📂 No file opened",
                                     font=("Segoe UI", 25, "bold"),
                                     bg="#1E1E2E",
                                     fg="#888888")
        self.no_tab_label.pack(expand=True)
        subtitle = tk.Label(self.no_tab_frame,
                            text="Select File From Folder List or Use 📂 Open or 🆕 New to get started ",
                            font=("Segoe UI", 14),
                            bg="#1E1E2E",
                            fg="#666666")
        subtitle.pack()
        # Initially shown
        self.no_tab_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Right-click context menu for tabs
        self.tab_context_menu = tk.Menu(self.notebook, tearoff=0, bg="#2A2A3C", fg="#F8F8F2")
        self.tab_context_menu.add_command(label="Close Tab", command=self.close_current_tab)
        self.tab_context_menu.add_command(label="Close All Tabs", command=self.close_all_tabs)

        self.notebook.bind("<Button-3>", self.on_right_click_tab)

        self.load_scripts_list()
        self.tabs = {}  # Track file tabs

        # Handle middle-click to close tabs and click on close symbol
        def on_tab_click(event):
            # Find which tab was clicked
            try:
                tab_id = self.notebook.tk.call(self.notebook._w, "identify", "tab", event.x, event.y)
                if tab_id != "":
                    tab_frame = self.notebook.tabs()[int(tab_id)]
                    tab_widget = self.notebook.nametowidget(tab_frame)

                    # Get the tab title to check if close button was clicked
                    tab_title = self.notebook.tab(tab_frame, "text")

                    # Check if click was on the close symbol (✕)
                    if "✕" in tab_title:
                        # Calculate approximate position of close symbol
                        # This is a rough estimation - you might need to adjust
                        tab_bbox = self.notebook.bbox(int(tab_id))
                        if tab_bbox:
                            tab_x, tab_y, tab_w, tab_h = tab_bbox
                            # If click is in the right portion of the tab (where ✕ would be)
                            if event.x > tab_x + tab_w - 20:  # 20 pixels from right edge
                                self.close_tab(tab_widget)
                                return

                    # Otherwise, normal tab selection
                    self.notebook.select(tab_frame)

            except (tk.TclError, IndexError, ValueError):
                pass

        def on_middle_click(event):
            # Find which tab was clicked
            try:
                tab_id = self.notebook.tk.call(self.notebook._w, "identify", "tab", event.x, event.y)
                if tab_id != "":
                    tab_frame = self.notebook.tabs()[int(tab_id)]
                    tab_widget = self.notebook.nametowidget(tab_frame)
                    self.close_tab(tab_widget)
            except (tk.TclError, IndexError, ValueError):
                pass  # Click wasn't on a tab

        self.notebook.bind("<Button-1>", on_tab_click)  # Left click
        self.notebook.bind("<Button-2>", on_middle_click)  # Middle mouse button

        self.load_scripts_list()

    def close_all_tabs(self):
        """Close all tabs"""
        # Make a copy of all tab frames
        all_tabs = list(self.tabs.keys())
        for tab_frame in all_tabs:
            self.close_tab(tab_frame)  # Will auto-show no_tab_label if last

        if not self.notebook.tabs():
            self.no_tab_frame.place(relx=0.5, rely=0.5, anchor="center")

    def prompt_unsaved(self):
        """Prompt user about unsaved changes"""
        return messagebox.askyesno("Unsaved Changes", "There are unsaved changes. Do you want to close without saving?")

    def load_scripts_list(self):
        self.filter_scripts()

    def filter_scripts(self, event=None):
        query = self.search_var.get().lower()
        self.scripts_listbox.delete(*self.scripts_listbox.get_children())

        for file in sorted(os.listdir(self.scripts_folder)):
            if file.endswith(".py") and query in file.lower():
                self.scripts_listbox.insert("", "end", text=file, )
                                            # image=self.python_icon)

    def on_file_select(self, event):
        selected_item = self.scripts_listbox.selection()
        if selected_item:
            item_id = selected_item[0]
            filename = self.scripts_listbox.item(item_id, "text")
            full_path = os.path.join(self.scripts_folder, filename)
            try:
                with open(full_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                self.create_tab(title=filename, content_text=content, file_path=full_path)
            except Exception as e:
                messagebox.showerror("File Load Error", f"Could not open file:\n{e}")

    def open_file(self):
        """Open file dialog and load selected file"""
        file_path = tk.filedialog.askopenfilename(
            title="Open File",
            filetypes=[
                ("Text files", "*.txt"),
                ("Python files", "*.py"),
                ("All files", "*.*")
            ]
        )

        if file_path:
            self.open_file_in_tab(file_path)

    def save_file(self):
        """Save the current file (wrapper for save_current_tab)"""
        self.save_current_tab()

    def new_file(self):
        counter = 1
        while True:
            filename = f"Untitled_{counter}.py"
            file_path = os.path.join(self.scripts_folder, filename)
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    f.write("#from selenium.webdriver.common.by import By \n"
                            "#import time \n"
                            "#from selenium.webdriver.common.keys import Keys \n"
                            "#from Base import Startwebdriver \n"
                            "#import pyautogui \n"
                            "#import random \n"
                            "#import string \n"
                            "#from concurrent.futures import ThreadPoolExecutor \n"
                            "# ============================================================================= \n"
                            "# Example Script: advanced_selenium.py \n "
                            "# This file will be Saved in the 'Scripts' folder \n"
                            "# =============================================================================\n"
                            "# Script metadata (required)\n"
                            "#SCRIPT_NAME = 'Advanced Selenium Test'\n"
                            "#SCRIPT_DESCRIPTION = 'Advanced Selenium automation with multiple browser actions'\n"
                            "#================================================================================= \n"
                             "#def run_test(user_id):\n"
                            "  #  creds = user_credentials[user_id]\n"
                            "   # script = Script(user=creds[\"user\"], passwd=creds[\"passwd\"])\n"
                            "   # script.run_logic(user_id)\n"
                            "\n"
                            "#def main(gui_instance=None):\n"
                            " #   user_count = len(user_credentials)\n"
                            "  #  print(f\"Starting test for {user_count} users...\")\n"
                            "\n"
                            "   # with ThreadPoolExecutor(max_workers=user_count) as executor:\n"
                            "    #    executor.map(run_test, range(user_count))\n")
                break
            counter += 1

        self.load_scripts_list()
        with open(file_path, 'r') as f:
            content = f.read()
        self.create_tab(title=os.path.basename(file_path), content_text=content, file_path=file_path)

    def open_file_in_tab(self, file_path):
        """Open a file in a new tab or switch to existing tab"""
        # Check if file is already open
        existing_tab = self.get_tab_by_file_path(file_path)
        if existing_tab:
            # Switch to existing tab
            self.notebook.select(existing_tab)
            return

        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()

            # Get filename for tab title
            filename = os.path.basename(file_path)

            # Create new tab with file content
            tab_frame, text_widget = self.create_tab(
                title=os.path.basename(file_path),
                content_text=content,
                file_path=file_path
            )

            # Mark as saved (since we just loaded it)
            self.tabs[tab_frame]["unsaved"] = False

            # Bind text change events to mark as unsaved
            def on_text_change(event=None):
                self.tabs[tab_frame]["unsaved"] = True
                # Optionally update tab title to show unsaved state
                current_title = self.tabs[tab_frame]["title"]
                if not current_title.endswith("*"):
                    new_title = current_title + "*"
                    self.notebook.tab(tab_frame, text=new_title)

            text_widget.bind("<<Modified>>", on_text_change)
            text_widget.bind("<Key>", on_text_change)
            text_widget.bind("<KeyRelease>", lambda e: self.schedule_highlight(text_widget))


        except Exception as e:
            # Handle file opening errors
            tk.messagebox.showerror("Error", f"Could not open file: {str(e)}")

    def save_current_tab(self):
        current_tab = self.notebook.select()
        if not current_tab:
            return

        current_frame = self.notebook.nametowidget(current_tab)
        tab_info = self.tabs.get(current_frame, {})

        file_path = tab_info.get("file_path")
        text_widget = tab_info.get("content_widget")

        if not file_path:
            # If still no path, do Save As
            file_path = tk.filedialog.asksaveasfilename(
                defaultextension=".py",
                filetypes=[("Python Files", "*.py"), ("Text Files", "*.txt"), ("All Files", "*.*")]
            )
            if not file_path:
                return  # Cancelled

        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(text_widget.get("1.0", "end-1c"))

            self.tabs[current_frame]["file_path"] = file_path
            self.tabs[current_frame]["unsaved"] = False
            filename = os.path.basename(file_path)
            self.notebook.tab(current_frame, text=filename)
            self.tabs[current_frame]["title"] = filename  # update clean title


        except Exception as e:
            tk.messagebox.showerror("Error", f"Could not save file: {str(e)}")

    def save_as_file(self):
        current_tab = self.notebook.select()
        file_path = filedialog.asksaveasfilename(defaultextension=".py", filetypes=[("Python Files", "*.py")])
        if file_path:
            content = self.tabs[current_tab]["content_widget"].get("1.0", tk.END)
            with open(file_path, 'w') as file:
                file.write(content)
            self.notebook.tab(current_tab, text=os.path.basename(file_path))
            self.tabs[current_tab]["file_path"] = file_path  # <-- fix key name
            self.tabs[current_tab]["unsaved"] = False
            messagebox.showinfo("Saved", f"File saved: {file_path}")

    def rename_file(self):
        selection = self.scripts_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a file to rename.")
            return

        index = selection[0]
        old_name = self.scripts_listbox.get(index)
        old_path = os.path.join(self.scripts_folder, old_name)

        # Create a popup window
        popup = tk.Toplevel(self.parent)
        popup.title("Rename File")
        popup.geometry("300x120")
        popup.configure(bg="#2A2A3C")

        tk.Label(popup, text="Rename file to:", bg="#2A2A3C", fg="#F8F8F2", font=("Arial", 10)).pack(pady=(10, 0))

        entry = tk.Entry(popup, font=("Arial", 10), bg="#282A36", fg="#F8F8F2", insertbackground="#F8F8F2")
        entry.insert(0, old_name)
        entry.pack(pady=5, padx=10, fill="x")

        def do_rename():
            new_name = entry.get().strip()
            if not new_name:
                messagebox.showerror("Error", "Filename cannot be empty.")
                return
            if not new_name.endswith(".py"):
                new_name += ".py"

            new_path = os.path.join(self.scripts_folder, new_name)

            if os.path.exists(new_path):
                messagebox.showerror("Error", "A file with that name already exists.")
                return

            try:
                os.rename(old_path, new_path)
                self.load_scripts_list()
                messagebox.showinfo("Renamed", f"File renamed to: {new_name}")

                # Update any open tab
                for tab_id, tab_data in self.tabs.items():
                    if tab_data["file_path"] == old_path:
                        tab_data["file_path"] = new_path
                        self.notebook.tab(tab_id, text=new_name)
                        break

                popup.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Rename failed: {e}")

        rename_button = tk.Button(popup, text="✅ Rename", command=do_rename,
                                  bg="#50FA7B", fg="#282A36", padx=10, pady=5)
        rename_button.pack(pady=5)

    def close_tab_by_frame(self, frame):
        index = self.notebook.index(frame)
        tab_id = self.notebook.tabs()[index]
        tab_data = self.tabs.get(tab_id)

        if tab_data and tab_data.get("unsaved"):
            result = self.show_save_prompt()
            if result == "save":
                self.notebook.select(frame)
                self.save_file()
            elif result == "cancel":
                return  # Abort closing

        del self.tabs[tab_id]
        self.notebook.forget(frame)

    def add_tab_with_close(self, frame, title):
        tab_text = tk.Frame(self.notebook, bg="#44475A")

        label = tk.Label(tab_text, text=title, bg="#44475A", fg="#F8F8F2", font=("Arial", 10))
        label.pack(side="left", padx=(5, 2))

        close_btn = tk.Button(tab_text, text="❌", bg="#44475A", fg="#F8F8F2",
                              font=("Arial", 10, "bold"), borderwidth=0,
                              command=lambda: self.close_tab_by_frame(frame))
        close_btn.pack(side="right", padx=(2, 5))

        self.notebook.add(frame, text="")  # Temporarily blank
        tab_id = self.notebook.tabs()[-1]
        self.tabs[tab_id] = {
            "content_widget": frame.winfo_children()[0],
            "file_path": title if title.endswith(".py") else None,
            "unsaved": False,
            "title": title
        }

        # Place tab_text as window after delay to avoid layout issues
        self.parent.after(100, lambda: self.notebook.tab(frame, compound="left", text="", image="", state="normal",
                                                         sticky="w"))
        self.parent.after(100, lambda: self.notebook.tab(frame, widget=tab_text))

        self.notebook.select(frame)

    def create_tab(self, title, content_text=None, file_path=None):
        """Create a tab with line numbers, styled scrollbars, and syntax highlighting"""
        #hide Message
        self.no_tab_frame.place_forget()

        if not self.notebook.winfo_ismapped():
            self.notebook.pack(fill="both", expand=True)

        tab_frame = tk.Frame(self.notebook, bg="#1E1E2E")
        text_frame = tk.Frame(tab_frame, bg="#1E1E2E")
        text_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # --- Line Numbers Widget ---
        line_numbers = tk.Text(text_frame,
                               width=4,
                               padx=4,
                               takefocus=0,
                               border=0,
                               background="#2A2A3C",
                               foreground="#888888",
                               state="disabled",
                               wrap="none",
                               font=("Consolas", 11))
        line_numbers.grid(row=0, column=0, sticky="ns")

        # --- Main Text Widget ---
        text_widget = tk.Text(text_frame,
                              bg="#2A2A3C",
                              fg="#F8F8F2",
                              insertbackground="#F8F8F2",
                              font=("Consolas", 11),
                              wrap="none",
                              undo=True)
        text_widget.grid(row=0, column=1, sticky="nsew")

        # --- Scrollbars ---
        v_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview,
                                    style="Custom.Vertical.TScrollbar")
        v_scrollbar.grid(row=0, column=2, sticky="ns")

        h_scrollbar = ttk.Scrollbar(text_frame, orient="horizontal", command=text_widget.xview,
                                    style="Custom.Horizontal.TScrollbar")
        h_scrollbar.grid(row=1, column=1, sticky="ew")

        text_widget.config(
            yscrollcommand=lambda *args: [v_scrollbar.set(*args), self.update_line_numbers(line_numbers, text_widget)],
            xscrollcommand=h_scrollbar.set)

        # --- Grid Weight ---
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(1, weight=1)

        # --- Initial Content ---
        if content_text:
            text_widget.insert("1.0", content_text)
            text_widget.mark_set("insert", "1.0")

        # --- Syntax Highlighting ---
        text_widget.bind("<KeyRelease>", lambda e: self.schedule_highlight(text_widget))
        self.schedule_highlight(text_widget)

        # --- Line Number Updates ---
        text_widget.bind("<KeyRelease>", lambda e: self.update_line_numbers(line_numbers, text_widget))
        text_widget.bind("<MouseWheel>", lambda e: self.update_line_numbers(line_numbers, text_widget))
        text_widget.bind("<Button-4>", lambda e: self.update_line_numbers(line_numbers, text_widget))  # Linux scroll up
        text_widget.bind("<Button-5>",
                         lambda e: self.update_line_numbers(line_numbers, text_widget))  # Linux scroll down

        # --- Unsaved Marker Handling ---
        text_widget.edit_modified(False)

        def on_modified(event):
            if text_widget.edit_modified():
                if not self.tabs[tab_frame]["unsaved"]:
                    self.tabs[tab_frame]["unsaved"] = True
                    current_title = self.tabs[tab_frame]["title"]
                    if not current_title.endswith("*"):
                        self.notebook.tab(tab_frame, text=current_title + "*Unsaved")
                text_widget.edit_modified(False)

        text_widget.bind("<<Modified>>", on_modified)

        # --- Add Tab ---
        self.notebook.add(tab_frame, text=title)
        self.tabs[tab_frame] = {
            "title": title,
            "unsaved": False,
            "content_widget": text_widget,
            "file_path": file_path,
            "line_widget": line_numbers
        }
        self.notebook.select(tab_frame)

        # Initial update of line numbers
        self.update_line_numbers(line_numbers, text_widget)

        return tab_frame, text_widget

    def update_line_numbers(self, line_widget, text_widget):
        """Update line numbers to match text widget"""
        line_widget.config(state="normal")
        line_widget.delete("1.0", "end")

        # Get visible range
        first_index = text_widget.index("@0,0")
        last_index = text_widget.index("@0,%d" % text_widget.winfo_height())

        first_line = int(first_index.split(".")[0])
        last_line = int(last_index.split(".")[0])

        # Generate line numbers for only visible lines
        line_numbers = "\n".join(str(i) for i in range(first_line, last_line + 1))
        line_widget.insert("1.0", line_numbers)
        line_widget.config(state="disabled")

    def highlight_syntax(self, text_widget):

        code = text_widget.get("1.0", tk.END)
        text_widget.tag_remove("Token", "1.0", tk.END)

        for tag in text_widget.tag_names():
            if tag.startswith("Token."):
                text_widget.tag_remove(tag, "1.0", tk.END)

        index = "1.0"
        tokens = list(lex(code, PythonLexer()))
        i = 0

        while i < len(tokens):
            token, content = tokens[i]
            tag_name = str(token)

            if not content:
                i += 1
                continue

            # --- Detect function/method calls ---
            if (token in [Token.Name, Token.Name.Attribute]
                    and i + 1 < len(tokens)
                    and tokens[i + 1][1] == '('):
                tag_name = "Token.Function.Call"

            # --- Detect regular variable assignment like `var =` ---
            elif (token == Token.Name
                  and i + 1 < len(tokens)
                  and tokens[i + 1][1] == '='):
                tag_name = "Token.Variable"

            # --- Detect attribute assignment like `self.attr =` ---
            elif (
                    token == Token.Name.Builtin.Pseudo and
                    i + 2 < len(tokens) and
                    tokens[i + 1][0] == Token.Operator and tokens[i + 1][1] == '.' and
                    tokens[i + 2][0] == Token.Name.Attribute and
                    i + 3 < len(tokens) and tokens[i + 3][1] == '='
            ):
                # Color `self` (optional)
                tag_self = "Token.Name.Builtin.Pseudo"
                tag_attr = "Token.Variable.Attribute"

                if tag_attr not in text_widget.tag_names():
                    text_widget.tag_configure(tag_attr, foreground=self.token_color(tag_attr))

                # Highlight the attribute name (e.g. 'first')
                attr_len = len(tokens[i + 2][1])
                attr_index = text_widget.index(f"{index}+{len(tokens[i][1]) + 1}c")
                end_attr_index = text_widget.index(f"{attr_index}+{attr_len}c")
                text_widget.tag_add(tag_attr, attr_index, end_attr_index)

                # Skip `self`, `.`, and `first`
                total_len = len(tokens[i][1]) + len(tokens[i + 1][1]) + len(tokens[i + 2][1])
                index = text_widget.index(f"{index}+{total_len}c")
                i += 3
                continue

            # --- Configure the tag color ---
            if tag_name not in text_widget.tag_names():
                text_widget.tag_configure(tag_name, foreground=self.token_color(tag_name))

            start_index = index
            end_index = text_widget.index(f"{start_index}+{len(content)}c")
            text_widget.tag_add(tag_name, start_index, end_index)

            index = end_index
            i += 1

    def schedule_highlight(self, text_widget):
        if hasattr(self, '_highlight_job'):
            text_widget.after_cancel(self._highlight_job)
        self._highlight_job = text_widget.after(300, lambda: self.highlight_syntax(text_widget))

    def token_color(self, token):
        token_str = str(token)

        if token_str == "Token.Function.Call":
            return "#00BFFF"  # Cyan
        elif token_str == "Token.Variable":
            return "#FFB86C"  # Orange
        elif token_str == "Token.Variable.Attribute":
            return "#FFB86C"
        elif token_str == "Token.Keyword.Namespace":
            return "#FF5555"
        elif token_str.startswith("Token.Keyword"):
            return "#FF79C6"
        elif token_str == "Token.Name.Builtin.Pseudo":  # self
            return "#FFB86C"
        elif token_str == "Token.Name.Function":
            return "#50FA7B"
        elif token_str == "Token.Name.Class":
            return "#8BE9FD"
        elif token_str.startswith("Token.Comment"):
            return "#6272A4"
        elif token_str.startswith("Token.String"):
            return "#F1FA8C"
        elif token_str.startswith("Token.Operator"):
            return "#FF79C6"
        elif token_str.startswith("Token.Number"):
            return "#BD93F9"
        elif token_str == "Token.Name.Builtin":
            return "#8BE9FD"
        elif token_str.startswith("Token.Literal.String"):
            return "#F1FA8C"
        elif token_str == "Token.Variable.Attribute":
            return "#FFB86C"  # orange
        elif token_str == "Token.Punctuation":
            return "#FF79C6"  # Pink/magenta for punctuation like {}, []
        elif token_str == "Token.Name.Attribute":
            return "#00BFFF"  # Blueish for e.g., `choices` in random.choices()
        elif token_str.startswith("Token.Literal.Number"):
            return "#BD93F9"

        return "#F8F8F2"

    def close_current_tab(self):
        """Close the currently selected tab"""
        try:
            current_tab = self.notebook.select()
            if current_tab:
                # Convert string ID to actual widget
                current_frame = self.notebook.nametowidget(current_tab)
                self.close_tab(current_frame)
        except tk.TclError:
            pass  # No tab selected

    def on_text_modified(self, event):
        widget = event.widget
        if widget.edit_modified():
            tab_id = self.notebook.select()
            if tab_id in self.tabs:
                self.tabs[tab_id]["unsaved"] = True
            widget.edit_modified(False)  # Reset flag

    def on_right_click_tab(self, event):
        """Handle right-click on tab to show context menu"""
        try:
            # Check if we clicked on a tab
            tab_id = self.notebook.tk.call(self.notebook._w, "identify", "tab", event.x, event.y)
            if tab_id != "":
                # Select the tab that was right-clicked
                tab_frame = self.notebook.tabs()[int(tab_id)]
                self.notebook.select(tab_frame)
                # Show context menu
                self.tab_context_menu.tk_popup(event.x_root, event.y_root)
        except (tk.TclError, IndexError, ValueError):
            pass  # Click wasn't on a tab
        finally:
            self.tab_context_menu.grab_release()

    def show_save_prompt(self):
        prompt = tk.Toplevel(self.parent)
        prompt.title("Unsaved Changes")
        prompt.configure(bg="#2A2A3C")
        prompt.geometry("350x150")
        prompt.resizable(False, False)
        prompt.grab_set()

        label = tk.Label(prompt, text="💾 Do you want to save changes before closing?",
                         font=("Arial", 10, "bold"), bg="#2A2A3C", fg="#F8F8F2", wraplength=320)
        label.pack(pady=20)

        button_frame = tk.Frame(prompt, bg="#2A2A3C")
        button_frame.pack(pady=10)

        def choose(value):
            prompt.grab_release()
            prompt.destroy()
            prompt.result = value

        tk.Button(button_frame, text="Save", width=10, bg="#50FA7B", fg="#1E1E2E",
                  font=("Arial", 10, "bold"), command=lambda: choose("save")).pack(side="left", padx=5)
        tk.Button(button_frame, text="Discard", width=10, bg="#FF5555", fg="#F8F8F2",
                  font=("Arial", 10, "bold"), command=lambda: choose("discard")).pack(side="left", padx=5)
        tk.Button(button_frame, text="Cancel", width=10, bg="#BD93F9", fg="#1E1E2E",
                  font=("Arial", 10, "bold"), command=lambda: choose("cancel")).pack(side="left", padx=5)

        prompt.wait_window()
        return getattr(prompt, "result", "cancel")

    def create_tab_with_close(self, title, content_widget=None):
        """Create a tab with a close button in the tab header"""
        # Create the main tab frame
        tab_frame = tk.Frame(self.notebook, bg="#1E1E2E")

        # If no content widget provided, create a text editor
        if content_widget is None:
            # Create text editor with scrollbar
            text_frame = tk.Frame(tab_frame, bg="#1E1E2E")
            text_frame.pack(fill="both", expand=True, padx=5, pady=5)

            content_widget = tk.Text(text_frame,
                                     bg="#2A2A3C",
                                     fg="#F8F8F2",
                                     insertbackground="#F8F8F2",
                                     font=("Consolas", 11),
                                     wrap="none",
                                     undo=True)

            # Add scrollbars
            v_scrollbar = tk.Scrollbar(text_frame, orient="vertical", command=content_widget.yview)
            h_scrollbar = tk.Scrollbar(text_frame, orient="horizontal", command=content_widget.xview)

            content_widget.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

            # Pack text widget and scrollbars
            content_widget.pack(side="left", fill="both", expand=True)
            v_scrollbar.pack(side="right", fill="y")
            h_scrollbar.pack(side="bottom", fill="x")
        else:
            # Use provided content widget - pack it properly
            content_widget.pack(in_=tab_frame, fill="both", expand=True, padx=5, pady=5)

        # Add tab to notebook with a close button symbol in the title
        tab_title_with_close = f"{title}  ✕"
        self.notebook.add(tab_frame, text=tab_title_with_close)

        # Store tab info
        self.tabs[tab_frame] = {
            "title": title,
            "original_title": title,
            "unsaved": False,
            "content_widget": content_widget
        }

        # Select the newly created tab
        self.notebook.select(tab_frame)

        return tab_frame

    def create_tab_with_embedded_close(self, title, content_widget=None):
        """Create a tab with close button embedded in the content area"""
        # Create the main tab frame
        tab_frame = tk.Frame(self.notebook, bg="#1E1E2E")

        # Create header frame with title and close button
        header_frame = tk.Frame(tab_frame, bg="#1E1E2E", height=30)
        header_frame.pack(fill="x", pady=2)
        header_frame.pack_propagate(False)

        # Tab title
        title_label = tk.Label(header_frame, text=title, bg="#1E1E2E", fg="#F8F8F2", font=("Arial", 10))
        title_label.pack(side="left", padx=5)

        # Close button
        close_btn = tk.Button(header_frame, text="×",
                              command=lambda: self.close_tab(tab_frame),
                              bg="#FF5555", fg="#FFFFFF",
                              relief="flat", width=2, height=1,
                              font=("Arial", 8, "bold"))
        close_btn.pack(side="right", padx=5)

        # Content area
        content_frame = tk.Frame(tab_frame, bg="#1E1E2E")
        content_frame.pack(fill="both", expand=True)

        # Handle content widget
        if content_widget is None:
            # Create text editor
            text_frame = tk.Frame(content_frame, bg="#1E1E2E")
            text_frame.pack(fill="both", expand=True, padx=5, pady=5)

            content_widget = tk.Text(text_frame,
                                     bg="#2A2A3C",
                                     fg="#F8F8F2",
                                     insertbackground="#F8F8F2",
                                     font=("Consolas", 11),
                                     wrap="none",
                                     undo=True)

            # Add scrollbars
            v_scrollbar = tk.Scrollbar(text_frame, orient="vertical", command=content_widget.yview)
            h_scrollbar = tk.Scrollbar(text_frame, orient="horizontal", command=content_widget.xview)

            content_widget.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

            # Pack text widget and scrollbars
            content_widget.pack(side="left", fill="both", expand=True)
            v_scrollbar.pack(side="right", fill="y")
            h_scrollbar.pack(side="bottom", fill="x")
        else:
            # Pack the provided content widget
            content_widget.pack(in_=content_frame, fill="both", expand=True, padx=5, pady=5)

        # Add tab to notebook (without close symbol since it's embedded)
        self.notebook.add(tab_frame, text=title)

        # Store tab info
        self.tabs[tab_frame] = {
            "title": title,
            "unsaved": False,
            "content_widget": content_widget
        }

        # Select the newly created tab
        self.notebook.select(tab_frame)

        return tab_frame

    def close_tab(self, tab_frame):
        """Close a specific tab with unsaved changes check"""
        if self.tabs.get(tab_frame, {}).get("unsaved"):
            if not self.prompt_unsaved():
                return

            # Remove from notebook and memory
        self.notebook.forget(tab_frame)
        tab_frame.destroy()
        self.tabs.pop(tab_frame, None)

        # ✅ If no tabs remain
        if not self.notebook.tabs():
            self.notebook.pack_forget()
            self.no_tab_frame.place(relx=0.5, rely=0.5, anchor="center")

    def show_search_popup(self, mode="find"):
        current_tab = self.notebook.select()
        if not current_tab:
            return

        current_frame = self.notebook.nametowidget(current_tab)
        text_widget = self.tabs.get(current_frame, {}).get("content_widget")
        if not text_widget:
            return

        popup = tk.Toplevel(self.parent)
        popup.title("Find" if mode == "find" else "Replace")
        popup.geometry("400x280" if mode == "replace" else "400x150")
        popup.configure(bg="#2A2A3C")
        popup.resizable(False, False)
        popup.transient(self.parent)
        popup.grab_set()
        try:
            popup.iconbitmap("assets/icon.ico")
        except Exception as e:
            print(f"Failed to set icon: {e}")

        # State tracking
        matches = []
        current_index = [0]

        def update_status():
            if not matches:
                status_label.config(text="No matches", fg="#FF5555")
            else:
                status_label.config(text=f"{current_index[0] + 1} of {len(matches)}", fg="#50FA7B")

        def do_find():
            nonlocal matches
            search_text = find_entry.get()
            matches.clear()
            text_widget.tag_remove("search_match", "1.0", tk.END)

            if search_text:
                start_pos = "1.0"
                while True:
                    start_pos = text_widget.search(search_text, start_pos, stopindex=tk.END, nocase=True)
                    if not start_pos:
                        break
                    end_pos = f"{start_pos}+{len(search_text)}c"
                    matches.append((start_pos, end_pos))
                    start_pos = end_pos

                for start, end in matches:
                    text_widget.tag_add("search_match", start, end)
                text_widget.tag_config("search_match", background="#FFB86C", foreground="#282A36")

                if matches:
                    current_index[0] = 0
                    move_to_match(0)

            update_status()

        def move_to_match(index):
            if not matches:
                return
            text_widget.tag_remove("active_match", "1.0", tk.END)
            start, end = matches[index]
            text_widget.tag_add("active_match", start, end)
            text_widget.tag_config("active_match", background="#FF79C6", foreground="#FFFFFF")
            text_widget.mark_set(tk.INSERT, start)
            text_widget.see(start)
            update_status()

        def prev_match():
            if not matches:
                return
            current_index[0] = (current_index[0] - 1) % len(matches)
            move_to_match(current_index[0])

        def next_match():
            if not matches:
                return
            current_index[0] = (current_index[0] + 1) % len(matches)
            move_to_match(current_index[0])

        def do_replace_current():
            if not matches:
                return
            start, end = matches[current_index[0]]
            text_widget.delete(start, end)
            text_widget.insert(start, replace_entry.get())
            do_find()  # Re-scan matches after replacement

        def do_replace_all():
            search_text = find_entry.get()
            replace_text = replace_entry.get()
            if search_text:
                content = text_widget.get("1.0", tk.END)
                new_content = content.replace(search_text, replace_text)
                text_widget.delete("1.0", tk.END)
                text_widget.insert("1.0", new_content)
                self.tabs[current_frame]["unsaved"] = True
                popup.destroy()

        # UI Elements
        tk.Label(popup, text="Find:", bg="#2A2A3C", fg="#F8F8F2", font=("Arial", 10)).pack(pady=(10, 0))
        find_entry = tk.Entry(popup, width=30, bg="#282A36", fg="#F8F8F2", insertbackground="#F8F8F2")
        find_entry.pack(pady=5)
        find_entry.focus_set()

        # Status and navigation
        nav_frame = tk.Frame(popup, bg="#2A2A3C")
        nav_frame.pack(pady=(5, 0))
        status_label = tk.Label(nav_frame, text="No matches", font=("Arial", 9), bg="#2A2A3C", fg="#888888")
        status_label.pack(side="left", padx=10)

        tk.Button(nav_frame, text="◀", command=prev_match, width=3, bg="#6272A4", fg="#F8F8F2").pack(side="left",
                                                                                                     padx=5)
        tk.Button(nav_frame, text="▶", command=next_match, width=3, bg="#6272A4", fg="#F8F8F2").pack(side="left",
                                                                                                     padx=5)

        tk.Button(nav_frame, text="Find All", command=do_find, bg="#50FA7B", fg="#1E1E2E").pack(side="right", padx=5)

        if mode == "replace":
            # Replace entry
            tk.Label(popup, text="Replace with:", bg="#2A2A3C", fg="#F8F8F2", font=("Arial", 10)).pack(pady=(10, 0))
            replace_entry = tk.Entry(popup, width=30, bg="#282A36", fg="#F8F8F2", insertbackground="#F8F8F2")
            replace_entry.pack(pady=5)

            btn_frame = tk.Frame(popup, bg="#2A2A3C")
            btn_frame.pack(pady=10)

            tk.Button(btn_frame, text="Replace Current", command=do_replace_current, width=15,
                      bg="#8BE9FD", fg="#1E1E2E").pack(side="left", padx=5)

            tk.Button(btn_frame, text="Replace All", command=do_replace_all, width=12,
                      bg="#FFB86C", fg="#282A36").pack(side="left", padx=5)

            tk.Button(btn_frame, text="Close", command=popup.destroy,
                      bg="#FF5555", fg="#F8F8F2").pack(side="left", padx=5)
        else:
            tk.Button(popup, text="Close", command=popup.destroy,
                      bg="#FF5555", fg="#F8F8F2").pack(pady=10)

    def show_find_dialog(self, event=None):
        self.show_search_popup(mode="find")

    def show_replace_dialog(self, event=None):
        self.show_search_popup(mode="replace")

class Test_case:
    def __init__(self, GUI_instance):
        self.GUI_instance = GUI_instance
        self.Script_instance = None


def main():
    root = tk.Tk()
    app = GUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()