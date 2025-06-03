import os
import csv
import re
import shutil
import threading
import time
import customtkinter as ctk
from tkinter import filedialog
import sys
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

matplotlib.use("Agg")

import os
import sys

def absolute_path(*args):
    """Always return an absolute normalized path, cross-platform."""
    return os.path.abspath(os.path.join(*args))

# Set up paths
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
ia_training_dir = os.path.join(parent_dir, "IA_training")

# Add parent and IA_training directories to sys.path if not already present
for path in [parent_dir, ia_training_dir]:
    if path not in sys.path:
        sys.path.append(path)

# Import your Model_Training class or function
from IA_training.IA_Model import Model_Training  # If IA_Model.py is in IA_training

# Usage example (if needed)
# model = Model_Training()


# --- CIRCULAR PROGRESS WIDGET ---
class CircularProgress(ctk.CTkCanvas):
    def __init__(self, master, size=100, width=10, fg="#62EDC5", bg="#243148", **kwargs):
        super().__init__(master, width=size, height=size, bg=bg, highlightthickness=0, **kwargs)
        self.size = size
        self.width = width
        self.fg = fg
        self.bgcolor = bg
        self.arc = None
        self.label = self.create_text(size//2, size//2, text="", fill="#B7FF8F", font=("Arial", 17, "bold"))
        self.progress = 0

    def set(self, percent):
        self.progress = percent
        self.delete("arc")
        extent = percent * 359.9
        # Draw background circle
        self.create_oval(
            self.width//2, self.width//2,
            self.size-self.width//2, self.size-self.width//2,
            outline="#384963", width=self.width, tags="arc_bg"
        )
        # Draw progress arc
        self.arc = self.create_arc(
            self.width//2, self.width//2,
            self.size-self.width//2, self.size-self.width//2,
            start=90, extent=-extent, style="arc",
            outline=self.fg, width=self.width, tags="arc"
        )
        percent_txt = f"{int(percent*100)}%"
        self.itemconfig(self.label, text=percent_txt)

    def reset(self):
        self.set(0)

# --- CSV/REPORT UTILS ---
def parse_training_report(report_path):
    metrics = {
        "R² Score": "",
        "MAPE": "",
        "MAE": "",
        "RMSE": "",
        "Max Error": "",
        "Total Training Time": ""
    }
    with open(report_path, "r", encoding="utf-8") as f:
        for line in f:
            for key in metrics:
                if key in line:
                    metrics[key] = line.split(":")[1].strip().replace("%", "")
    return metrics

def get_next_version(csv_path):
    if not os.path.exists(csv_path):
        return 0
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)
        versions = [int(re.findall(r"\d+", row[0])[0]) for row in reader if "Version_" in row[0]]
        if not versions:
            return 0
        return max(versions) + 1

