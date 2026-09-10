import os
import hashlib
import json

prod_files = [
    r"c:\Users\Shreyash\Documents\vs work\SIH26103\data\paimana_master_dataset.csv",
    r"c:\Users\Shreyash\Documents\vs work\SIH26103\data\paimana_completed_projects.csv",
    r"c:\Users\Shreyash\Documents\vs work\SIH26103\data\paimana_newly_added_projects.csv",
    r"c:\Users\Shreyash\Documents\vs work\SIH26103\target_labels_v2\target_dataset_v2.csv",
    r"c:\Users\Shreyash\Documents\vs work\SIH26103\features\feature_dataset_v1.csv",
    r"c:\Users\Shreyash\Documents\vs work\SIH26103\ml\models\best_model_random_forest.joblib"
]

hashes = {}
for p in prod_files:
    if os.path.exists(p):
        with open(p, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest()
            hashes[p] = h
            print(f"{os.path.basename(p)}: {h}")
    else:
        print(f"MISSING: {p}")

os.makedirs(r"c:\Users\Shreyash\Documents\vs work\SIH26103\mentor_suggestion\clustering", exist_ok=True)
os.makedirs(r"c:\Users\Shreyash\Documents\vs work\SIH26103\mentor_suggestion\data", exist_ok=True)
os.makedirs(r"c:\Users\Shreyash\Documents\vs work\SIH26103\mentor_suggestion\src", exist_ok=True)
os.makedirs(r"c:\Users\Shreyash\Documents\vs work\SIH26103\mentor_suggestion\reports", exist_ok=True)

with open(r"c:\Users\Shreyash\Documents\vs work\SIH26103\mentor_suggestion\clustering\production_hashes_before.json", "w") as f:
    json.dump(hashes, f, indent=2)
print("Saved production_hashes_before.json")
