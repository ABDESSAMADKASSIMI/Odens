
---

# 📦 Data Processing & Feature Engineering

Hello Adam, hello team! 👋

Welcome to the Data Processing & Feature Engineering section of our AI-powered pricing engine project.

Here, I’ll walk you through how we transform raw, real-world manufacturing data—**starting from PDF quotes**—into a clean, structured, and feature-rich dataset, ready for cutting-edge machine learning.

Each part is designed with transparency, modularity, and future scalability in mind.
You’ll find direct script references at every step, so you can jump straight into the code whenever you’re curious.

Let’s get started on our data adventure! 🚀

---

## 🏁 Step 1: PDF Extraction – The True Beginning

* **What’s happening?**
  Our journey starts with a pile of PDF files—actual historical quotes, just like you’d get from a customer inbox or archive. No shortcuts here: we go from “paper” to “data.”
* **Justification:**
  This mirrors real business scenarios, where data isn’t born clean. By starting from PDFs, we prove the system’s robustness and real-world utility.
* **How?**

  * In `Pdf_txt.py`, we use `pdfplumber` to open every PDF, reading each page and pulling out all the raw text.
  * We save each result as a `.txt` file, ready for cleaning and structuring downstream.
  * *Why this approach?* Many companies only have PDFs as records—starting here ensures our platform works for real businesses.

---

## 🧹 Step 2: Text Correction & Standardization (from Chaos to Clarity)

* **What’s happening?**
  The raw extracted text can be a mess—tables get jumbled, and numbers might end up in the wrong columns.
  Here’s an example, straight from a PDF:

  ```
  Aluminiumprofiler från Nordisk Alu Profil/ Purso OY
  Profil nr / Vikt Längd/m Kap + truml ca antal Pris Legerin
  Kund ref. kg/m m Pris/st Årsvolym st kr/st g:
  SEK
  Karmlist 1,342 23,8 0,78 40000 2,92 Rå
  Karmlist 1,342 25,8 0,78 40000 3,05 Rå
  Karmlist 1,342 23,8 0,78 85000 2,88 Rå
  Karmlist 1,342 25,8 0,78 85000 3,01 Rå
  ```

  We clean this up into:

  ```
  Profil nr/Kund ref | Vikt kg/m | Längd/m m | Kap + truml Pris/st | ca antal Årsvolym st | Prix kr/st SEK | Legering
  -------------------|-----------|-----------|---------------------|----------------------|----------------|---------
  Karmlist           |     1.342 |      23.8 |                0.78 |                40000 |           2.92 | Rå
  ...
  ```
* **Justification:**
  Structured tables mean no guesswork—downstream scripts can always trust what’s in each column.
* **How?**

  * In `txt_Correction.py`, we analyze every line, using logic to detect section headers and table starts/ends.
  * We split out metadata, product lines, and commercial conditions.
  * We normalize number formats (converting “1,342” to “1.342” for example).
  * We automatically generate consistent headers and align all product columns.
  * The result: a clean, reliable, and standardized text file, ready to become structured data.

---

## 🏗️ Step 3: Schema Parsing & Validation

* **What’s happening?**
  Now that our data is structured, we parse the cleaned text into a flexible schema that holds everything important: material, geometry, tolerances, context, and target price.
* **Justification:**
  Flexible, validated schemas mean we’re ready for changing requirements or new fields—if a new supplier adds a “Coating Type” column, we simply update the schema and move forward, no breaking changes.
* **How?**

  * In `txt_json.py`, we turn the standardized text into rich JSON, using sections for metadata, products, and conditions.
  * In `Handling.py`, we use **pydantic** models to enforce correct field types and required values, raising clear errors if anything is missing or misformatted.
  * This approach also means the pipeline is “self-documenting”—it’s always clear what fields are expected.

---

## 🧠 Step 4: Handling — Smart Data Cleaning & Preprocessing

* **What’s happening?**
  Here’s where we solve the problems that trip up most naive data pipelines: missing values, outliers, and high-cardinality categories.
