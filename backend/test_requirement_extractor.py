from app.ai.requirement_extractor import extract_requirements

result = extract_requirements(
    """
    I need a villa in Goa for four people.
    Check-in is 2026-11-10 and check-out is 2026-11-15.
    My budget is 8000 rupees per night.
    I need a swimming pool.
    """
)

print(result.model_dump(mode="json"))