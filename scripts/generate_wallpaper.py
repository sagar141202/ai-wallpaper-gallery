import os
import random
import time
import json
import requests
from datetime import datetime
from groq import Groq
from huggingface_hub import InferenceClient

groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])
hf_client = InferenceClient(token=os.environ["HF_TOKEN"])

DATE_STR = datetime.now().strftime("%Y-%m-%d")
TIME_STR = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# How many images to generate per day
IMAGES_PER_DAY = 5
# Total commits split evenly across images
TOTAL_COMMITS = random.randint(45, 50)

STYLES = [
    "lofi aesthetic, soft pastel colors, cozy room, warm lighting",
    "cyberpunk cityscape, neon lights, rain-soaked streets, night",
    "cottagecore, wildflower meadow, golden hour sunlight, dreamy",
    "dark academia library, candle light, antique books, moody",
    "vaporwave sunset, retro grid, palm trees, purple and pink sky",
    "Japanese zen garden, cherry blossoms, misty mountains, serene",
    "solarpunk greenhouse, lush plants, natural light, utopian",
    "ocean at midnight, bioluminescent waves, starry sky, ethereal",
    "autumn forest path, fallen leaves, fog, cinematic lighting",
    "minimalist studio, white walls, soft shadows, architectural",
    "fantasy floating islands, waterfalls, magical clouds, epic",
    "desert at dusk, sand dunes, amber sky, vast emptiness",
    "underwater coral reef, light rays, vibrant tropical fish",
    "snowy mountain cabin, warm glow from windows, snowfall",
    "futuristic space station, stars through glass dome, sci-fi",
]

# ─────────────────────────────────────────────────────────────────────────────

def generate_prompts(count, style):
    """Use Groq to generate a batch of unique prompts for one style."""
    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{
            "role": "user",
            "content": (
                f"Generate {count} unique, vivid, highly detailed AI image prompts "
                f"for aesthetic wallpapers in this style: '{style}'. "
                f"Each prompt should be 1-2 sentences, very descriptive and visual. "
                f"Output ONLY a JSON array of strings, no explanation, no markdown. "
                f'Example: ["prompt one here", "prompt two here"]'
            )
        }],
        max_tokens=2000,
        temperature=1.0,
    )
    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    # Find the JSON array in the response
    start = raw.find("[")
    end = raw.rfind("]") + 1
    if start == -1 or end == 0:
        raise ValueError(f"No JSON array found in Groq response: {raw[:200]}")
    prompts = json.loads(raw[start:end])
    return prompts

