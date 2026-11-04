
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_ollama import ChatOllama

model = ChatOllama(
    model="llama3.2:3b",
    temperature=0.2,
)

SYSTEM_PROMPT = """
You are a helpful Vacation Rental AI Assistant.

Help guests find suitable vacation rental properties.

Use only the property information provided to you.
Never invent property names, prices, availability, or bookings.

Use SQL property details for exact facts such as price, destination,
guest capacity, amenities, and availability.

Use retrieved RAG context only to answer descriptive questions.
Do not treat retrieved context as proof of current availability or price.

If matching properties are available, explain their details clearly.
If no properties are available, politely inform the guest.

Ask follow-up questions when important requirements are missing.
"""


def generate_reply(
    message: str,
    history: list[BaseMessage] | None = None,
    properties: list | None = None,
    availability_note: str | None = None,
    retrieved_context: str | None = None,
) -> str:

    property_context = ""

    if properties:
        property_context = "\nSQL-matched properties:\n"

        for property in properties:
            property_context += f"""
            Property Name: {property.name}
            Destination: {property.destination}
            Type: {property.property_type}
            Price per Night: {property.price_per_night}
            Maximum Guests: {property.max_guests}
            Swimming Pool: {property.has_pool}
            Amenities: {", ".join(property.amenities) or "Not specified"}
            Description: {property.description}
            """

    else:
        property_context = (
            "No properties matched the structured SQL filters."
        )

    if retrieved_context:
        property_context += f"""

        Retrieved descriptive context from the property knowledge base:
        {retrieved_context}
        """

    if availability_note:
        property_context += f"\n{availability_note}"

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        *(history or []),
        HumanMessage(
            content=f"""
            Guest Message: {message}

            {property_context}

            Respond using the available property information.
            """
        ),
    ]

    response = model.invoke(messages)

    return str(response.content)
