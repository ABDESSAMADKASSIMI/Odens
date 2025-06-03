
---

# 📚 Model Versioning & Training Scripts

Throughout this project, we faced many modeling challenges and tested a variety of solutions—each time, saving our code for reproducibility and future comparison.

**What did we do?**

* For every significant version (from V1 up to V7), we kept the *full model training script*—including all data loading, preprocessing, model definition, and evaluation steps.
* Each script reflects a different modeling strategy:
  You’ll find approaches with CatBoost, XGBoost, LightGBM, TabNet, PyTorch MLP, feature selection utilities, Optuna hyperparameter optimization, and more.
* We always saved the version that achieved the best results *at the time*, but we didn’t throw away the others—so the team can review what worked and what didn’t.

**Want to dig deeper?**
If you’re interested in how we processed data for any specific version, or want to see our preprocessing code or feature engineering steps, just ask—I'm happy to share any scripts or explain the logic behind any experiment.

---

**How to use these scripts:**

* Each `Verion_X.py` file is standalone: you can run it to retrain or benchmark that approach.
* They make great references if you want to re-test, reproduce results, or compare new ideas to our previous models.

**If you have any questions or want to explore a particular version’s data processing workflow in detail, let me know—I'll gladly walk you through it or provide the necessary code.**

---