def insert_new_version_row(csv_path, new_row):
    rows = []
    if os.path.exists(csv_path):
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = list(csv.reader(f))
        rows = reader[1:]  # skip header
        header = reader[0]
    else:
        header = ["Version", "path", "R² Score", "MAPE", "MAE", "RMSE", "Max Error", "Total Training Time"]
    with open(csv_path, "w", encoding="utf-8", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerow(new_row)
        writer.writerows(rows)

# --- TRAIN PAGE ---
class TrainPage(ctk.CTkFrame ):
    def __init__(self, master, path1, path2, path3, path4, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.path1 = path1
        self.path2 = path2
        self.path3 = path3
        self.path4 = path4

        self.configure(fg_color="#192233")
        self.grid_columnconfigure(0, weight=1)

        # Title
        title_frame = ctk.CTkFrame(self, fg_color="#0F1928", corner_radius=25, height=80)
        title_frame.grid(row=0, column=0, pady=(24, 16), padx=32, sticky="ew")
        title_label = ctk.CTkLabel(title_frame, text="Train Your Model", font=("Helvetica", 38, "bold"), text_color="#A8F0E2")
        title_label.pack(pady=16)

        # File drop/select box
        self.file_box = ctk.CTkFrame(self, fg_color="#243148", corner_radius=20, height=110)
        self.file_box.grid(row=1, column=0, padx=80, pady=(0, 18), sticky="ew")
        self.file_box.grid_columnconfigure(0, weight=1)
        drop_label = ctk.CTkLabel(self.file_box, text="Drop or select your PDF files here", font=("Arial", 20), text_color="#A8F0E2")
        drop_label.pack(pady=16)
        select_btn = ctk.CTkButton(self.file_box, text="Select PDF(s)", font=("Arial", 16), fg_color="#415AA2", command=self.select_files)
        select_btn.pack()
        self.selected_files_label = ctk.CTkLabel(self.file_box, text="", font=("Arial", 14), text_color="#F0D48A", wraplength=900, anchor="w", justify="left")
        self.selected_files_label.pack(pady=4)
        self.pdf_files = []

        # Progress Circle (hidden initially)
        self.progress_circle = CircularProgress(self, size=100, fg="#B7FF8F")
        self.progress_circle.grid(row=2, column=0, pady=(0,10))
        self.progress_circle.grid_remove()

        # Train button
        self.train_btn = ctk.CTkButton(self, text="Start Training", font=("Arial", 22, "bold"), fg_color="#62EDC5", text_color="#112232",
            hover_color="#36D399", corner_radius=36, height=64, command=self.train_model)
        self.train_btn.grid(row=3, column=0, pady=26, padx=220, sticky="ew")

        # Progress and result
        self.progress_label = ctk.CTkLabel(self, text="", font=("Arial", 18, "bold"), text_color="#A8F0E2")  # Color same as "Train Your Model"
        self.progress_label.grid(row=4, column=0, pady=(10,10))

        # Placeholder for plot
        self.canvas_frame = ctk.CTkFrame(self, fg_color="#192233")
        self.canvas_frame.grid(row=5, column=0, pady=(0, 16))
        self.plot_canvas = None

    def select_files(self):
        files = filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])
        if files:
            self.pdf_files = files
            filenames = [os.path.basename(f) for f in files]
            if len(filenames) > 4:
                display = ", ".join(filenames[:3]) + f", ... (+{len(filenames)-3} more)"
            else:
                display = ", ".join(filenames)
            self.selected_files_label.configure(text=f"Selected: {display}")
        else:
            self.pdf_files = []
            self.selected_files_label.configure(text="")

    def save_pdfs(self):
        os.makedirs(self.path1, exist_ok=True)
        self.progress_circle.grid()
        total = len(self.pdf_files)
        for i, f in enumerate(self.pdf_files, 1):
            shutil.copy(f, self.path1)
            self.progress_circle.set(i / total)
            self.update_idletasks()
            time.sleep(0.11)  # Lent
        self.progress_circle.set(1.0)
        self.after(900, self.progress_circle.grid_remove)

    def train_model(self):
        if not self.pdf_files:
            self.progress_label.configure(text="Please select at least one PDF file.")
            return
        if self.plot_canvas:
            self.plot_canvas.get_tk_widget().destroy()
        thread = threading.Thread(target=self.background_training)
        thread.start()

    def background_training(self):
        self.progress_label.configure(text="")
        self.train_btn.configure(state="disabled")
        self.save_pdfs()
        self.progress_label.configure(text="Training in progress... Please wait ⏳")
        csv_path = os.path.join(self.path3, "evaluations.csv")
        N = get_next_version(csv_path)
        version_str = f"version_{N}"
        assets_path = os.path.join(self.path3, version_str)
        os.makedirs(assets_path, exist_ok=True)

        Model_Training(
            input_dir=self.path1,
            output_dir=self.path2,
            assets_path=assets_path,
            extra_json_folder=self.path4
        )

        report_path = os.path.join(assets_path, "IA_", "training_report.txt")
        metrics = parse_training_report(report_path)
        # R² as percent string, keep MAE and Max Error as float, MAPE is already in %
        try:
            r2_float = float(metrics["R² Score"])
            r2_disp = f"{r2_float * 100:.2f}%"  # Display as percent
        except Exception:
            r2_disp = metrics["R² Score"]

        new_row = [
            f"Version_{N}",
            os.path.join(self.path3, version_str, "IA_"),
            r2_disp, metrics["MAPE"], metrics["MAE"], metrics["RMSE"], metrics["Max Error"], metrics["Total Training Time"]
        ]
        insert_new_version_row(csv_path, new_row)
        self.progress_label.configure(
            text="✅ Training completed!\n"
                 f"R²: {r2_disp}, MAPE: {metrics['MAPE']}%, MAE: {metrics['MAE']}",
            text_color="#A8F0E2"
        )
        self.train_btn.configure(state="normal")
        self.show_plot(metrics)

    def show_plot(self, metrics):
        # Convert string metrics to float, R² as percent
        try:
            r2_float = float(metrics["R² Score"]) * 100  # percent
            mape = float(metrics["MAPE"])
            mae = float(metrics["MAE"])
            rmse = float(metrics["RMSE"])
            max_err = float(metrics["Max Error"])
            values = [r2_float, mape, mae, rmse, max_err]
            labels = ["R² (%)", "MAPE (%)", "MAE", "RMSE", "Max Error"]
        except Exception:
            return

        # White vertical bar plot, short, tight spacing
        fig, ax = plt.subplots(figsize=(7, 3.1), dpi=120, facecolor="#192233")
        fig.patch.set_alpha(1.0)
        fig.patch.set_facecolor("#192233")
        bars = ax.bar(
            labels,
            values,
            color="#FFFFFF",
            width=0.45,
            edgecolor="#FFFFFF",     # BORDERS WHITE
            linewidth=2.1
        )
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, fontsize=16, color='#FFFFFF', fontweight='bold')   # LABELS WHITE
        ax.set_yticks([])
        ax.set_facecolor('#192233')
        for spine in ax.spines.values():
            spine.set_visible(False)
        for bar, value in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width()/2,
                bar.get_height() + max(values)*0.025,
                f'{value:.2f}',
                ha='center',
                va='bottom',
                color='#FFFFFF',     # TEXT WHITE
                fontsize=13,
                fontweight='bold'
            )
        plt.tight_layout()

        # Clear old canvas if exists
        if self.plot_canvas:
            self.plot_canvas.get_tk_widget().destroy()
        self.plot_canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        self.plot_canvas.draw()
        widget = self.plot_canvas.get_tk_widget()
        widget.config(bg="#192233", highlightthickness=0, borderwidth=0)
        widget.pack(pady=10)
        plt.close(fig)

# --- EXEMPLE POUR TESTER SEUL ---
if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    root = ctk.CTk()
    root.title("Train Model Demo")
    root.geometry("1200x820")
    # Set your real project paths here:
    page = TrainPage(
        root,
        path1="DATA_1",                  # Where PDFs go
        path2="DATA_2",                  # Output for processed data
        path3="Odens/IA_training",       # Where evaluations.csv is and model versions will go
        path4="DATA_3"                   # Extra JSON folder
    )
    page.pack(fill="both", expand=True)
    root.mainloop()
