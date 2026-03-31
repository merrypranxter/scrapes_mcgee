# McGee + GitHub Integration — Setup Guide

## ✨ New Feature: Push to GitHub!

McGee can now push scraped content directly to your repos.

---

## Quick Setup (3 steps):

### 1. Install PyGithub
```bash
cd ~/Documents/scrapes-mcgee
pip3 install PyGithub --break-system-packages
```

### 2. Get GitHub Token
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Give it a name: "Scrapes McGee"
4. Check: **`repo`** (Full control of private repositories)
5. Click "Generate token" at bottom
6. **Copy the token** (you won't see it again!)

### 3. Add Token to .env
```bash
cd ~/Documents/scrapes-mcgee
nano .env
```

Add this line (paste your actual token):
```
GITHUB_TOKEN=ghp_your_token_here
```

Save: Ctrl+O, Enter, Ctrl+X

---

## Using GitHub with McGee:

### List Your Repos
```
You: list repos

McGee: Found 15 repositories:
       • Terence_McKenna_Corpus
       • ghost-erowid-cosmology
       • scrapes-mcgee
       ...
```

### Push Scraped Content
```
You: scrape erowid for 10 DMT reports

McGee: [scrapes...]
       Done. 10 reports extracted.

You: push to Terence_McKenna_Corpus

McGee: Pushing to Terence_McKenna_Corpus...
       ✓ Created: data/scrape_20240330_143022.json
       https://github.com/merrypranxter/Terence_McKenna_Corpus/...
```

### Push as Markdown
```
You: push to ghost-erowid-cosmology as markdown

McGee: ✓ Created: data/scrape_20240330_143022.md
```

### Specify Custom Path
```
You: push to Terence_McKenna_Corpus at entities/dmt_reports.json

McGee: ✓ Created: entities/dmt_reports.json
```

---

## Natural Language Commands

McGee understands these:
- "push this to my McKenna corpus"
- "save to ghost-erowid-cosmology repo"
- "commit to Terence_McKenna_Corpus as markdown"
- "put this in my scrapes-mcgee repo"

---

## Example Workflow:

```
You: scrape erowid DMT experience vault for entity encounters, 
     get 20 reports, extract entity descriptions and dosages

McGee: Aight, hunting for machine elves...
       [scrapes 20 reports]
       Done. 20 reports with entities. 
       Top types: jesters (8), geometric beings (7), insectoid (5).

You: push to Terence_McKenna_Corpus as markdown in entities/ folder

McGee: Pushing to Terence_McKenna_Corpus...
       ✓ Created: entities/dmt_entities_20240330.md
       https://github.com/merrypranxter/Terence_McKenna_Corpus/blob/main/entities/dmt_entities_20240330.md
```

---

## Troubleshooting:

**"GitHub integration disabled"**
→ Add GITHUB_TOKEN to .env (see step 3 above)

**"Permission denied"**
→ Your token needs `repo` scope. Create a new token with that checked.

**"Repository not found"**
→ Check spelling. Use `list repos` to see exact names.

---

## What Gets Committed:

- **Filename**: Auto-generated with timestamp (or custom path)
- **Format**: JSON (default), Markdown, or YAML
- **Commit message**: "Scrapes McGee: Add [filename] [timestamp]"
- **Branch**: `main` (default)

---

## Security Note:

Your GitHub token is powerful — it can modify your repos. Keep your `.env` file safe and never commit it to git (it's in `.gitignore` already).

---

**Now restart McGee and try pushing something!** 🕷️⚡

```bash
python3 scrapes.py
```