* **How?**

  * **Smart validation:**
    In `Handling.py`, we validate each JSON with pydantic before moving forward. This catches “bad” data right at the gate.
  * **Advanced missing value imputation:**
    Instead of just filling blanks with zeros or column averages, we use **iterative imputation** (`sklearn.experimental.IterativeImputer`). This method estimates each missing value based on all other available fields in the same row, keeping the statistical relationships intact. For example, if “weight” is missing but “length” and “volume” are present, we can make a much better guess than a random average.
  * **Outlier detection and smoothing:**
    We apply an **Isolation Forest** algorithm to flag outliers (points that are statistically “weird” compared to the rest of the data). Then, instead of deleting them, we clip these values to the 5th and 95th percentiles—preserving real extremes but removing obvious errors.
  * **Target encoding for high-cardinality variables:**
    For fields like customer or profile reference, which could have hundreds of unique values, we use **target encoding**. This replaces each category with a smoothed average of the target variable, keeping the model powerful and preventing overfitting or “curse of dimensionality.”
* **Why this is smart:**
  Most “data cleaning scripts” run a few quick fixes—here we use advanced, proven machine learning approaches. That means more reliable predictions and no “garbage in, garbage out.”

---

## 🔬 Step 5: Feature Engineering

* **What’s happening?**
  Here, we transform domain knowledge into features that matter for pricing.
* **How?**

  * **Geometric complexity & manufacturability:**
    In `Last_Traitement.py`, we calculate custom features—like thinness ratio, area-to-length ratio, wall factor, DFM (Design for Manufacturability) index, and symmetry score—using formulas that blend domain knowledge and data science. For example, DFM index tells the model how “difficult” a profile might be to manufacture, impacting its likely price.
  * **Tolerance mapping:**
    Still in `Last_Traitement.py`, we map textual manufacturing standards (like “EN 755-9” or “ASME Y14.5”) to quantitative features (linear tolerance, angular tolerance, flatness, etc.), so the model can use this critical information.
  * **Material encoding:**
    In `Organisation_json.py`, we parse and encode alloy type, strength, temper code, and European standard into numeric fields—so even “qualitative” differences become usable by AI.
  * **LME price features:**

    * **And here’s a key strength:**
      The system **fetches daily LME (London Metal Exchange) prices directly from the internet**.
      In `Last_Traitement.py`, we create time-series features such as moving averages and lagged values for LME.
      *Why?* Because our predictions reflect the true, current market, not just historical averages. This means every day the AI’s features are fresh—no manual updates required.

---

## 🧪 Step 6: Synthetic Data Generation

* **What’s happening?**
  To build a robust ML model and meet dataset size targets, we generate realistic synthetic quote variants from the originals.
* **How?**

  * In `Simulation.py`, for every real quote, we generate up to 20 variants by:

    * Adding small, consistent noise to numerical fields (within plausible business limits).
    * Randomly adjusting categorical fields (like alloy or tolerance standard).
    * Keeping relationships between fields realistic (e.g., larger volume, slightly different price).
  * This gives us the diversity and volume needed for robust AI, especially when historical data is scarce.

---

## 🗃️ Step 7: User-specific, Secure, and Scalable Storage

* **What’s happening?**
  Each user’s data is kept separate for security and easy scaling. The folder structure makes it simple to add more users or migrate to a real database later.
* **How?**

  * Every processing script is built to work with user-specific directories, and the design can be adapted to any multi-tenant or cloud-based storage in the future.
  * This means the system is ready to grow without having to rewrite the data pipeline.

---

## 🛠️ Full Pipeline Orchestration

* **Want to run the whole adventure?**
  Script: `main_Data_Processing.py` runs every step in order, from PDFs all the way to an ML-ready CSV or JSON.
  *(Check path: Odens/Data\_Processing/main\_Data\_Processing.py)*

---

## ⭐ Why This Data Processing Is Special

* Starts with messy, real-world PDFs—no lab assumptions
* Cleaning and structuring are handled with modern, robust ML methods
* Feature engineering is grounded in manufacturing science
* LME features are always up to date—**fetched live from the internet**
* Data isolation, security, and scalability are built in from day one
* The entire pipeline is transparent, modular, and open for review or extension

---

> **Any step look interesting? Check the script and follow the path. All code is documented and ready for you to explore.**

---
