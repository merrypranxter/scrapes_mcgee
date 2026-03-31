#!/usr/bin/env python3
"""
Example: Programmatic usage of Scrapes McGee

This shows how to use McGee's scraper directly without the chat interface.
"""
import asyncio
import os
from dotenv import load_dotenv
from mcgee.agent import ScrapesMcGee


async def scrape_erowid_entities():
    """Example: Scrape Erowid for DMT entity encounters."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    
    # Initialize McGee
    mcgee = ScrapesMcGee(api_key)
    await mcgee.init()
    
    # Run the scrape
    results = await mcgee.execute_scrape(
        target_url="https://erowid.org/experiences/subs/exp_DMT.shtml",
        max_depth=2,
        max_pages=10,  # Just 10 for this example
        selection_prompt="""
            Only follow links to DMT experience reports that mention:
            - Entities, beings, or alien contact
            - Machine elves, jesters, or autonomous beings
            - Breakthrough experiences with entity interaction
        """,
        extraction_prompt="""
            Extract as JSON:
            {
                "title": "report title",
                "dosage": "amount in mg if mentioned",
                "entity_description": "description of entities encountered",
                "entity_type": "jesters/geometric/insectoid/other",
                "key_quotes": ["notable quotes about entities"]
            }
        """,
        job_name="erowid_dmt_entities_example"
    )
    
    # Export results
    output_path = await mcgee.export_results(format="json")
    print(f"\n✓ Results saved to: {output_path}")
    
    # Show summary
    matched = sum(1 for r in results if r.matched)
    print(f"\nSummary:")
    print(f"  Total pages scraped: {len(results)}")
    print(f"  Matching reports: {matched}")
    
    if matched > 0:
        print(f"\nFirst match example:")
        for result in results:
            if result.matched and result.extracted_content:
                print(f"  URL: {result.url}")
                print(f"  Content: {result.extracted_content}")
                break


if __name__ == "__main__":
    asyncio.run(scrape_erowid_entities())
