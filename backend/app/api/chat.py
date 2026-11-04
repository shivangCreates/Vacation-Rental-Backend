
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.property_service import search_properties
from app.services.semantic_search_service import search_similar_documents

from ..ai.requirement_extractor import extract_requirements
from ..ai.chat_service import generate_reply

from ..schemas.chat import ChatRequest, ChatResponse

from ..services.session_store import session_store


logger = logging.getLogger(__name__)

router = APIRouter(tags=["Chat"])


@router.post("/sessions", status_code=201)
def create_session():

    session_id = session_store.create_session()

    return {
        "session_id": session_id,
        "message": "Conversation created successfully.",
    }


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
) -> ChatResponse:

    # 1. Verify that the session exists.
    if not session_store.session_exists(request.session_id):
        raise HTTPException(
            status_code=404,
            detail="Session not found. Create a session first.",
        )

    try:
        # 2. Retrieve conversation history.
        history = session_store.get_history(request.session_id)

        # 3. Extract vacation requirements.
        requirements = extract_requirements(
            message=request.message,
            history=history,
        )

        has_complete_date_range = (
            requirements.check_in is not None
            and requirements.check_out is not None
        )
        has_partial_date_range = (
            (requirements.check_in is None) != (requirements.check_out is None)
        )

        # 4. Search matching properties in PostgreSQL.
        properties = search_properties(
            db=db,
            destination=requirements.destination,
            guests=requirements.guests,
            budget_per_night=requirements.budget_per_night,
            property_type=requirements.property_type,
            amenities=requirements.amenities,
            check_in=requirements.check_in if has_complete_date_range else None,
            check_out=requirements.check_out if has_complete_date_range else None,
        )

        # 5. Generate AI response.
        candidate_property_ids = [property.id for property in properties]

        retrieved_documents = search_similar_documents(
         db=db,
         query=request.message,
         op_k=5,
         property_ids=candidate_property_ids,
         )

        retrieved_context = "\n\n".join(
         document.content for document in retrieved_documents
          )
        availability_note = None
        if has_partial_date_range:
            missing_date = (
                "check-in"
                if requirements.check_in is None
                else "check-out"
            )
            availability_note = (
                "The guest has provided only one travel date. These properties "
                "were not checked for date availability. Ask for the missing "
                f"{missing_date} date and do not claim that any property is available."
            )

        reply = generate_reply(
            message=request.message,
            history=history,
            properties=properties,
            availability_note=availability_note,
            retrieved_context=retrieved_context,
        )

        # 6. Save conversation.
        session_store.add_exchange(
            session_id=request.session_id,
            user_message=request.message,
            assistant_reply=reply,
        )

        # 7. Return response.
        return ChatResponse(
            session_id=request.session_id,
            reply=reply,
            requirements=requirements,
            properties=properties
        )

    except Exception:
        logger.exception("Failed to process chat request")

        raise HTTPException(
            status_code=503,
            detail="The AI assistant is temporarily unavailable.",
        )


@router.delete("/chat/{session_id}/history")
def clear_chat_history(session_id: str):

    cleared = session_store.clear_history(session_id)

    return {
        "session_id": session_id,
        "cleared": cleared,
        "message": (
            "Conversation history cleared."
            if cleared
            else "No conversation history found."
        ),
    }
