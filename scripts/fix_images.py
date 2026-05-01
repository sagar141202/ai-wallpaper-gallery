import os
import shutil
import json

def main():
    # Load the log
    log_path = "docs/log.json"
    if not os.path.exists(log_path):
        print("No log.json found")
        return

    with open(log_path) as f:
        entries = json.load(f)

    os.makedirs("docs/images", exist_ok=True)
    fixed = 0

    for entry in entries:
        img = entry.get("image", "")
        if not img:
            print(f"  ⚠ No image for {entry['date']} — skipping")
            continue

        src = f"images/{img}"
        dst = f"docs/images/{img}"

        if os.path.exists(dst):
            print(f"  ✓ Already exists: {img}")
            continue

        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"  ✓ Copied: {img}")
            fixed += 1
        else:
            print(f"  ✗ Source missing: {src} — image was never generated")

    if fixed > 0:
        os.system('git add docs/images/')
        os.system(f'git commit -m "fix: backfill {fixed} images into docs/images/"')
        print(f"\nDone — {fixed} images copied and committed")
    else:
        print("\nNothing to fix — all images already in docs/images/")

if __name__ == "__main__":
    main()
