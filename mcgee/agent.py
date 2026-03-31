"""
Scrapes McGee — Conversational web scraping agent with personality.
"""
import google.generativeai as genai
from typing import Dict, List, Optional
import json
import os
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from scraper.core import LLMScraper, ScrapeConfig
from scraper.storage import ScrapeStorage
from mcgee.github_pusher import GitHubPusher


MCGEE_PERSONALITY = """You are Scrapes McGee, a scrappy web scraping bot with personality.

Your job: Help users scrape websites by understanding what they want in natural language, then building and executing scrape jobs. You can also push scraped content directly to their GitHub repositories.

Your personality:
- Scrappy, gets shit done, no-nonsense but friendly
- Show cool/interesting finds during scraping ("Yo, found a report about rotating hypercubes 👀")
- Give helpful suggestions ("Lots of these mention entity colors, want me to track that?")
- Casual updates on progress ("23 reports deep, 8 jesters found so far")
- Remember context from the conversation
- Witty but not annoying

Communication style:
- Blunt, direct, a bit chaotic
- Use emojis sparingly (only when actually cool)
- No corporate speak or excessive politeness
- Cuss if it fits ("This site's HTML is a fucking mess")

When user asks to scrape something:
1. Clarify what they want (if needed)
2. Build a scrape config
3. Execute the scrape
4. Show interesting finds along the way
5. Report results and ask what format they want OR if they want to push to GitHub

GitHub Integration:
- You can push scraped files directly to the user's GitHub repos
- When they say "push to [repo]" or "save to my [repo] repo", use the github_push function
- You can list their repos, create new repos, and commit files
- Default to pushing JSON for structured data, Markdown for readable reports

Available tools:
- start_scrape: Begin a scraping job
- show_progress: Update user on scraping progress
- export_results: Save results locally (json, markdown, yaml)
- github_push: Push file(s) to a GitHub repo
- github_list_repos: List user's GitHub repositories
- search_scraped: Search previously scraped content
- list_jobs: Show past scrape jobs

Examples of how you talk:
User: "scrape erowid for DMT entity encounters"
You: "Aight, hunting for machine elves on Erowid. Targeting experience vaults, looking for breakthrough + entity keywords. Want me to grab dosages and entity descriptions too?"

User: "yeah, and push it to my Terence_McKenna_Corpus repo"
You: "On it. Starting crawl... [shows progress] Found 12 so far. This one mentions 'autonomous hypercube beings with rotating faces' 👀 Keep going?"

User: "yeah get to 50"
You: "[continues] Done. 53 reports extracted. Top entities: jesters (23), geometric beings (18), insectoid intelligence (8). Pushing to Terence_McKenna_Corpus... ✓ Committed: data/erowid_dmt_entities.json"

User: "put that in markdown instead"
You: "✓ Converted to markdown. ✓ Pushed: reports/dmt_entity_encounters.md to Terence_McKenna_Corpus"
"""


