Crystal clear!
You want a **developer/professional-level logic explanation**—not how users interact, but **how the code and functions interact**:

* What gets called,
* In what order,
* How user isolation is achieved,
* How training is triggered and handled,
* And the reasoning for each key architectural step.

You want the **underlying workflow and logic** explained for the client’s technical team or devs, not end users.
Here’s exactly that, based on your `Page_main.py` and overall architecture—still lively, but precise and functional, with just a hint of emoji.

---

# 🛠️ Oden Platform – Workflow & Core Logic (For Developers & Technical Teams)

Here’s how Oden Platform orchestrates user isolation, model training, versioning, and real-time updates—step by step, function by function.

---

## 1️⃣ User Context & Workspace Initialization

* **On signup:**
  The system creates a private directory tree under `Odens/Global_engin/{username}_{password}/`, with subfolders for training data (`DATA_1`), predictions (`DATA_2`), model assets (`IA_Models`), and temp files.
* **On login:**
  The app loads `user_info.csv` to build a session context (user profile, first-login status, workspace paths).
  All future actions (training, prediction, stats) are then *scoped* to this user context—no data ever leaves this sandbox.

---

## 2️⃣ Page Navigation & Main Event Loop

* The main interface (`MainApp` in `Page_main.py`) uses **frame switching** to show the correct view:

  * `LoginFrame` (auth)
  * `SignupFrame` (user registration)
  * `Dashboard` (main nav)
* `Dashboard` further swaps in specialized pages (Prediction, Training, Statistics, Version Control, etc.), always using the current user’s directories as working space.

---

## 3️⃣ Data Flow: Prediction and Training

* **Prediction:**

  * When the user enters product specs and clicks predict, the form collects data and writes it to the current user’s `DATA_2` folder.
  * The active trained model (loaded from `IA_Models/ensemble_model.pkl`) is used to generate a prediction, which is displayed and also logged for traceability.
  * Each prediction increments a counter. Once 50 new predictions are reached, the retraining logic is triggered.
* **Training:**

  * Training is always launched in the context of the current user’s workspace.
  * When called (from the IA\_Model/Train page or via automatic trigger), the workflow is:

    1. Collect and validate all raw and new PDF data in `DATA_1`.
    2. Run `main_Data_Processing.py` to extract, clean, validate, and engineer features, then output a training-ready CSV/JSON.
    3. Call `Model_Training()`, which:

       * Loads and concatenates user data,
       * Runs feature selection with XGBoost,
       * Trains an MLP (with the top features),
       * Creates a VotingRegressor ensemble,
       * Validates performance, saves metrics and plots,
       * Serializes the new model and scaler into the user’s `IA_Models` folder (with versioning).
    4. Updates the model version index, so the dashboard and stats always point to the latest.

---

## 4️⃣ Versioning & Audit Trail

* Each new training run saves:

  * The model artifacts (`ensemble_model.pkl`, `scaler.pkl`)
  * All evaluation metrics and plots
  * A log entry in `evaluations.csv` or an equivalent version-tracking file.
* Old models are never overwritten—they’re archived by version, allowing full rollback, side-by-side comparison, or audit.

---

## 5️⃣ Automation & Continuous Learning

* After every batch of 50 predictions, the retraining trigger is auto-fired.

  * The process above (data processing → training → model promotion) happens in the background.
  * Users are notified in-app once the new model is available.
* This **continuous learning loop** ensures the AI gets smarter with real-world use, without manual intervention.

---

## 6️⃣ Security, Privacy, and User Isolation

* All filesystem and memory operations are strictly user-scoped—paths are built from session context and never overlap.
* Credential validation is enforced at each sensitive operation.
* No user can access or impact another user’s files, predictions, or models—even with concurrent logins.

---

## 7️⃣ Live Market Data Integration

* On the home page, live aluminium prices are fetched via the `yfinance` API every time the dashboard is loaded.
* This value is also recorded and used in feature engineering for the most recent predictions, ensuring models always use up-to-date market data.

---

**Summary:**
The Oden Platform’s logic is designed for end-to-end automation, robust user separation, and smooth retraining—powered by clearly structured function calls and tight workspace scoping. Every step, from data ingestion to model deployment, is tracked, versioned, and instantly recoverable.

---

Want a call graph, more detailed class/function breakdown, or code snippets? Just say the word!
