import os
import hashlib
import json

before_path = r"c:\Users\Shreyash\Documents\vs work\SIH26103\mentor_suggestion\clustering\production_hashes_before.json"
with open(before_path, "r") as f:
    before_hashes = json.load(f)

print("="*80)
print("FINAL PRODUCTION SHA-256 HASH INTEGRITY VERIFICATION")
print("="*80)

all_matched = True
for filepath, expected_hash in before_hashes.items():
    if not os.path.exists(filepath):
        print(f"FAILED: Missing file {filepath}")
        all_matched = False
        continue
    with open(filepath, "rb") as f:
        current_hash = hashlib.sha256(f.read()).hexdigest()
    if current_hash == expected_hash:
        print(f"MATCHED: {os.path.basename(filepath)} ({current_hash[:16]}...)")
    else:
        print(f"MISMATCH: {os.path.basename(filepath)}")
        print(f"  Expected: {expected_hash}")
        print(f"  Current : {current_hash}")
        all_matched = False

print("\n" + "="*80)
if all_matched:
    print("ALL PRODUCTION HASHES MATCHED 100%. PRODUCTION FILES CHANGED = 0 (ZERO).")
else:
    print("ERROR: PRODUCTION HASH VIOLATION DETECTED.")
print("="*80)
