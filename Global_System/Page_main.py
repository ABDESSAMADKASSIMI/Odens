#main Sytem
import os
import shutil
import time
import tkinter as tk
import customtkinter as ctk
import csv
import yfinance as yf
from datetime import datetime
from tkinter import messagebox
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from Page_1 import PredictionPage
from Page_2 import TrainPage
from Page_3 import StatisticsPage
from Page_4 import VersionsPage
import threading  
import customtkinter as ctk
import threading
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import yfinance as yf
from datetime import datetime

def get_aluminium_price():
    try:
        data = yf.download("ALI=F", period="5d")['Close']
        last_val = float(data.dropna().iloc[-1])
        return last_val
    except Exception: 
        return "N/A"

class HomePage(ctk.CTkFrame):
    def __init__(self, master, user_info, on_use_model, on_train_model, show_buttons=True):
        super().__init__(master, fg_color="#0C1C2C")
        self.user_info = user_info
        self.show_buttons = show_buttons
        self.on_use_model = on_use_model
        self.on_train_model = on_train_model

        # Overlay card style: main container
        overlay = ctk.CTkFrame(self, fg_color="#152942", corner_radius=34)
        overlay.pack(pady=30, padx=30, fill="both", expand=True)

        # Welcome block
        title_font = ("Segoe UI Black", 36, "bold")
        sub_font = ("Segoe UI", 18, "bold")
        hello_lbl = ctk.CTkLabel(
            overlay, text=f"👋 Hello, {user_info['first_name']}!", font=title_font, text_color="#8CE8FF"
        )
        hello_lbl.pack(pady=(22, 6))

        ctk.CTkLabel(
            overlay, text="Welcome to your Pricing Powered IA Engine",
            font=sub_font, text_color="#8CE8FF"
        ).pack(pady=0)
        ctk.CTkLabel(
            overlay, text="",
            font=("Segoe UI", 15), text_color="#B7BEDD"
        ).pack(pady=(0, 13))

        # Clock & Price
        info_frame = ctk.CTkFrame(overlay, fg_color="#182840", corner_radius=18)
        info_frame.pack(pady=(8, 3))
        self.clock_lbl = ctk.CTkLabel(info_frame, text="", font=("Consolas", 18, "bold"), text_color="#8CE8FF")
        self.clock_lbl.grid(row=0, column=0, padx=18, pady=13)
        self.price_lbl = ctk.CTkLabel(info_frame, text="", font=("Consolas", 17, "bold"), text_color="#8CE8FF")
        self.price_lbl.grid(row=0, column=1, padx=18)
        self.update_time_and_price()

        # Professional description
        desc = (
            f"Hey {user_info['first_name']}, welcome to your Price Engine designed by Odens!\n"
            "This engine is powered by artificial intelligence to help you predict aluminium prices at any moment with high accuracy. "
            "You can train a new model on your own data at any time, and have full control to use or train whichever model you want."
        )
        ctk.CTkLabel(
            overlay,
            text=desc,
            font=("Segoe UI", 16, "bold"),
            text_color="#F7F9FE",
            justify="center",
            wraplength=820
        ).pack(pady=(22, 4))

        # Chart area
        chart_outer = ctk.CTkFrame(overlay, fg_color="#1D2B3C", corner_radius=20)
        chart_outer.pack(pady=(36, 14))
        self.display_price_chart(chart_outer)

        # Buttons
        self.btns_frame = ctk.CTkFrame(overlay, fg_color="transparent")
        self.btns_frame.pack(pady=8)
        if self.show_buttons:
            self.fancy_button("Use Our Model", self.on_use_model, "left")
            self.fancy_button("Train Your Own Model", self.on_train_model, "right")

        ctk.CTkLabel(overlay, text="designed by Odens 2025", font=("Segoe UI", 13, "bold"), text_color="#40D9FF").pack(side="bottom", pady=10)

    # ... keep your update_time_and_price, display_price_chart, and fancy_button code as is ...

    def update_time_and_price(self):
        now = datetime.now().strftime("%A, %d %b %Y | %H:%M:%S")
        self.clock_lbl.configure(text=now)

        def fetch_price():
            price_per_kg = get_aluminium_price()
            try:
                price_per_kg_f = float(price_per_kg/1000)
                price_per_ton = round(price_per_kg_f * 1000, 2)
                price_text = (
                    f"Aluminium price per kg: {price_per_kg_f} €/kg\n"
                    f"Aluminium price per ton: {price_per_ton} €/ton"
                )
            except Exception:
                price_text = f"Aluminium price per kg: {price_per_kg} €/kg"
            self.price_lbl.after(0, lambda: self.price_lbl.configure(text=price_text))

        threading.Thread(target=fetch_price, daemon=True).start()
        self.after(2000, self.update_time_and_price)

    def display_price_chart(self, frame):
        def fetch_and_plot():
            try:
                data = yf.download("ALI=F", period="30d")['Close'].dropna()
                dates = [d.strftime("%d %b") for d in data.index][-15:]
                prices = np.array(data.values)[-15:].flatten()
            except Exception as e:
                prices = np.linspace(2, 3, 15)
                dates = [f"Day {i+1}" for i in range(15)]

            def draw_chart():
                fig, ax = plt.subplots(figsize=(10, 3.7), dpi=100)
                fig.patch.set_facecolor("#1D2B3C")
                ax.set_facecolor("#23344B")
                ax.plot(dates, prices, color="#22DDF9", linewidth=4, marker="o", markersize=10, zorder=10)
                ax.fill_between(dates, prices, color="#6BF1E2", alpha=0.16, zorder=5)
                ax.set_title("Aluminium Price - Last 15 Days", color="#E3F7FF", fontsize=20)
                ax.tick_params(axis='x', rotation=20, labelcolor="#B3FFF6")
                ax.tick_params(axis='y', labelcolor="#97F6C8")
                for spine in ax.spines.values():
                    spine.set_visible(False)
                ax.grid(True, linestyle="--", alpha=0.16)
                plt.tight_layout()
                canvas = FigureCanvasTkAgg(fig, master=frame)
                canvas.draw()
                canvas.get_tk_widget().pack()
                plt.close(fig)
            self.after(0, draw_chart)

        threading.Thread(target=fetch_and_plot, daemon=True).start()

    def fancy_button(self, text, command, side):
        btn = ctk.CTkButton(
            self.btns_frame,
            text=text,
            width=300,
            height=78,
            font=("Segoe UI", 23, "bold"),
            fg_color="#56D1B3",
            text_color="#152942",
            corner_radius=24,
            hover_color="#53F1FF",
            command=command
        )
        btn.pack(side=side, padx=46, pady=20)
        self.animated_glow(btn, 0)

        def on_enter(event):
            btn.configure(width=330, height=88, fg_color="#9DFEFF")
        def on_leave(event):
            btn.configure(width=300, height=78, fg_color="#56D1B3")
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

    def animated_glow(self, btn, i):
        colors = ["#A6E7FF", "#73F8FF", "#4FD7FF", "#B6FFF6", "#A6E7FF"]
        btn.configure(border_color=colors[i])
        self.after(650, lambda: self.animated_glow(btn, (i+1) % len(colors)))

