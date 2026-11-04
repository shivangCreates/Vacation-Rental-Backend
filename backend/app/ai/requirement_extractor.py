
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from ..schemas.vacation import VacationRequirements


model = ChatOllama(
    model="llama3.2:3b",
    temperature=0,
)

extractor = model.with_structured_output(
    VacationRequirements,
    method="json_schema",
)

EXTRACTION_PROMPT = """
You are a vacation rental information extraction system.

Read the user's message and extract these fields:
- destination
- check_in
- check_out
- guests
- budget_per_night
- property_type
- amenities

Rules:
1. Copy only information provided by the user.
2. If a value is missing, return null.
3. If no amenities are mentioned, return an empty list.
4. Return dates in YYYY-MM-DD format.
5. Return the property type separately from the destination.

Example input:
I need a villa in Goa for four people from
2026-11-10 to 2026-11-15. Budget is 8000 rupees
per night. I need a swimming pool.
If the guest says "villa in Goa", extract:
  destination = "Goa"
  property_type = "villa"
Always extract an explicitly stated property type.

Expected fields:
destination = Goa
check_in = 2026-11-10
check_out = 2026-11-15
guests = 4
budget_per_night = 8000
property_type = villa
amenities = ["swimming pool"]
"""


def extract_requirements(
    message: str,
    history: list | None = None,
) -> VacationRequirements:
    messages = [
        SystemMessage(content=EXTRACTION_PROMPT),
        *(history or []),
        HumanMessage(
            content=(
                "Extract the current vacation requirements from this "
                f"latest message:\n{message}"
            )
        ),
    ]

    return extractor.invoke(messages)
