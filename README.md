# ✨ AI Wallpaper Gallery

An automated GitHub repo that generates a new **AI aesthetic wallpaper** every day at **6:00 AM IST** — completely hands-free.

🌐 **Live Gallery:** [sagar141202.github.io/ai-wallpaper-gallery](https://sagar141202.github.io/ai-wallpaper-gallery/)

---

## How it works

Every morning at 6 AM IST, GitHub Actions automatically:

1. Calls **Groq (Llama 3.1 8B)** to generate 40–50 unique aesthetic image prompts
2. Makes **40–50 individual commits** — one per prompt — keeping the contribution graph green
3. Calls **Hugging Face FLUX.1-schnell** to generate a real 1024×576 wallpaper image
4. Saves the image to `/images/` and updates the live HTML gallery
5. Pushes everything — zero manual effort

## Tech stack

| Tool | Purpose |
|---|---|
| GitHub Actions | Daily cron scheduler |
| Groq API (Llama 3.1 8B) | Generates creative aesthetic prompts |
| Hugging Face FLUX.1-schnell | Generates the actual AI wallpaper image |
| GitHub Pages | Hosts the live gallery |

## Aesthetic styles

Randomly rotates through: lofi · cyberpunk · cottagecore · dark academia · vaporwave · Japanese zen · solarpunk · underwater · fantasy · and more.

## Setup for your own fork

1. Get free Groq API key at [console.groq.com](https://console.groq.com)
2. Get free HF token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
3. Create a PAT at [github.com/settings/tokens](https://github.com/settings/tokens) with `repo` scope
4. Add secrets: `GROQ_API_KEY`, `HF_TOKEN`, `PAT_TOKEN`
5. Update the git email/username in the workflow
6. Enable GitHub Pages from the `/gallery` folder
7. Trigger manually to test

## License

MIT