class WelcomePage(ctk.CTkFrame):
    def __init__(self, master, user_info):
        super().__init__(master, fg_color="#0C1C2C")
        self.master = master
        ctk.CTkLabel(self, text=f"Hello {user_info['first_name']} 👋", font=("Helvetica", 32, "bold"), text_color="#8CE8FF").pack(pady=(40,12))
        ctk.CTkLabel(self, text="Welcome to your Pricing Powered IA Engine", font=("Arial", 20, "bold"), text_color="#8CE8FF").pack(pady=5)
        ctk.CTkLabel(self, text="This engine allows you to predict prices in real time with less than 0.5% error.", font=("Arial", 16), text_color="#D7E9F7").pack(pady=4)
        # Show time and aluminium price
        now_lbl = ctk.CTkLabel(self, text="", font=("Arial", 15), text_color="#F0D48A")
        now_lbl.pack(pady=3)
        price_lbl = ctk.CTkLabel(self, text="", font=("Arial", 15), text_color="#A8F0E2")
        price_lbl.pack(pady=3)
        self.update_time_and_price(now_lbl, price_lbl)
        # Big green buttons
        ctk.CTkButton(self, text="Use Our Model", font=("Arial", 20, "bold"), fg_color="#62EDC5", text_color="#112232", height=70, corner_radius=25, command=lambda:self.master.show_dashboard("Prediction")).pack(pady=(45,20), ipadx=60)
        ctk.CTkButton(self, text="Train Your Own Model", font=("Arial", 20, "bold"), fg_color="#62EDC5", text_color="#112232", height=70, corner_radius=25, command=lambda:self.master.show_dashboard("IA_Model")).pack(ipadx=45)
    def update_time_and_price(self, now_lbl, price_lbl):
        now_lbl.configure(text="Time now: "+datetime.now().strftime("%A %d %B %Y | %H:%M:%S"))
        price_lbl.configure(text=f"Aluminium price now: {get_aluminium_price()} €/kg")
        self.after(60000, lambda:self.update_time_and_price(now_lbl, price_lbl))




