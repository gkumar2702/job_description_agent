#!/usr/bin/env python3
"""
Example script demonstrating structured logging output for question generation.
"""

import asyncio
from jd_agent.components.prompt_engine import PromptEngine
from jd_agent.utils.config import Config
from jd_agent.components.jd_parser import JobDescription


async def main():
    """Demonstrate structured logging for question generation."""
    
    # Create config with test API keys
    config = Config(
        OPENAI_API_KEY="test_key_123456789012345678901234567890",
        SERPAPI_KEY="test_serpapi_key_long_enough_for_validation",
        TEMPERATURE=0.3,
        TOP_P=0.9,
        MAX_TOKENS=2000
    )
    
    # Create sample job description
    jd = JobDescription(
        email_id="example_email_123",
        company="Example Corp",
        role="Software Engineer",
        location="San Francisco, CA",
        experience_years=2,
        skills=["Python", "JavaScript", "React", "Node.js"],
        content="We are looking for a Software Engineer to join our team...",
        confidence_score=0.9,
        parsing_metadata={"method": "example"}
    )
    
    # Create sample scraped content
    scraped_content = [
        {
            'source': 'GitHub',
            'title': 'Software Engineering Interview Questions',
            'content': 'This is a comprehensive guide to software engineering interview questions.',
            'relevance_score': 0.8
        }
    ]
    
    # Create PromptEngine
    engine = PromptEngine(config)
    
    print("=== Structured Logging Example ===")
    print("This will demonstrate JSON log events that can be forwarded to Loki/DataDog")
    print("Each log line will be a valid JSON object with structured data")
    print()
    
    # Generate questions (this will produce structured logs)
    print("Generating questions...")
    questions = await engine.generate_questions_async(jd, scraped_content)
    
    print(f"\nGenerated {len(questions)} questions")
    
    # Enhance questions (this will also produce structured logs)
    print("\nEnhancing questions...")
    enhanced_questions = await engine.enhance_questions_with_context_async(questions, scraped_content)
    
    print(f"Enhanced {len(enhanced_questions)} questions")
    
    print("\n=== Log Format Summary ===")
    print("The logs above show structured JSON events with the following format:")
    print()
    print("Question Generation Events:")
    print("- event: 'question_generation'")
    print("- role: Job role (e.g., 'Software Engineer')")
    print("- company: Company name (e.g., 'Example Corp')")
    print("- difficulty: Difficulty level ('easy', 'medium', 'hard', 'mixed')")
    print("- tokens_in: Estimated input tokens")
    print("- tokens_out: Estimated output tokens")
    print("- latency_ms: Generation time in milliseconds")
    print("- num_questions: Number of questions generated")
    print("- temperature: Temperature parameter used")
    print()
    print("Question Enhancement Events:")
    print("- event: 'question_enhancement'")
    print("- num_questions: Total number of questions processed")
    print("- enhanced_count: Number of questions successfully enhanced")
    print("- latency_ms: Enhancement time in milliseconds")
    print()
    print("These logs can be easily parsed and forwarded to:")
    print("- Loki for log aggregation and querying")
    print("- DataDog for monitoring and alerting")
    print("- Any JSON-compatible log management system")


if __name__ == "__main__":
    asyncio.run(main()) 