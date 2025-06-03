import os
import csv
import json
import joblib
import numpy as np
import uuid
import math
import re
import yfinance as yf
from datetime import datetime
import customtkinter as ctk


DENSITY_ALU = 2700
TOLERANCE_MAPPING = {
    "EN 755-9": {"linear_tol": 0.15, "angular_tol": 0.5, "flatness": 0.2, "gd_t_index": 2.1},
    "ISO 2768-m": {"linear_tol": 0.1, "angular_tol": 0.3, "flatness": 0.15, "gd_t_index": 2.8},
    "ASME Y14.5": {"linear_tol": 0.05, "angular_tol": 0.2, "flatness": 0.1, "gd_t_index": 3.5},
    "DIN 7168": {"linear_tol": 0.08, "angular_tol": 0.25, "flatness": 0.12, "gd_t_index": 3.0},
    "ISO 286": {"linear_tol": 0.06, "angular_tol": 0.22, "flatness": 0.08, "gd_t_index": 3.2},
    "JIS B 0401": {"linear_tol": 0.07, "angular_tol": 0.28, "flatness": 0.11, "gd_t_index": 2.9},
    "ISO 8015": {"linear_tol": 0.04, "angular_tol": 0.18, "flatness": 0.07, "gd_t_index": 3.6},
    "ASME B4.1": {"linear_tol": 0.12, "angular_tol": 0.35, "flatness": 0.18, "gd_t_index": 2.5},
    "BS 4500": {"linear_tol": 0.11, "angular_tol": 0.33, "flatness": 0.16, "gd_t_index": 2.6},
    "ISO 1829": {"linear_tol": 0.13, "angular_tol": 0.4, "flatness": 0.19, "gd_t_index": 2.4},
    "DEFAULT": {"linear_tol": 0.3, "angular_tol": 1.0, "flatness": 0.5, "gd_t_index": 1.0}
}
ALLOY_CATEGORIES = [
    "Aluminium 1050 Rå", "Aluminium 2017 T4", "Aluminium 3003 H14",
    "Aluminium 4043 O", "Aluminium 5083 H111", "Aluminium 6061 T6",
    "Aluminium 7075 T651", "Aluminium 2024 T351", "Rå"
]

def parse_ytbehandling(text):
    result = {"alloy_series": None, "alloy_strength": None, "temper_code": None, "european_std": 0}
    if "EN-AW" in text:
        result["european_std"] = 1
    if "606" in text:
        result["alloy_series"] = 6
        result["alloy_strength"] = 63
    match = re.search(r"T(\d)", text)
    if match:
        result["temper_code"] = int(match.group(1))
    return result

def calculate_geometric_features(weight_kg_per_m, length_m):
    area_mm2 = (weight_kg_per_m / DENSITY_ALU) * 1e6
    height = math.sqrt(area_mm2 * 2)
    width = area_mm2 / height
    perimeter = 2 * (height + width)
    return {
        "thinness_ratio": round((4 * math.pi * area_mm2) / (perimeter ** 2), 4),
        "area_to_length": round(area_mm2 / (length_m * 1000), 5),
        "wall_factor": round(area_mm2 / perimeter, 4),
        "dfm_index": round(min(1.0, 0.7 / (weight_kg_per_m ** 0.25)), 4),
        "symmetry_score": 0.8
    }

def get_today_aluminium_price():
    try:
        data = yf.download("ALI=F", period="5d")['Close'].dropna()
        eur_kg = 0.93 / 1000
        nordic_premium = 1.0
        today_val = float(data.iloc[-1])
        today_val = round(today_val * eur_kg + nordic_premium, 2)
        today_date = data.index[-1].strftime("%d/%m/%Y")
        return today_val, today_date
    except Exception:
        return "N/A", "N/A"

def average_from_input(text):
    parts = re.findall(r"\d+(?:\.\d+)?", text)
    numbers = list(map(float, parts))
    return round(sum(numbers) / len(numbers), 2) if numbers else 0

