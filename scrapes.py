#!/usr/bin/env python3
"""
Scrapes McGee - Conversational web scraper

Talk to McGee, tell him what to scrape, and he'll get it done.
"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from mcgee.agent import ScrapesMcGee


async def main():
    """Main chat interface with Scrapes McGee."""
    load_dotenv()
    
    console = Console()
    
    # Welcome banner
    console.print(Panel.fit(
        "[bold cyan]Scrapes McGee[/bold cyan]\n"
        "Your scrappy web scraping buddy\n\n"
        "[dim]Commands: 'quit' to exit, 'help' for tips[/dim]",
        border_style="cyan"
    ))
    
    # Get API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        console.print("[red]Error: GEMINI_API_KEY not found in environment[/red]")
        console.print("Create a .env file with: GEMINI_API_KEY=your_key_here")
        return
    
    # Initialize McGee
    console.print("[yellow]Initializing Scrapes McGee...[/yellow]")
    mcgee = ScrapesMcGee(api_key)
    await mcgee.init()
    console.print("[green]✓ McGee is ready![/green]\n")
    
    # Chat loop
    while True:
        try:
            # Get user input
            user_input = console.input("[bold blue]You:[/bold blue] ")
            
            if not user_input.strip():
                continue
            
            # Handle special commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                console.print("[yellow]Later! 👋[/yellow]")
                break
            
            if user_input.lower() == 'help':
                show_help(console)
                continue
            
            # Parse for direct scrape commands
            if user_input.lower().startswith('scrape '):
                # Extract URL and run scrape
                parts = user_input.split()
                if len(parts) >= 2:
                    url = parts[1]
                    console.print(f"[cyan]McGee:[/cyan] Aight, scraping {url}...")
                    
                    # Simple extraction for demo
                    await mcgee.execute_scrape(
                        target_url=url,
                        max_depth=2,
                        max_pages=10,
                        extraction_prompt="Extract the main content, title, and any interesting data."
                    )
                    
                    console.print(f"[cyan]McGee:[/cyan] Done! Want me to export these? (json/markdown/yaml)")
                    continue
            
            if user_input.lower().startswith('export '):
                format = user_input.split()[1] if len(user_input.split()) > 1 else 'json'
                await mcgee.export_results(format=format)
                continue
            
            # GitHub commands
            if user_input.lower() == 'list repos':
                mcgee.list_github_repos()
                continue
            
            if user_input.lower().startswith('push to '):
                # Extract repo name
                parts = user_input.split()
                if len(parts) >= 3:
                    repo_name = parts[2]
                    format = 'json'  # default
                    if 'markdown' in user_input.lower() or 'md' in user_input.lower():
                        format = 'markdown'
                    elif 'yaml' in user_input.lower():
                        format = 'yaml'
                    
                    await mcgee.push_to_github(repo_name, format=format)
                    continue
            
            # Send to McGee's chat
            console.print("[cyan]McGee:[/cyan] ", end="")
            response = mcgee.chat(user_input)
            
            # Print McGee's response
            console.print(response)
            console.print()
        
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted. Type 'quit' to exit or continue chatting.[/yellow]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


def show_help(console: Console):
    """Show help information."""
    help_text = """
# Scrapes McGee - Quick Guide

## Chat Commands
- Just talk to McGee naturally: "scrape erowid for DMT reports"
- `scrape <url>` - Quick scrape of a URL
- `export <format>` - Export results (json, markdown, yaml)
- `list repos` - Show your GitHub repositories
- `push to <repo>` - Push results to a GitHub repo
- `help` - Show this help
- `quit` - Exit

## Example Conversations
**You:** scrape erowid for DMT entity encounters, grab about 50 reports  
**McGee:** Aight, hunting for machine elves...

**You:** only the weird ones, skip boring trip reports  
**McGee:** Got it, filtering for high-weirdness...

**You:** push to Terence_McKenna_Corpus as markdown  
**McGee:** ✓ Pushed: data/dmt_entities_20240330.md

## GitHub Integration
Set GITHUB_TOKEN in .env to enable pushing to repos.
Get token: https://github.com/settings/tokens

## Tips
- Be specific about what you want extracted
- McGee will suggest refinements as he scrapes
- He remembers context, so you can refine on the fly
- Check `data/` folder for exports and database
"""
    console.print(Panel(Markdown(help_text), title="Help", border_style="cyan"))


if __name__ == "__main__":
    asyncio.run(main())