class Dashboard(ctk.CTkFrame):


    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()


    def should_show_buttons(self, csv_path):
        if not os.path.exists(csv_path):
            return True
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("Version", "").startswith("Version_") and row.get("Version", "") != "Version_0":
                    return False
        return True  # only Version_0 present (or file empty)

    def __init__(self, master, user_info, start_page, show_buttons=True):
        super().__init__(master, fg_color="#0C1C2C")
        self.master = master
        self.user_info = user_info
        self.current_page = None
        self.nav = None

        # Grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- SIDEBAR (with user info & nav) ---
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="#153242")
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar.grid_rowconfigure(8, weight=1)

        # Logo and title
        ctk.CTkLabel(
            self.sidebar, text="DASHBOARD",
            font=ctk.CTkFont(family="Helvetica", size=20, weight="bold"),
            text_color="#153242"
        ).grid(row=0, column=0, padx=20, pady=(20, 10))

        # User info area
        user_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        user_frame.grid(row=1, column=0, padx=20, pady=20)

        # Avatar
        avatar_canvas = tk.Canvas(user_frame, width=80, height=80, bg="#153242", highlightthickness=0)
        avatar_canvas.pack()
        self.draw_avatar(avatar_canvas)



        ctk.CTkLabel(
        user_frame, 
        text=f"{user_info['first_name']}",
        font=ctk.CTkFont(size=16, weight="bold"),
        text_color="#E0E3E6"  # Same as sidebar, now invisible
        ).pack(pady=(10, 0))

        ctk.CTkLabel(
            self.sidebar, text="DASHBOARD",
            font=ctk.CTkFont(family="Helvetica", size=20, weight="bold"),
            text_color="#419CCE"
        ).grid(row=0, column=0, padx=20, pady=(20, 10))

        ctk.CTkLabel(
            user_frame,
            text=user_info['first_name'],
            text_color="#153242"  # Same as sidebar, now invisible
        ).pack(pady=(0, 15))

        # Navigation buttons (with icons for style)
        nav_items = [
            ("Home", "🏠 "),
            ("Prediction", "📈"),
            ("IA_Model", "🤖  "),
            ("Statistics", "📊 "),
            ("Versions", "📁"),
        ]
        self.nav_buttons = []
        for idx, (label, icon) in enumerate(nav_items):
            b = ctk.CTkButton(
                self.sidebar,
                text=f"{icon}{label}",
                font=ctk.CTkFont(size=15),
                anchor="center",       # <-- CENTRÉ !
                fg_color="transparent",
                hover_color="#1E4D8C" if label == start_page else "#2A5D9F",
                height=45,
                width=180,             # <-- largeur fixe pour forcer le centrage, ajuste si tu veux
                corner_radius=18,
                command=lambda p=label: self.show_page(p)
            )
            b.grid(row=idx+2, column=0, padx=10, pady=5, sticky="ew")
            self.nav_buttons.append((b, label))

        # Logout button
        ctk.CTkButton(
            self.sidebar,
            text="Logout",
            fg_color="#1E4D8C",
            hover_color="#2A5D9F",
            height=40,
            corner_radius=8,
            command=master.logout
        ).grid(row=8, column=0, padx=10, pady=20, sticky="s")

        # --- MAIN CONTENT AREA ---
        self.content = ctk.CTkFrame(self, fg_color="#0C1C2C")
        self.content.grid(row=0, column=1, sticky="nsew")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.show_page(start_page)



    def draw_avatar(self, canvas):
        w, h = 80, 80
        # Head
        canvas.create_oval(10, 10, 70, 70, fill="#153242", outline="")
        # Eyes
        canvas.create_oval(25, 30, 35, 40, fill="#153242", outline="")
        canvas.create_oval(45, 30, 55, 40,fill="#153242", outline="")
        # Smile
        


    def show_page(self, page):
        # Remove current page if exists
        if self.current_page:
            self.current_page.destroy()
        # Update nav hover effect
        for b, p in self.nav_buttons:
            b.configure(hover_color="#1E4D8C" if p == page else "#2A5D9F")
        u = self.user_info
        upath = f"Odens/Global_engin/{u['username']}_{u['password']}"
        eval_csv = os.path.join(upath, "IA_Models", "evaluations.csv")
        # Home/Prediction/IA_Model/Statistics/Versions logic as before
        if page == "Home":
            show_buttons = self.should_show_buttons(eval_csv)
            self.current_page = HomePage(
                self.content,
                self.user_info,
                on_use_model=lambda: self.show_page("Prediction"),
                on_train_model=lambda: self.show_page("IA_Model"),
                show_buttons=show_buttons
            )
        elif page == "Prediction":
            self.current_page = PredictionPage(self.content, csv_path=eval_csv, output_folder=os.path.join(upath, "DATA_2"))
        elif page == "IA_Model":
            self.current_page = TrainPage(
                self.content,
                path1=os.path.join(upath, "DATA_1"),
                path2=os.path.join(upath, "TEMP"),
                path3=os.path.join(upath, "IA_Models"),
                path4=os.path.join(upath, "DATA_2"),
            )
        elif page == "Statistics":
            self.current_page = StatisticsPage(self.content, csv_path=eval_csv, page_color="#192233")
        elif page == "Versions":
            self.current_page = VersionsPage(self.content, csv_path=eval_csv)
        else:
            show_buttons = self.should_show_buttons(eval_csv)

            self.current_page = HomePage(
                self.content,
                self.user_info,
                on_use_model=lambda: self.show_page("Prediction"),
                on_train_model=lambda: self.show_page("IA_Model"),
                show_buttons=show_buttons
            )
        self.current_page.pack(fill="both", expand=True)

    def should_show_buttons(self, csv_path):
        if not os.path.exists(csv_path):
            return True
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # check for any Version_N where N >= 1
                if row.get("Version", "").startswith("Version_") and row.get("Version", "") != "Version_0":
                    return False
        return True  # only Version_0 present (or file empty)