class PredictionPage(ctk.CTkFrame):
    def __init__(self, master, csv_path, output_folder, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.csv_path = csv_path
        self.output_folder = output_folder

        # Style
        self.configure(fg_color="#192233")
        self.grid_columnconfigure(0, weight=1)

        # Title (Big, Rounded)
        title_frame = ctk.CTkFrame(self, fg_color="#0F1928", corner_radius=25, height=80)
        title_frame.grid(row=0, column=0, pady=(24, 16), padx=32, sticky="ew")
        title_label = ctk.CTkLabel(title_frame, text="Aluminium Pricing Prediction Engine", font=("Helvetica", 38, "bold"), text_color="#A8F0E2")
        title_label.pack(pady=16)

        # Info Frame (Date+Time left, Price right)
        info_frame = ctk.CTkFrame(self, fg_color="#243148", corner_radius=16)
        info_frame.grid(row=1, column=0, padx=32, pady=(0, 16), sticky="ew")
        info_frame.grid_columnconfigure(0, weight=1)
        info_frame.grid_columnconfigure(1, weight=1)
        self.time_label = ctk.CTkLabel(info_frame, text="", font=("Arial", 17), text_color="#A8F0E2")
        self.time_label.grid(row=0, column=0, padx=20, pady=8, sticky="w")
        self.price_label = ctk.CTkLabel(info_frame, text="", font=("Arial", 17, "bold"), text_color="#A8F0E2")
        self.price_label.grid(row=0, column=1, padx=20, pady=8, sticky="e")
        self.update_time_and_price()

        # Main input Frame (as in your screenshot)
        main_frame = ctk.CTkFrame(self, fg_color="#21304C", corner_radius=18)
        main_frame.grid(row=2, column=0, padx=48, pady=6, sticky="ew")

        # Entries & dropdowns
        labels_examples = [
            ("Weight (kg/m)", "Vikt_kg_m", "1.342"),
            ("Length (m)", "Längd_m_m", "23.8"),
            ("Tooling Price", "Kap_truml_Pris_st", "0.78"),
            ("Annual Volume", "Årsvolym_st", "42000"),
            ("Tool Cost", "Verktygskostnad", "14500"),
            ("Min. Quantity (NOT)", "NOT", "15000"),
            ("First delivery weeks (e.g. 8–10)", "first_deliv", "8-10"),
            ("Continued delivery weeks (e.g. 5–6)", "cont_deliv", "5-6"),
            ("Ytbehandling", "ytb", "EN-AW-6063-T5"),
        ]
        self.entries = {}
        for i, (label, key, example) in enumerate(labels_examples):
            l = ctk.CTkLabel(main_frame, text=label + " :", font=("Arial", 16), anchor="w", text_color="#D7E9F7")
            l.grid(row=i, column=0, sticky="w", padx=14, pady=6)
            ent = ctk.CTkEntry(main_frame, width=280, font=("Arial", 16), fg_color="#324268", corner_radius=12, placeholder_text=example)
            ent.grid(row=i, column=1, padx=14, pady=6)
            self.entries[key] = ent


        # Tolerance dropdown
        tol_label = ctk.CTkLabel(main_frame, text="Tolerance :", font=("Arial", 16), anchor="w", text_color="#D7E9F7")
        tol_label.grid(row=len(labels_examples), column=0, sticky="w", padx=14, pady=6)
        self.tol_dropdown = ctk.CTkOptionMenu(main_frame, values=list(TOLERANCE_MAPPING.keys()), font=("Arial", 15), fg_color="#415AA2", width=280)
        self.tol_dropdown.set("EN 755-9")
        self.tol_dropdown.grid(row=len(labels_examples), column=1, padx=14, pady=6)

        # Alloy dropdown
        alloy_label = ctk.CTkLabel(main_frame, text="Alloy Category :", font=("Arial", 16), anchor="w", text_color="#D7E9F7")
        alloy_label.grid(row=len(labels_examples)+1, column=0, sticky="w", padx=14, pady=6)
        self.alloy_dropdown = ctk.CTkOptionMenu(main_frame, values=ALLOY_CATEGORIES, font=("Arial", 15), fg_color="#415AA2", width=280)
        self.alloy_dropdown.set(ALLOY_CATEGORIES[0])
        self.alloy_dropdown.grid(row=len(labels_examples)+1, column=1, padx=14, pady=6)

        # Predict button
        self.pred_btn = ctk.CTkButton(
            self, text="Predict", font=("Arial", 20, "bold"), fg_color="#62EDC5", text_color="#112232",
            hover_color="#36D399", corner_radius=30, height=60, command=self.predict_action
        )
        self.pred_btn.grid(row=3, column=0, pady=22, padx=150, sticky="ew")

        # Result Frame
        result_frame = ctk.CTkFrame(self, fg_color="#243148", corner_radius=16, height=100)
        result_frame.grid(row=4, column=0, padx=32, pady=(16, 28), sticky="ew")
        self.result_label = ctk.CTkLabel(result_frame, text="", font=("Arial", 22, "bold"), text_color="#F0D48A", anchor="center")
        self.result_label.pack(pady=12)

        # Animation: blinking border on Predict button
        self.blinking = True
        self.animate_button()

    def update_time_and_price(self):
        now = datetime.now().strftime("%A %d %B %Y | %H:%M:%S")
        today_price, today_date = get_today_aluminium_price()
        price_str = f"Today Aluminium: {today_price} €/kg  ({today_date})"
        self.price_label.configure(text=price_str)
        self.time_label.configure(text="Time now: " + now)
        self.after(1000, self.update_time_and_price)  # Update every second

    def animate_button(self):
        if self.blinking:
            color = "#62EDC5" if datetime.now().second % 2 == 0 else "#36D399"
            self.pred_btn.configure(border_width=3, border_color=color)
            self.after(400, self.animate_button)

    def get_model_path(self):
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)
            first_data = next(reader)
            model_base_path = first_data[1]
        return model_base_path