class ScrapesMcGee:
    """Conversational web scraping agent."""
    
    def __init__(self, gemini_api_key: str):
        """Initialize Scrapes McGee with Gemini API."""
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel(
            'gemini-2.5-flash',
            system_instruction=MCGEE_PERSONALITY
        )
        
        self.scraper = LLMScraper(gemini_api_key)
        self.storage = ScrapeStorage()
        self.console = Console()
        self.chat_history = []
        self.current_job = None
        self.current_results = []
        
        # Initialize GitHub pusher (optional)
        try:
            self.github = GitHubPusher()
            self.github_enabled = True
        except (ValueError, Exception) as e:
            self.console.print(f"[yellow]GitHub integration disabled: {e}[/yellow]")
            self.github = None
            self.github_enabled = False
    
    async def init(self):
        """Initialize storage and any async setup."""
        await self.storage.init_db()
    
    def chat(self, user_message: str) -> str:
        """Send a message to McGee and get a response."""
        self.chat_history.append({"role": "user", "parts": [user_message]})
        
        # Build context about current state
        context = self._build_context()
        
        # Get response from Gemini
        response = self.model.generate_content(
            self.chat_history + [{"role": "user", "parts": [context]}]
        )
        
        mcgee_response = response.text
        self.chat_history.append({"role": "model", "parts": [mcgee_response]})
        
        # Check if McGee wants to trigger a scraping action
        self._parse_actions(mcgee_response)
        
        return mcgee_response
    
    def _build_context(self) -> str:
        """Build context about current scraping state."""
        context_parts = []
        
        if self.current_job:
            context_parts.append(f"Current job: {self.current_job}")
        
        if self.current_results:
            matched = sum(1 for r in self.current_results if r.matched)
            context_parts.append(f"Current results: {len(self.current_results)} pages, {matched} matched")
        
        if context_parts:
            return "Context: " + " | ".join(context_parts)
        return ""
    
    def _parse_actions(self, response: str):
        """Parse McGee's response for action triggers."""
        # Simple action detection - in a full version this would use function calling
        response_lower = response.lower()
        
        if "starting crawl" in response_lower or "starting scrape" in response_lower:
            self.console.print("[yellow]McGee is preparing to scrape...[/yellow]")
    
    async def execute_scrape(
        self,
        target_url: str,
        max_depth: int = 3,
        max_pages: Optional[int] = None,
        selection_prompt: Optional[str] = None,
        extraction_prompt: Optional[str] = None,
        job_name: Optional[str] = None
    ) -> List:
        """Execute a scraping job."""
        if not job_name:
            from datetime import datetime
            job_name = f"scrape_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.current_job = job_name
        
        config = ScrapeConfig(
            target_url=target_url,
            max_depth=max_depth,
            max_pages=max_pages,
            selection_prompt=selection_prompt,
            extraction_prompt=extraction_prompt
        )
        
        self.console.print(f"[bold green]Starting scrape job: {job_name}[/bold green]")
        self.console.print(f"Target: {target_url}")
        self.console.print(f"Max depth: {max_depth}, Max pages: {max_pages or 'unlimited'}")
        
        def progress_callback(page, total_scraped, queue_size):
            """Show progress updates."""
            self.console.print(f"[cyan]→ Scraped {page.url}[/cyan] (depth {page.depth})")
            if page.matched and page.extracted_content:
                # Show interesting finds
                content_str = json.dumps(page.extracted_content)[:200]
                self.console.print(f"  [green]✓ Match found: {content_str}...[/green]")
        
        # Run the scrape
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Scraping...", total=None)
            
            results = await self.scraper.crawl(config, progress_callback)
            progress.update(task, completed=True)
        
        # Save results
        for page in results:
            await self.storage.save_page(job_name, page)
        
        await self.storage.save_job(job_name, config.__dict__, results)
        
        self.current_results = results
        matched = sum(1 for r in results if r.matched)
        
        self.console.print(f"\n[bold green]✓ Scrape complete![/bold green]")
        self.console.print(f"Total pages: {len(results)}")
        self.console.print(f"Matched pages: {matched}")
        
        return results
    
    async def export_results(self, format: str = "json", output_path: Optional[str] = None):
        """Export current results to file."""
        if not self.current_results:
            self.console.print("[red]No results to export[/red]")
            return
        
        if not output_path:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"data/export_{timestamp}.{format}"
        
        if format == "json":
            self.storage.export_json(self.current_results, output_path)
        elif format == "markdown" or format == "md":
            self.storage.export_markdown(self.current_results, output_path)
        elif format == "yaml":
            self.storage.export_yaml(self.current_results, output_path)
        else:
            self.console.print(f"[red]Unknown format: {format}[/red]")
            return
        
        self.console.print(f"[green]✓ Exported to {output_path}[/green]")
        return output_path
    
    async def search(self, query: str, job_name: Optional[str] = None):
        """Search scraped content."""
        results = await self.storage.search_content(query, job_name)
        
        if not results:
            self.console.print(f"[yellow]No results found for '{query}'[/yellow]")
            return []
        
        self.console.print(f"[green]Found {len(results)} results for '{query}':[/green]")
        for i, result in enumerate(results[:10], 1):  # Show top 10
            self.console.print(f"{i}. {result['url']}")
            content_preview = result['content'][:150]
            self.console.print(f"   {content_preview}...")
        
        return results
    
    def list_github_repos(self):
        """List user's GitHub repositories."""
        if not self.github_enabled:
            self.console.print("[red]GitHub integration not enabled. Add GITHUB_TOKEN to .env[/red]")
            return []
        
        try:
            repos = self.github.list_repos()
            self.console.print(f"[green]Found {len(repos)} repositories:[/green]")
            for repo in repos:
                self.console.print(f"  • {repo}")
            return repos
        except Exception as e:
            self.console.print(f"[red]Error listing repos: {e}[/red]")
            return []
    
    async def push_to_github(
        self,
        repo_name: str,
        file_path: Optional[str] = None,
        content: Optional[str] = None,
        format: str = "json",
        commit_message: Optional[str] = None
    ):
        """
        Push scraped results to GitHub repository.
        
        Args:
            repo_name: Name of the repo (e.g., "Terence_McKenna_Corpus")
            file_path: Optional custom file path in repo
            content: Optional custom content (uses current_results if not provided)
            format: Format to export (json, markdown, yaml)
            commit_message: Optional custom commit message
        """
        if not self.github_enabled:
            self.console.print("[red]GitHub integration not enabled. Add GITHUB_TOKEN to .env[/red]")
            return
        
        if not self.current_results and not content:
            self.console.print("[red]No results to push. Run a scrape first.[/red]")
            return
        
        try:
            # Generate content if not provided
            if not content:
                import tempfile
                from pathlib import Path
                
                # Export to temp file
                with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{format}', delete=False) as tmp:
                    tmp_path = tmp.name
                
                if format == "json":
                    self.storage.export_json(self.current_results, tmp_path)
                elif format == "markdown" or format == "md":
                    self.storage.export_markdown(self.current_results, tmp_path)
                elif format == "yaml":
                    self.storage.export_yaml(self.current_results, tmp_path)
                
                # Read content
                with open(tmp_path, 'r') as f:
                    content = f.read()
                
                # Clean up
                Path(tmp_path).unlink()
            
            # Default file path if not provided
            if not file_path:
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                job_name = self.current_job or "scrape"
                file_path = f"data/{job_name}_{timestamp}.{format}"
            
            # Push to GitHub
            self.console.print(f"[yellow]Pushing to {repo_name}...[/yellow]")
            action, url = self.github.push_file(
                repo_name=repo_name,
                file_path=file_path,
                content=content,
                commit_message=commit_message
            )
            
            self.console.print(f"[green]✓ {action}: {file_path}[/green]")
            self.console.print(f"[cyan]{url}[/cyan]")
            
            return url
        
        except Exception as e:
            self.console.print(f"[red]Error pushing to GitHub: {e}[/red]")
            return None

