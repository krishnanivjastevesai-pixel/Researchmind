"""
Research Pipeline Module
Orchestrates the multi-agent research workflow:
1. Search Agent - Finds information
2. Reader Agent - Scrapes detailed content
3. Writer Chain - Drafts report
4. Critic Chain - Reviews and scores

Enhanced with validation, error handling, and progress tracking.
"""

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from agents import build_reader_agent, build_search_agent, writer_chain, critic_chain
from utils import validate_topic, save_report, logger

console = Console()


def run_research_pipeline(topic: str, progress_callback=None) -> dict:
    """
    Execute the complete research pipeline with validation and error handling.
    
    Args:
        topic: The research topic to investigate
        progress_callback: Optional callback function for progress updates
        
    Returns:
        Dictionary containing all pipeline results
        
    Raises:
        ValueError: If topic validation fails
        Exception: If pipeline execution fails
    """
    # Validate topic
    is_valid, error_msg = validate_topic(topic)
    if not is_valid:
        logger.error(f"Topic validation failed: {error_msg}")
        raise ValueError(error_msg)
    
    logger.info(f"Starting research pipeline for topic: {topic}")
    state = {"topic": topic}
    
    try:
        # ============================================
        # Step 1: Search Agent (25% progress)
        # ============================================
        console.print(Panel.fit(
            "[bold cyan]Step 1: Search Agent[/bold cyan]\n"
            "Finding recent, reliable information...",
            border_style="cyan"
        ))
        
        if progress_callback:
            progress_callback(25, "Searching the web...")
        
        search_agent = build_search_agent()
        search_result = search_agent.invoke({
            "input": f"Find recent, reliable and detailed information about: {topic}"
        })
        state["search_results"] = search_result['output']
        
        console.print("[green]✓[/green] Search completed\n")
        console.print(f"[dim]{state['search_results'][:500]}...[/dim]\n")
        logger.info("Search agent completed successfully")

        # ============================================
        # Step 2: Reader Agent (50% progress)
        # ============================================
        console.print(Panel.fit(
            "[bold magenta]Step 2: Reader Agent[/bold magenta]\n"
            "Scraping top resources for detailed content...",
            border_style="magenta"
        ))
        
        if progress_callback:
            progress_callback(50, "Scraping web content...")
        
        reader_agent = build_reader_agent()
        reader_result = reader_agent.invoke({
            "input": (
                f"Based on the following search results about '{topic}', "
                f"pick the most relevant URL and scrape it for deeper content.\n\n"
                f"Search Results:\n{state['search_results'][:800]}"
            )
        })
        
        state['scraped_content'] = reader_result['output']
        
        console.print("[green]✓[/green] Content scraped\n")
        console.print(f"[dim]{state['scraped_content'][:500]}...[/dim]\n")
        logger.info("Reader agent completed successfully")

        # ============================================
        # Step 3: Writer Chain (75% progress)
        # ============================================
        console.print(Panel.fit(
            "[bold yellow]Step 3: Writer Chain[/bold yellow]\n"
            "Drafting comprehensive research report...",
            border_style="yellow"
        ))
        
        if progress_callback:
            progress_callback(75, "Writing the report...")
        
        research_combined = (
            f"SEARCH RESULTS:\n{state['search_results']}\n\n"
            f"DETAILED SCRAPED CONTENT:\n{state['scraped_content']}"
        )
        
        state["report"] = writer_chain.invoke({
            "topic": topic,
            "research": research_combined
        })
        
        console.print("[green]✓[/green] Report drafted\n")
        console.print(Panel(state['report'][:800] + "...", title="Report Preview", border_style="yellow"))
        logger.info("Writer chain completed successfully")

        # ============================================
        # Step 4: Critic Chain (90% progress)
        # ============================================
        console.print(Panel.fit(
            "[bold red]Step 4: Critic Chain[/bold red]\n"
            "Reviewing and scoring the report...",
            border_style="red"
        ))
        
        if progress_callback:
            progress_callback(90, "Reviewing the report...")
        
        state["feedback"] = critic_chain.invoke({
            "report": state['report']
        })
        
        console.print("[green]✓[/green] Review completed\n")
        console.print(Panel(state['feedback'], title="Critic Feedback", border_style="red"))
        logger.info("Critic chain completed successfully")
        
        # ============================================
        # Complete (100% progress)
        # ============================================
        if progress_callback:
            progress_callback(100, "Pipeline completed!")
        
        console.print("\n[bold green]✓ Pipeline completed successfully![/bold green]\n")
        logger.info(f"Research pipeline completed for topic: {topic}")
        
        return state
    
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
        console.print(f"\n[bold red]✗ Pipeline failed: {str(e)}[/bold red]\n")
        raise


if __name__ == "__main__":
    console.print(Panel.fit(
        "[bold cyan]ResearchMind AI Pipeline[/bold cyan]\n"
        "Multi-agent research system powered by Groq",
        border_style="cyan"
    ))
    
    topic = console.input("\n[bold yellow]Enter a research topic:[/bold yellow] ")
    
    if topic.strip():
        try:
            results = run_research_pipeline(topic)
            
            # Save report to file
            filepath = save_report(
                topic=results['topic'],
                report=results['report'],
                feedback=results['feedback'],
                format='md'
            )
            
            console.print(f"\n[green]✓[/green] Report saved to: [bold]{filepath}[/bold]")
            
            # Show statistics
            from utils import get_cache_stats, get_reports_stats
            cache_stats = get_cache_stats()
            reports_stats = get_reports_stats()
            
            console.print(f"\n[dim]Cache: {cache_stats['total_files']} files ({cache_stats['total_size_mb']} MB)[/dim]")
            console.print(f"[dim]Reports: {reports_stats['total_reports']} files ({reports_stats['total_size_mb']} MB)[/dim]")
        
        except ValueError as e:
            console.print(f"[red]Validation Error:[/red] {e}")
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            logger.error(f"Pipeline execution failed: {e}", exc_info=True)
    else:
        console.print("[red]Error:[/red] Please enter a valid topic.")

