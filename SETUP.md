# Scrapes McGee — Quick Setup Guide

## 🚀 Get Started in 3 Steps

### 1️⃣ Push to GitHub

```bash
cd scrapes-mcgee
git init
git add .
git commit -m "Initial commit - Scrapes McGee v0.1"
git branch -M main
git remote add origin https://github.com/merrypranxter/scrapes-mcgee.git
git push -u origin main
```

### 2️⃣ Get Gemini API Key

1. Go to: https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key

### 3️⃣ Run McGee

**Locally:**
```bash
# Install dependencies
pip install -e .

# Create .env file
echo "GEMINI_API_KEY=your_key_here" > .env

# Run McGee
python scrapes.py
```

**In GitHub Codespaces:**
1. Go to your repo on GitHub
2. Click "Code" → "Codespaces" → "Create codespace"
3. In Codespaces terminal:
   ```bash
   echo "GEMINI_API_KEY=your_key_here" > .env
   python scrapes.py
   ```

---

## 💬 Example Conversation

```
You: yo McGee, scrape erowid for DMT entity encounters, like 50 reports

McGee: Aight, hunting for machine elves. Targeting experience vaults,
       looking for breakthrough + entity keywords. Want me to grab
       dosages and entity descriptions too?

You: yeah and only the wild ones, skip the boring shit

McGee: Got it — filtering for high-weirdness reports. Starting crawl...
       [progress updates]
       Done. 53 reports extracted. Top entities: jesters (23), 
       geometric beings (18), insectoid intelligence (8).
       Want JSON, markdown, or SQLite?

You: markdown

McGee: ✓ Exported to data/erowid_dmt_20240315.md
```

---

## 🎯 What You Can Scrape

### Erowid Trip Reports
```
"scrape erowid for salvia reports with zipper/wheel entities"
"get 100 DMT breakthrough reports, extract dosages and entity types"
```

### McKenna Transcripts
```
"scrape organism.earth for all McKenna talks about language"
"find timewave zero discussions, extract quotes and concepts"
```

### Shadertoy Shaders
```
"get voronoi noise techniques from shadertoy with code"
"scrape fractal shaders, need the GLSL and descriptions"
```

### Generic Sites
```
"scrape [url] for [topic], extract [fields]"
```

---

## 📂 Project Structure

```
scrapes-mcgee/
├── scrapes.py           # Main chat interface
├── scraper/             # Core engine
├── mcgee/               # McGee's brain
├── targets/examples/    # Example configs
├── examples/            # Example scripts
└── data/                # Your scraped content goes here
```

---

## 🛠️ Advanced Usage

### Programmatic (no chat)

```python
from mcgee.agent import ScrapesMcGee

mcgee = ScrapesMcGee(api_key)
await mcgee.execute_scrape(
    target_url="https://...",
    max_depth=3,
    extraction_prompt="Extract: title, content, etc"
)
```

See `examples/scrape_erowid.py` for full example.

### YAML Configs

Save repeated scrapes:
```yaml
# targets/my_scrape.yaml
target_url: "https://example.com"
max_depth: 3
selection_prompt: "Only pages about X"
extraction_prompt: "Extract: field1, field2"
```

Load it: `You: load targets/my_scrape.yaml`

---

## 🐛 Troubleshooting

**"GEMINI_API_KEY not found"**
→ Create `.env` file with your key

**McGee not responding**
→ Check your API key is valid
→ Try restarting the script

**Scraping too slow**
→ Reduce `max_pages` or `max_depth`
→ Use more specific `selection_prompt`

**Can't install dependencies**
→ Try: `pip install --upgrade pip`
→ Or use: `uv pip install -e .`

---

## 🎨 Next Steps

1. ✅ **Test McGee** — Run `python scrapes.py` and try scraping
2. ✅ **Try examples** — Run `python examples/scrape_erowid.py`
3. ✅ **Create your own configs** — Copy `targets/examples/` and customize
4. ✅ **Integrate with your projects** — Use scraped data in your codex/corpus work

---

## 📞 Need Help?

- Check the main README.md
- Open an issue on GitHub
- DM on Twitter/X (if you have Merry's handle)

---

**Built with chaos and coffee ☕🕷️**