#____

    def predict_action(self):
        try:
            data = {
                "Vikt_kg_m": float(self.entries["Vikt_kg_m"].get()),
                "Längd_m_m": float(self.entries["Längd_m_m"].get()),
                "Kap_truml_Pris_st": float(self.entries["Kap_truml_Pris_st"].get()),
                "Årsvolym_st": float(self.entries["Årsvolym_st"].get()),
                "Verktygskostnad": float(self.entries["Verktygskostnad"].get()),
                "NOT": float(self.entries["NOT"].get())
            }
        except ValueError:
            self.result_label.configure(text="Please fill all numeric fields correctly.")
            return

        first_deliv = self.entries["first_deliv"].get()
        cont_deliv = self.entries["cont_deliv"].get()
        if not first_deliv or not cont_deliv:
            self.result_label.configure(text="Enter delivery weeks!")
            return
        a = average_from_input(first_deliv)
        b = average_from_input(cont_deliv)
        data["Lev_tid"] = round((a + b) / 2, 2)

        # LME and Tolerance
        try:
            today_price, _ = get_today_aluminium_price()
            data["Råvara"] = today_price if isinstance(today_price, (float, int)) else 1.0
        except:
            data["Råvara"] = 1.0
        tol = self.tol_dropdown.get()
        data.update(TOLERANCE_MAPPING.get(tol, TOLERANCE_MAPPING["DEFAULT"]))

        # Ytbehandling
        ytb = self.entries["ytb"].get()
        data.update(parse_ytbehandling(ytb))
        data.update(calculate_geometric_features(data["Vikt_kg_m"], data["Längd_m_m"]))

        # Alloy
        alloy_idx = self.alloy_dropdown.cget("values").index(self.alloy_dropdown.get())
        data["alloy_category"] = alloy_idx

        # 2. Get model/scaler
        model_dir = self.get_model_path()
        try:
            model = joblib.load(os.path.join(model_dir, "ensemble_model.pkl"))
            scaler = joblib.load(os.path.join(model_dir, "scaler.pkl"))
        except Exception as e:
            self.result_label.configure(text=f"Model loading error: {e}")
            return

        feature_order = [
            "Längd_m_m", "NOT", "Årsvolym_st", "Verktygskostnad",
            "Vikt_kg_m", "dfm_index", "area_to_length", "Råvara", "Lev_tid"
        ]
        try:
            input_array = np.array([[data.get(key, 0) for key in feature_order]])
            input_scaled = scaler.transform(input_array)
            predicted_price = model.predict(input_scaled)[0]
        except Exception as e:
            self.result_label.configure(text=f"Prediction error: {e}")
            return

        data["Pris_kr_st_SEK"] = round(predicted_price, 2)
        self.result_label.configure(text=f"Predicted Price: {data['Pris_kr_st_SEK']} SEK/unit")

        # 3. Save to JSON
        os.makedirs(self.output_folder, exist_ok=True)
        output_filename = f"prediction_{uuid.uuid4().hex[:8]}.json"
        output_path = os.path.join(self.output_folder, output_filename)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

# --- EXEMPLE POUR TESTER SEUL ---
if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    root = ctk.CTk()
    root.title("Prediction Engine Demo")
    root.geometry("1200x820")
    page = PredictionPage(root, csv_path="Odens/IA_training/evaluations.csv", output_folder="Odens/IA_training/predictions_output")
    page.pack(fill="both", expand=True)
    root.mainloop()
