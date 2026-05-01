import os
import random
import time
import json
import requests
from datetime import datetime
from groq import Groq

groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])
HF_TOKEN = os.environ["HF_TOKEN"]
DATE_STR = datetime.now().strftime("%Y-%m-%d")
TIME_STR = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ── Aesthetic styles for prompts ──────────────────────────────────────────────
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

def generate_prompts_batch(count):
    """Use Groq to generate a batch of unique aesthetic image prompts."""
    style = random.choice(STYLES)
    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{
            "role": "user",
            "content": (
                f"Generate {count} unique, vivid, highly detailed AI image prompts "
                f"for aesthetic wallpapers in this style: '{style}'. "
                f"Each prompt should be 1-2 sentences, rich with visual detail. "
                f"Output ONLY a JSON array of strings, nothing else. "
                f"Example: [\"prompt one\", \"prompt two\"]"
            )
        }],
        max_tokens=2000,
        temperature=1.0,
    )
    raw = response.choices[0].message.content.strip()
    # Strip markdown fences if present
    raw = raw.replace("```json", "").replace("```", "").strip()
    prompts = json.loads(raw)
    return prompts, style

def generate_image(prompt):
    """Call Hugging Face FLUX.1-schnell to generate an image."""
    api_url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "width": 1024,
            "height": 576,   # 16:9 wallpaper ratio
            "num_inference_steps": 4,
        }
    }
    # Retry up to 3 times (model may need warm-up)
    for attempt in range(3):
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            return response.content   # raw image bytes
        elif response.status_code == 503:
            print(f"    Model loading, waiting 20s... (attempt {attempt+1})")
            time.sleep(20)
        else:
            print(f"    Image gen failed: {response.status_code} — {response.text[:100]}")
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
    os.system(f'git commit -m "wallpaper({index}/{total}): {prompt[:50]}"')
    print(f"  ✓ Commit {index}/{total}")

def update_gallery(image_filename, prompt, style, all_entries):
    """Regenerate the HTML gallery page."""
    cards_html = ""
    for entry in reversed(all_entries):   # newest first
        cards_html += f"""
        <div class="card">
          <img src="../images/{entry['image']}" alt="{entry['prompt'][:60]}" loading="lazy" onerror="this.parentElement.style.display='none'">
          <div class="card-body">
            <span class="style-tag">{entry['style']}</span>
            <p class="prompt-text">{entry['prompt'][:120]}...</p>
            <span class="date">{entry['date']}</span>
          </div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Wallpaper Gallery</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ background: #0d0d0d; color: #e0e0e0; font-family: 'Segoe UI', sans-serif; }}
    header {{ text-align: center; padding: 3rem 1rem 1rem; }}
    header h1 {{ font-size: 2.5rem; background: linear-gradient(135deg, #a78bfa, #60a5fa, #34d399); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    header p {{ color: #888; margin-top: 0.5rem; font-size: 0.95rem; }}
    .stats {{ text-align: center; padding: 1rem; color: #666; font-size: 0.85rem; }}
    .gallery {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 1.5rem; padding: 2rem; max-width: 1400px; margin: 0 auto; }}
    .card {{ background: #1a1a1a; border-radius: 12px; overflow: hidden; border: 1px solid #2a2a2a; transition: transform 0.2s, border-color 0.2s; }}
    .card:hover {{ transform: translateY(-4px); border-color: #a78bfa; }}
    .card img {{ width: 100%; height: 200px; object-fit: cover; display: block; }}
    .card-body {{ padding: 1rem; }}
    .style-tag {{ background: #1e1b4b; color: #a78bfa; border-radius: 99px; padding: 2px 10px; font-size: 0.75rem; }}
    .prompt-text {{ margin: 0.6rem 0; font-size: 0.88rem; color: #bbb; line-height: 1.5; }}
    .date {{ font-size: 0.75rem; color: #555; }}
    footer {{ text-align: center; padding: 2rem; color: #444; font-size: 0.8rem; }}
  </style>
</head>
<body>
  <header>
    <h1>✨ AI Wallpaper Gallery</h1>
    <p>Auto-generated daily using FLUX.1 + Groq · Updated every morning at 6 AM IST</p>
  </header>
  <div class="stats">
    {len(all_entries)} wallpapers generated and counting · Last updated {TIME_STR} IST
  </div>
  <div class="gallery">
    {cards_html}
  </div>
  <footer>Built with GitHub Actions · Hugging Face FLUX.1 · Groq Llama 3.1</footer>
</body>
</html>"""

    with open("docs/index.html", "w") as f:
        f.write(html)

    os.system('git add docs/index.html')
    os.system(f'git commit -m "gallery: update with {DATE_STR} wallpaper"')
    print("  ✓ Gallery page updated")

def load_entries_log():
    """Load the log of all previous images."""
    log_path = "images/log.json"
    if os.path.exists(log_path):
        with open(log_path) as f:
            return json.load(f)
    return []

def save_entries_log(entries):
    with open("images/log.json", "w") as f:
        json.dump(entries, f, indent=2)
    os.system('git add images/log.json')

def main():
    total_commits = random.randint(40, 50)
    print(f"Target: {total_commits} commits + 1 image + gallery update")

    # Generate all prompts in one Groq call (saves API quota)
    print("Generating prompts via Groq...")
    prompts, style = generate_prompts_batch(total_commits)
    if len(prompts) < total_commits:
        # Pad if Groq returned fewer
        while len(prompts) < total_commits:
            prompts.append(prompts[random.randint(0, len(prompts)-1)])
    prompts = prompts[:total_commits]
    print(f"  ✓ Got {len(prompts)} prompts in style: {style[:40]}")

    # Make 40-50 commits (one per prompt)
    for i, prompt in enumerate(prompts, 1):
        make_commit(i, total_commits, prompt, style)
        time.sleep(random.randint(2, 5))

    # Generate ONE actual image from the best-sounding prompt
    print("\nGenerating AI image via HuggingFace FLUX.1...")
    image_prompt = prompts[0]   # use first prompt for the image
    image_bytes = generate_image(f"{image_prompt}, 4k wallpaper, highly detailed, {style}")

    image_filename = f"{DATE_STR}_wallpaper.jpg"
    all_entries = load_entries_log()

    if image_bytes:
        image_path = f"images/{image_filename}"
        with open(image_path, "wb") as f:
            f.write(image_bytes)
        os.system(f'git add "{image_path}"')
        os.system(f'git commit -m "image: daily wallpaper {DATE_STR}"')
        print(f"  ✓ Image saved: {image_filename}")

        all_entries.append({
            "date": DATE_STR,
            "image": image_filename,
            "prompt": image_prompt,
            "style": style
        })
    else:
        print("  ✗ Image generation failed, skipping image this run")
        all_entries.append({
            "date": DATE_STR,
            "image": "",
            "prompt": image_prompt,
            "style": style
        })

    save_entries_log(all_entries)
    update_gallery(image_filename, image_prompt, style, all_entries)

    print(f"\nAll done — {total_commits} commits + image + gallery updated!")

if __name__ == "__main__":
    main()