def generate_image(prompt, style):
    """Generate image using HuggingFace InferenceClient (handles API correctly)."""
    full_prompt = f"{prompt}, {style}, 4k, highly detailed, award winning photography"
    print(f"    Prompt: {full_prompt[:80]}...")

    for attempt in range(4):
        try:
            image = hf_client.text_to_image(
                prompt=full_prompt,
                model="black-forest-labs/FLUX.1-schnell",
            )
            return image  # returns a PIL Image object
        except Exception as e:
            err = str(e)
            if "503" in err or "loading" in err.lower():
                wait = 25 * (attempt + 1)
                print(f"    Model warming up, waiting {wait}s... (attempt {attempt+1}/4)")
                time.sleep(wait)
            elif "429" in err or "rate" in err.lower():
                wait = 60
                print(f"    Rate limited, waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"    Image gen error: {err[:120]}")
                return None
    return None

def make_commit(index, total, prompt, style):
    """Write a markdown file and commit it."""
    filename = f"content/{DATE_STR}_prompt_{index:03d}.md"
    with open(filename, "w") as f:
        f.write(f"# Wallpaper Prompt {index} of {total}\n\n")
        f.write(f"**Date:** {TIME_STR}\n\n")
        f.write(f"**Style:** {style}\n\n")
        f.write(f"**Prompt:**\n\n> {prompt}\n")
    os.system(f'git add "{filename}"')
    os.system(f'git commit -m "wallpaper({index}/{total}): {prompt[:48]}"')
    print(f"  ✓ Commit {index}/{total}")

def load_entries_log():
    log_path = "docs/log.json"
    if os.path.exists(log_path):
        with open(log_path) as f:
            return json.load(f)
    return []

def save_entries_log(entries):
    with open("docs/log.json", "w") as f:
        json.dump(entries, f, indent=2)
    os.system('git add docs/log.json')

def update_gallery(all_entries):
    """Regenerate the full HTML gallery page."""
    cards_html = ""
    for entry in reversed(all_entries):
        if entry.get("image"):
            img_tag = (
                f'<img src="images/{entry["image"]}" '
                f'alt="{entry["prompt"][:60]}" loading="lazy">'
            )
        else:
            img_tag = '<div class="no-img">🖼️ Generation unavailable</div>'

        cards_html += f"""
        <div class="card">
          {img_tag}
          <div class="card-body">
            <span class="style-tag">{entry["style"][:45]}</span>
            <p class="prompt-text">{entry["prompt"][:130]}</p>
            <span class="date">{entry["date"]}</span>
          </div>
        </div>"""

    total = len(all_entries)
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Wallpaper Gallery</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: #0a0a0f; color: #e0e0e0; font-family: 'Segoe UI', system-ui, sans-serif; min-height: 100vh; }}
    header {{ text-align: center; padding: 3.5rem 1rem 0.5rem; }}
    header h1 {{
      font-size: clamp(1.8rem, 5vw, 3rem);
      background: linear-gradient(135deg, #a78bfa 0%, #60a5fa 50%, #34d399 100%);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
      background-clip: text; letter-spacing: -0.5px;
    }}
    header p {{ color: #666; margin-top: 0.6rem; font-size: 0.92rem; }}
    .stats {{
      text-align: center; padding: 0.8rem 1rem;
      color: #555; font-size: 0.82rem; letter-spacing: 0.3px;
    }}
    .stats strong {{ color: #a78bfa; }}
    .gallery {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 1.4rem; padding: 1.5rem 2rem 3rem;
      max-width: 1400px; margin: 0 auto;
    }}
    .card {{
      background: #13131a; border-radius: 14px; overflow: hidden;
      border: 1px solid #1e1e2e;
      transition: transform 0.22s ease, border-color 0.22s ease, box-shadow 0.22s ease;
    }}
    .card:hover {{
      transform: translateY(-5px);
      border-color: #7c3aed;
      box-shadow: 0 8px 30px rgba(124, 58, 237, 0.18);
    }}
    .card img {{
      width: 100%; height: 210px; object-fit: cover;
      display: block; background: #0d0d14;
    }}
    .no-img {{
      width: 100%; height: 210px; display: flex;
      align-items: center; justify-content: center;
      background: #0d0d14; color: #333; font-size: 0.85rem;
      flex-direction: column; gap: 0.5rem;
    }}
    .card-body {{ padding: 1rem 1.1rem 1.1rem; }}
    .style-tag {{
      background: #1a1040; color: #a78bfa;
      border-radius: 99px; padding: 3px 11px;
      font-size: 0.72rem; display: inline-block;
      border: 1px solid #2d1f6e; margin-bottom: 0.55rem;
    }}
    .prompt-text {{
      font-size: 0.86rem; color: #aaa; line-height: 1.55;
      margin-bottom: 0.6rem;
      display: -webkit-box; -webkit-line-clamp: 3;
      -webkit-box-orient: vertical; overflow: hidden;
    }}
    .date {{ font-size: 0.72rem; color: #444; }}
    footer {{
      text-align: center; padding: 1.5rem;
      color: #333; font-size: 0.78rem; border-top: 1px solid #111;
    }}
  </style>
</head>
<body>
  <header>
    <h1>✨ AI Wallpaper Gallery</h1>
    <p>Auto-generated daily · FLUX.1-schnell + Groq Llama · 6 AM IST every morning</p>
  </header>
  <div class="stats">
    <strong>{total}</strong> wallpapers generated · Last updated {TIME_STR} IST
  </div>
  <div class="gallery">
    {cards_html}
  </div>
  <footer>
    Powered by GitHub Actions · Hugging Face FLUX.1-schnell · Groq Llama 3.1 8B
  </footer>
</body>
</html>"""

    os.makedirs("docs", exist_ok=True)
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html)
    os.system('git add docs/index.html')
    os.system(f'git commit -m "gallery: {total} wallpapers · {DATE_STR}"')
    print(f"  ✓ Gallery updated — {total} total wallpapers")

# ─────────────────────────────────────────────────────────────────────────────

def main():
    print(f"═══════════════════════════════════════")
    print(f"  AI Wallpaper Bot — {DATE_STR}")
    print(f"  {IMAGES_PER_DAY} images · {TOTAL_COMMITS} commits")
    print(f"═══════════════════════════════════════")

    # Ensure all folders exist
    os.makedirs("docs/images", exist_ok=True)
    os.makedirs("images", exist_ok=True)
    os.makedirs("content", exist_ok=True)

    # Disable Jekyll
    if not os.path.exists("docs/.nojekyll"):
        open("docs/.nojekyll", "w").close()
        os.system('git add docs/.nojekyll')
        os.system('git commit -m "chore: disable jekyll"')
        print("  ✓ .nojekyll created")

    # Pick IMAGES_PER_DAY different styles (no repeats today)
    todays_styles = random.sample(STYLES, IMAGES_PER_DAY)

    # Divide commits evenly across images
    commits_per_image = TOTAL_COMMITS // IMAGES_PER_DAY
    commit_counter = 0
    all_entries = load_entries_log()

    for img_idx, style in enumerate(todays_styles, 1):
        print(f"\n── Image {img_idx}/{IMAGES_PER_DAY} ──────────────────────────")
        print(f"   Style: {style[:55]}")

        # Generate prompts for this image's commits
        prompts_needed = commits_per_image
        # Last image gets any leftover commits
        if img_idx == IMAGES_PER_DAY:
            prompts_needed = TOTAL_COMMITS - commit_counter

        try:
            prompts = generate_prompts(prompts_needed, style)
        except Exception as e:
            print(f"  ✗ Groq error: {e}")
            prompts = [f"Beautiful {style} scene, highly detailed aesthetic wallpaper"] * prompts_needed

        # Pad/trim to exact count needed
        while len(prompts) < prompts_needed:
            prompts.append(prompts[random.randint(0, len(prompts) - 1)])
        prompts = prompts[:prompts_needed]

        # Make commits for this image
        for prompt in prompts:
            commit_counter += 1
            make_commit(commit_counter, TOTAL_COMMITS, prompt, style)
            time.sleep(random.randint(2, 4))

        # Generate the actual image using the first prompt
        print(f"  Generating image {img_idx}...")
        image_pil = generate_image(prompts[0], style)

        image_filename = f"{DATE_STR}_wallpaper_{img_idx:02d}.jpg"

        if image_pil is not None:
            # Save as JPEG to both locations
            image_pil = image_pil.convert("RGB")

            archive_path = f"images/{image_filename}"
            docs_path = f"docs/images/{image_filename}"

            image_pil.save(archive_path, "JPEG", quality=92)
            image_pil.save(docs_path, "JPEG", quality=92)

            os.system(f'git add "{archive_path}"')
            os.system(f'git add "{docs_path}"')
            os.system(f'git commit -m "image({img_idx}/{IMAGES_PER_DAY}): {style[:45]}"')
            print(f"  ✓ Image {img_idx} saved: {image_filename}")

            all_entries.append({
                "date": DATE_STR,
                "image": image_filename,
                "prompt": prompts[0],
                "style": style,
            })
        else:
            print(f"  ✗ Image {img_idx} failed — recording entry without image")
            all_entries.append({
                "date": DATE_STR,
                "image": "",
                "prompt": prompts[0],
                "style": style,
            })

        # Pause between images to avoid rate limiting
        if img_idx < IMAGES_PER_DAY:
            print(f"  Waiting 15s before next image...")
            time.sleep(15)

    # Save log and update gallery
    print(f"\n── Finalising ───────────────────────────")
    save_entries_log(all_entries)
    update_gallery(all_entries)

    print(f"\n✅ Done — {commit_counter} commits · {IMAGES_PER_DAY} images attempted · gallery updated")


if __name__ == "__main__":
    main()
