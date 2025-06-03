import os
import csv
import customtkinter as ctk
from tkinter import messagebox

class VersionsPage(ctk.CTkFrame):
    def __init__(self, master, csv_path, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.csv_path = csv_path
        self.selected_idx = None
        self.rows = []
        self.header = []

        self.bgcolor = "#192233"
        self.selected_color = "#223A51"

        self.configure(fg_color=self.bgcolor)
        self.grid_columnconfigure(0, weight=1)

        # Title
        title_frame = ctk.CTkFrame(self, fg_color="#0F1928", corner_radius=25, height=80)
        title_frame.grid(row=0, column=0, pady=(24, 8), padx=32, sticky="ew")
        title_label = ctk.CTkLabel(title_frame, text="Versions", font=("Helvetica", 38, "bold"), text_color="#A8F0E2")
        title_label.pack(pady=16)

        # Table frame
        self.table_frame = ctk.CTkScrollableFrame(self, fg_color="#243148", width=1120, height=500, corner_radius=16)
        self.table_frame.grid(row=1, column=0, pady=(8, 16), padx=40, sticky="ew")

        # Info label + Buttons
        self.info_label = ctk.CTkLabel(self, text="Select a version to promote or delete.", font=("Arial", 16), text_color="#A8F0E2")
        self.info_label.grid(row=2, column=0, pady=(0, 4))

        # Button frame (horizontal)
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=3, column=0, pady=8)
        self.select_btn = ctk.CTkButton(btn_frame, text="Promote Selected Version", command=self.promote_selected, fg_color="#62EDC5", text_color="#112232", font=("Arial", 18, "bold"))
        self.select_btn.grid(row=0, column=0, padx=6)
        self.delete_btn = ctk.CTkButton(btn_frame, text="Delete Selected Version", command=self.delete_selected, fg_color="#FF5252", text_color="#FFFFFF", font=("Arial", 18, "bold"))
        self.delete_btn.grid(row=0, column=1, padx=6)
        self.select_btn.configure(state="disabled")
        self.delete_btn.configure(state="disabled")

        self.load_csv_and_draw_table()

    def load_csv_and_draw_table(self):
        # Clear previous widgets
        for widget in self.table_frame.winfo_children():
            widget.destroy()
        # Read CSV
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = list(csv.reader(f))
        self.header = reader[0]
        self.rows = reader[1:]

        # 1️⃣ Trouver l'index de la colonne 'path'
        if "path" in self.header:
            path_idx = self.header.index("path")
        else:
            path_idx = -1

        # 2️⃣ Afficher le header sans 'path'
        col = 0
        for j, h in enumerate(self.header):
            if j == path_idx:
                continue  # Skip path column
            ctk.CTkLabel(
                self.table_frame,
                text=h,
                font=("Arial", 15, "bold"),
                text_color="#FFFFFF",
                fg_color=self.bgcolor,
                width=160
            ).grid(row=0, column=col, padx=2, pady=2, sticky="nsew")
            col += 1

        # 3️⃣ Afficher les lignes sans la colonne 'path'
        self.row_labels = []
        for i, row in enumerate(self.rows):
            row_widgets = []
            col = 0
            for j, cell in enumerate(row):
                if j == path_idx:
                    continue  # Skip path column
                lbl = ctk.CTkLabel(
                    self.table_frame,
                    text=cell,
                    font=("Arial", 14),
                    text_color="#A8F0E2",
                    fg_color=self.bgcolor,
                    width=160
                )
                lbl.grid(row=i+1, column=col, padx=2, pady=2, sticky="nsew")
                row_widgets.append(lbl)
                col += 1
            # Bind selection event
            for lbl in row_widgets:
                lbl.bind("<Button-1>", lambda e, idx=i: self.on_row_select(idx))
            self.row_labels.append(row_widgets)

    def on_row_select(self, idx):
        # Highlight selected row
        for i, widgets in enumerate(self.row_labels):
            color = self.selected_color if i == idx else self.bgcolor
            for lbl in widgets:
                lbl.configure(fg_color=color)
        self.selected_idx = idx
        self.select_btn.configure(state="normal")
        self.delete_btn.configure(state="normal")
        self.info_label.configure(text=f"Selected: {self.rows[idx][0]}", text_color="#112232")

    def promote_selected(self):
        if self.selected_idx is None:
            self.info_label.configure(text="No version selected.", text_color="#8A9092")
            return
        # Move selected row to top (after header)
        selected_row = self.rows.pop(self.selected_idx)
        self.rows.insert(0, selected_row)
        # Save to CSV
        with open(self.csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(self.header)
            writer.writerows(self.rows)
        self.info_label.configure(text=f"Promoted {selected_row[0]} to top!", text_color="#A8F0E2")
        self.select_btn.configure(state="disabled")
        self.delete_btn.configure(state="disabled")
        # Redraw table
        self.load_csv_and_draw_table()
        self.selected_idx = None

    def delete_selected(self):
        if self.selected_idx is None:
            self.info_label.configure(text="No version selected.", text_color="#8A9092")
            return
        # Confirm dialog
        res = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete version: {self.rows[self.selected_idx][0]}?")
        if not res:
            return
        deleted_row = self.rows.pop(self.selected_idx)
        with open(self.csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(self.header)
            writer.writerows(self.rows)
        self.info_label.configure(text=f"Deleted {deleted_row[0]}.", text_color="#FF5252")
        self.select_btn.configure(state="disabled")
        self.delete_btn.configure(state="disabled")
        self.load_csv_and_draw_table()
        self.selected_idx = None


# --- TEST SOLO ---
if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    root = ctk.CTk()
    root.title("Versions Page Demo")
    root.geometry("1200x800")
    csv_path = "Odens/IA_training/evaluations.csv"
    page = VersionsPage(root, csv_path=csv_path)
    page.pack(fill="both", expand=True)
    root.mainloop()
