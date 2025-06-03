import os
import csv
from PIL import Image, ImageTk
import customtkinter as ctk

class StatisticsPage(ctk.CTkFrame):
    def __init__(self, master, csv_path, page_color="#192233", *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.csv_path = csv_path
        self.page_color = page_color

        self.configure(fg_color=page_color)
        self.grid_columnconfigure(0, weight=1)

        # Title
        title_frame = ctk.CTkFrame(self, fg_color="#0F1928", corner_radius=25, height=80)
        title_frame.grid(row=0, column=0, pady=(24, 8), padx=32, sticky="ew")
        title_label = ctk.CTkLabel(title_frame, text="Statistics", font=("Helvetica", 38, "bold"), text_color="#A8F0E2")
        title_label.pack(pady=16)

        # Phrase
        phrase = ctk.CTkLabel(self, text="Here is our statistiques after training", font=("Arial", 20, "bold"), text_color="#A8F0E2", fg_color=page_color)
        phrase.grid(row=1, column=0, pady=10, padx=20, sticky="w")

        # Scrollable frame for images
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color=page_color, width=1150, height=700, corner_radius=24)
        self.scroll_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(4, 20))
        self.grid_rowconfigure(2, weight=1)
        self.display_images()

    def display_images(self):
        # Step 1: Find Statistiques folder from CSV row 1, col 1
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            first_data = next(reader)
            base_path = first_data[1]
        img_dir = os.path.join(base_path, "Statistiques")

        # Step 2: List image files (PNG, JPG, etc.)
        img_files = [os.path.join(img_dir, f)
                    for f in os.listdir(img_dir)
                    if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
        if not img_files:
            ctk.CTkLabel(self.scroll_frame, text="No images found in Statistiques.", font=("Arial", 16), text_color="#F0D48A", fg_color=self.page_color).pack()
            return

        # Step 3: Display all images, taille 1100x600, couleurs originales
        for file in img_files:
            img = Image.open(file)
            # Target max width and height
            max_width, max_height = 1100, 600
            orig_width, orig_height = img.size

            # Compute the scaling factor while maintaining the aspect ratio
            scale = min(max_width / orig_width, max_height / orig_height, 1.5)  # never upscale more than 1.5x
            new_width = int(orig_width * scale)
            new_height = int(orig_height * scale)

            # Only resize if it would actually make the image larger or fit better (no stretch)
            if (new_width, new_height) != img.size:
                img = img.resize((new_width, new_height), Image.LANCZOS)

            photo = ImageTk.PhotoImage(img)
            lbl = ctk.CTkLabel(self.scroll_frame, image=photo, text="")
            lbl.image = photo  # Keep reference!
            lbl.pack(pady=22)


# --- TEST SOLO ---
if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    root = ctk.CTk()
    root.title("Statistics Page Demo")
    root.geometry("1200x900")
    # Set to your real path to evaluations.csv
    csv_path = "Odens/IA_training/evaluations.csv"
    page = StatisticsPage(root, csv_path=csv_path, page_color="#192233")
    page.pack(fill="both", expand=True)
    root.mainloop()
