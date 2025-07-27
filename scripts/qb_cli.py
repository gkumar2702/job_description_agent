#!/usr/bin/env python3
"""
QuestionBank CLI using Typer.
"""

import json
import typer
from pathlib import Path
from typing import List, Optional
import asyncio

# Add the parent directory to the path so we can import jd_agent
import sys
sys.path.append(str(Path(__file__).parent.parent))

from jd_agent.components.question_bank import QuestionBank
from jd_agent.components.jd_parser import JobDescription
from jd_agent.components.scoring_strategies import HeuristicScorer, EmbeddingScorer, HybridScorer
from jd_agent.utils.config import Config

app = typer.Typer(help="QuestionBank CLI for managing interview questions")


def load_questions(json_file: Path) -> List[dict]:
    """Load questions from JSON file."""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different JSON structures
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'questions' in data:
            return data['questions']
        else:
            typer.echo(f"Error: Invalid JSON structure in {json_file}")
            raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error loading {json_file}: {e}")
        raise typer.Exit(1)


def load_job_description(jd_file: Path) -> JobDescription:
    """Load job description from JSON file."""
    try:
        with open(jd_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Create JobDescription from JSON data
        return JobDescription(**data)
    except Exception as e:
        typer.echo(f"Error loading job description from {jd_file}: {e}")
        raise typer.Exit(1)


@app.command()
def dedup(
    json_file: Path = typer.Argument(..., help="JSON file containing questions"),
    output_file: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file (default: overwrite input)")
):
    """Remove duplicate questions from a JSON file."""
    typer.echo(f"Loading questions from {json_file}...")
    questions = load_questions(json_file)
    typer.echo(f"Loaded {len(questions)} questions")
    
    # Initialize QuestionBank
    config = Config()
    qb = QuestionBank(config)
    qb.add_questions(questions)
    
    # Deduplicate
    typer.echo("Deduplicating questions...")
    deduplicated = qb.deduplicate_questions()
    typer.echo(f"Deduplicated to {len(deduplicated)} questions")
    
    # Save results
    output_path = output_file or json_file
    result_data = {
        'metadata': {
            'original_count': len(questions),
            'deduplicated_count': len(deduplicated),
            'deduplicated_at': typer.get_current_datetime().isoformat()
        },
        'questions': [q.model_dump() for q in deduplicated]
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False)
    
    typer.echo(f"Saved deduplicated questions to {output_path}")


@app.command()
def score(
    json_file: Path = typer.Argument(..., help="JSON file containing questions"),
    jd_file: Path = typer.Argument(..., help="JSON file containing job description"),
    output_file: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file (default: overwrite input)"),
    scorer: str = typer.Option("heuristic", "--scorer", "-s", help="Scoring strategy: heuristic, embedding, hybrid"),
    embedding_weight: float = typer.Option(0.6, "--embedding-weight", help="Weight for embedding similarity (0-1)"),
    heuristic_weight: float = typer.Option(0.4, "--heuristic-weight", help="Weight for heuristic scoring (0-1)")
):
    """Score questions based on relevance to job description."""
    typer.echo(f"Loading questions from {json_file}...")
    questions = load_questions(json_file)
    typer.echo(f"Loaded {len(questions)} questions")
    
    typer.echo(f"Loading job description from {jd_file}...")
    jd = load_job_description(jd_file)
    typer.echo(f"Loaded job description for {jd.role} at {jd.company}")
    
    # Initialize QuestionBank with scoring strategy
    config = Config()
    
    if scorer == "heuristic":
        scoring_strategy = HeuristicScorer()
    elif scorer == "embedding":
        scoring_strategy = EmbeddingScorer(embedding_weight, heuristic_weight)
    elif scorer == "hybrid":
        scoring_strategy = HybridScorer(embedding_weight, heuristic_weight)
    else:
        typer.echo(f"Error: Unknown scoring strategy '{scorer}'")
        raise typer.Exit(1)
    
    qb = QuestionBank(config, scorer=scoring_strategy)
    qb.add_questions(questions)
    
    # Score questions
    typer.echo("Scoring questions...")
    scored_questions = qb.score_questions(jd)
    typer.echo(f"Scored {len(scored_questions)} questions")
    
    # Save results
    output_path = output_file or json_file
    result_data = {
        'metadata': {
            'job_description': {
                'company': jd.company,
                'role': jd.role,
                'location': jd.location,
                'experience_years': jd.experience_years,
                'skills': jd.skills
            },
            'scoring': {
                'strategy': scorer,
                'embedding_weight': embedding_weight,
                'heuristic_weight': heuristic_weight,
                'scored_at': typer.get_current_datetime().isoformat()
            },
            'total_questions': len(scored_questions)
        },
        'questions': scored_questions
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False)
    
    typer.echo(f"Saved scored questions to {output_path}")
    
    # Show top questions
    typer.echo("\nTop 5 questions by relevance score:")
    for i, q in enumerate(scored_questions[:5], 1):
        score = q.get('relevance_score', 0)
        typer.echo(f"{i}. [{score:.3f}] {q.get('question', '')[:80]}...")


@app.command()
def export(
    json_file: Path = typer.Argument(..., help="JSON file containing questions"),
    jd_file: Path = typer.Argument(..., help="JSON file containing job description"),
    formats: str = typer.Option("md,csv,xlsx", "--formats", "-f", help="Export formats (comma-separated)"),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir", "-o", help="Output directory")
):
    """Export questions in various formats."""
    typer.echo(f"Loading questions from {json_file}...")
    questions = load_questions(json_file)
    typer.echo(f"Loaded {len(questions)} questions")
    
    typer.echo(f"Loading job description from {jd_file}...")
    jd = load_job_description(jd_file)
    typer.echo(f"Loaded job description for {jd.role} at {jd.company}")
    
    # Parse formats
    format_list = [f.strip() for f in formats.split(',')]
    valid_formats = ['markdown', 'csv', 'json', 'xlsx', 'md']
    
    # Map 'md' to 'markdown'
    format_list = ['markdown' if f == 'md' else f for f in format_list]
    
    for fmt in format_list:
        if fmt not in valid_formats:
            typer.echo(f"Error: Unknown format '{fmt}'. Valid formats: {', '.join(valid_formats)}")
            raise typer.Exit(1)
    
    # Initialize QuestionBank
    config = Config()
    if output_dir:
        config.EXPORT_DIR = str(output_dir)
    
    qb = QuestionBank(config)
    
    # Export questions
    typer.echo(f"Exporting questions in formats: {', '.join(format_list)}...")
    
    async def export_async():
        return await qb.export_questions_async(jd, questions, format_list)
    
    try:
        export_files = asyncio.run(export_async())
        
        typer.echo("\nExport completed successfully!")
        for format_type, file_path in export_files.items():
            typer.echo(f"  {format_type.upper()}: {file_path}")
            
    except Exception as e:
        typer.echo(f"Error during export: {e}")
        raise typer.Exit(1)


@app.command()
def stats(
    json_file: Path = typer.Argument(..., help="JSON file containing questions")
):
    """Show statistics about questions."""
    typer.echo(f"Loading questions from {json_file}...")
    questions = load_questions(json_file)
    typer.echo(f"Loaded {len(questions)} questions")
    
    # Initialize QuestionBank
    config = Config()
    qb = QuestionBank(config)
    qb.add_questions(questions)
    
    # Get statistics
    stats = qb.get_question_statistics()
    
    typer.echo("\nQuestion Statistics:")
    typer.echo(f"  Total Questions: {stats.get('total_questions', 0)}")
    
    if 'by_difficulty' in stats:
        typer.echo("\n  By Difficulty:")
        for difficulty, count in stats['by_difficulty'].items():
            typer.echo(f"    {difficulty.title()}: {count}")
    
    if 'by_category' in stats:
        typer.echo("\n  By Category:")
        for category, count in stats['by_category'].items():
            typer.echo(f"    {category}: {count}")
    
    if 'avg_relevance_score' in stats:
        typer.echo(f"\n  Average Relevance Score: {stats['avg_relevance_score']:.3f}")


if __name__ == "__main__":
    app() 