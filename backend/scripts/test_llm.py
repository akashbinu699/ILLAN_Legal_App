import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.llm_service import llm_service

async def test_llm():
    description = "Objet : Demande de prise en charge d’un appel suite à signification de jugement\n\nMaître,\n\nJe me permets de vous contacter afin de solliciter votre assistance dans le cadre d’un appel à former contre un jugement récemment signifié."
    print(f"Testing with description: {description}")
    
    result = await llm_service.analyze_case_stage_and_benefits(description)
    print("\nAnalysis Result:")
    print(result)

if __name__ == "__main__":
    asyncio.run(test_llm())
