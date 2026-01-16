"""Sample queries for testing the A2A RAG agent."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent.a2a_agent import A2ARAGAgent
from config.settings import get_settings


async def main():
    """Run sample queries."""
    
    # Initialize settings and agent
    settings = get_settings()
    agent = A2ARAGAgent(settings)
    
    print("=== A2A RAG Agent - Sample Queries ===\n")
    
    # Sample queries
    queries = [
        "What is the Agent-to-Agent protocol?",
        "How does the Model Context Protocol work?",
        "Explain the architecture of IBM Orchestrate",
        "What are the key features of MCP?",
        "How do agents communicate in the A2A protocol?",
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n{'='*60}")
        print(f"Query {i}: {query}")
        print('='*60)
        
        try:
            # Process query
            result = await agent.process_query(query)
            
            # Display results
            print(f"\nAnswer:\n{result['response']}\n")
            
            if result.get('sources'):
                print(f"Sources ({len(result['sources'])}):")
                for j, source in enumerate(result['sources'], 1):
                    print(f"  {j}. {source['source']} (score: {source['score']:.3f})")
            
            print()
            
        except Exception as e:
            print(f"Error: {e}\n")
    
    # Clean up
    await agent.close()
    print("\n=== Sample queries completed ===")


if __name__ == "__main__":
    asyncio.run(main())

# Made with Bob