# --- LOGIN PAGE ---
class LoginFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="#0C1C2C")
        self.master = master
        self.login_panel = ctk.CTkFrame(self, width=420, height=430, fg_color="#0F1928", corner_radius=16)
        self.login_panel.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(self.login_panel, text="LOGIN", font=("Helvetica", 28, "bold"), text_color="#4AB5FF").pack(pady=(28,10))
        self.username_entry = ctk.CTkEntry(self.login_panel, width=320, height=38, placeholder_text="Username")
        self.username_entry.pack(pady=10)
        self.password_entry = ctk.CTkEntry(self.login_panel, width=320, height=38, placeholder_text="Password", show="•")
        self.password_entry.pack(pady=10)
        self.status = ctk.CTkLabel(self.login_panel, text="", text_color="#FF5555")
        self.status.pack(pady=5)
        ctk.CTkButton(self.login_panel, text="Login", width=320, height=38, fg_color="#1E4D8C", hover_color="#2A5D9F", command=self.login_action).pack(pady=(16,4))
        ctk.CTkLabel(self.login_panel, text="Don't have an account?", text_color="#9DB9D9").pack(pady=(10,0))
        ctk.CTkButton(self.login_panel, text="Sign up", fg_color="transparent", text_color="#4AB5FF", command=master.show_signup_page).pack()
        ctk.CTkLabel(
            self,
            text="designed by Odens 2025",
            font=("Segoe UI", 13, "bold"),
            text_color="#40D9FF"
        ).pack(side="bottom", pady=(0, 10))

    def login_action(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            self.status.configure(text="Please enter both fields!", text_color="#FF5555")
            return
        user_folder = f"Odens/Global_engin/{username}_{password}"
        if not os.path.exists(user_folder):
            self.status.configure(text="Account not found.", text_color="#FF5555")
            return
        # Load info
        with open(os.path.join(user_folder, "user_info.csv"), "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            info = next(reader)
        is_first = info.get("first_login", "yes") == "yes"
        # Mark as not first after login
        info["first_login"] = "no"
        with open(os.path.join(user_folder, "user_info.csv"), "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=info.keys())
            writer.writeheader()
            writer.writerow(info)
        self.master.after_login(info, is_first)

# --- SIGNUP PAGE ---
class SignupFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="#0C1C2C")
        self.master = master
        self.signup_panel = ctk.CTkFrame(self, width=440, height=540, fg_color="#0F1928", corner_radius=16)
        self.signup_panel.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(self.signup_panel, text="CREATE ACCOUNT", font=("Helvetica", 25, "bold"), text_color="#4AB5FF").pack(pady=(22,12))
        self.firstname = ctk.CTkEntry(self.signup_panel, width=330, height=34, placeholder_text="First Name")
        self.firstname.pack(pady=6)
        self.lastname = ctk.CTkEntry(self.signup_panel, width=330, height=34, placeholder_text="Last Name")
        self.lastname.pack(pady=6)
        self.username = ctk.CTkEntry(self.signup_panel, width=330, height=34, placeholder_text="Username")
        self.username.pack(pady=6)
        self.password = ctk.CTkEntry(self.signup_panel, width=330, height=34, placeholder_text="Password", show="•")
        self.password.pack(pady=6)
        self.confirmpw = ctk.CTkEntry(self.signup_panel, width=330, height=34, placeholder_text="Confirm Password", show="•")
        self.confirmpw.pack(pady=6)
        # Password strength
        self.strength_label = ctk.CTkLabel(self.signup_panel, text="", font=("Arial", 13, "bold"))
        self.strength_label.pack()
        self.password.bind("<KeyRelease>", self.check_strength)
        self.status = ctk.CTkLabel(self.signup_panel, text="", text_color="#FF5555")
        self.status.pack(pady=5)
        ctk.CTkButton(self.signup_panel, text="Sign Up", width=330, height=38, fg_color="#1E4D8C", hover_color="#2A5D9F", command=self.signup_action).pack(pady=(16,4))
        ctk.CTkButton(self.signup_panel, text="Back to Login", fg_color="transparent", text_color="#4AB5FF", command=master.show_login_page).pack()

    def check_strength(self, event=None):
        pw = self.password.get()
        if len(pw) < 6:
            self.strength_label.configure(text="Password too short", text_color="#FF5555")
        elif len(pw) < 10:
            self.strength_label.configure(text="Weak password", text_color="#FFA500")
        elif any(c.isdigit() for c in pw) and any(c.isupper() for c in pw) and any(c in "!@#$%^&*()" for c in pw):
            self.strength_label.configure(text="Strong password", text_color="#3AB2FF")
        else:
            self.strength_label.configure(text="Medium password", text_color="#36D399")

    def signup_action(self):
        fn, ln, un, pw, cpw = self.firstname.get(), self.lastname.get(), self.username.get(), self.password.get(), self.confirmpw.get()
        if not (fn and ln and un and pw and cpw):
            self.status.configure(text="Please fill all fields.", text_color="#FF5555")
            return
        if len(pw) < 6:
            self.status.configure(text="Password must be at least 6 characters!", text_color="#FF5555")
            return
        if pw != cpw:
            self.status.configure(text="Passwords do not match!", text_color="#FF5555")
            return
        # Create user folder & files
        user_folder = f"Odens/Global_engin/{un}_{pw}"
        if os.path.exists(user_folder):
            self.status.configure(text="User already exists!", text_color="#FF5555")
            return
        os.makedirs(user_folder)
        for sub in ["DATA_1", "DATA_2", "TEMP", "IA_Models"]:
            os.makedirs(os.path.join(user_folder, sub))
        # Copy evaluations.csv
        src = "Odens/IA_training/evaluations.csv"
        dst = os.path.join(user_folder, "IA_Models", "evaluations.csv")
        try:
            from shutil import copy2
            copy2(src, dst)
        except Exception:
            pass
        # Save user info
        with open(os.path.join(user_folder, "user_info.csv"), "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["first_name","last_name","username","password","first_login"])
            writer.writeheader()
            writer.writerow({"first_name":fn, "last_name":ln, "username":un, "password":pw, "first_login":"yes"})
        tk.messagebox.showinfo("Success", "Account created! Please login.")
        self.master.show_login_page()

# --- MAIN APP ---
class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("IA Pricing Engine")
        self.geometry("1200x820")
        self.resizable(True, True)
        self.configure(fg_color="#0C1C2C")
        self.user_info = None
        self.sidebar = None
        self.current_frame = None
        self.show_login_page()

    def show_login_page(self):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = LoginFrame(self)
        self.current_frame.pack(fill="both", expand=True)

    def show_signup_page(self):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = SignupFrame(self)
        self.current_frame.pack(fill="both", expand=True)

    def after_login(self, user_info, is_first_time):
        self.user_info = user_info
        # Always check version count after login
        upath = f"Odens/Global_engin/{user_info['username']}_{user_info['password']}/IA_Models/evaluations.csv"
        show_buttons = self.should_show_buttons(upath)
        self.show_dashboard("Home", show_buttons=show_buttons)

    def show_dashboard(self, page, show_buttons=True):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = Dashboard(self, self.user_info, page, show_buttons=show_buttons)
        self.current_frame.pack(fill="both", expand=True)

    def should_show_buttons(self, csv_path):
        if not os.path.exists(csv_path):
            return True
        with open(csv_path, "r", encoding="utf-8") as f:
            lines = [l for l in f.readlines() if l.strip()]
            # If only Version_0 (1 data + 1 header), show buttons
            if len(lines) <= 2:
                return True
            # If multiple versions (header + >1 line), hide buttons
            return False

    def logout(self):
        self.user_info = None
        self.show_login_page()

# --- DASHBOARD ---

# --- RUN APP ---
if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    app = MainApp()
    app.mainloop()
