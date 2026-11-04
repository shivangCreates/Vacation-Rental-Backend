
from threading import Lock
from uuid import uuid4

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

MAX_HISTORY_MESSAGES = 20


class SessionStore:
    def __init__(self):
        self._sessions: dict[str, list[BaseMessage]] = {}
        self._lock = Lock()

    def create_session(self) -> str:
        """Create a new conversation with a unique ID."""
        session_id = str(uuid4())

        with self._lock:
            self._sessions[session_id] = []

        return session_id

    def session_exists(self, session_id: str) -> bool:
        """Check whether a conversation exists."""
        with self._lock:
            return session_id in self._sessions

    def get_history(self, session_id: str) -> list[BaseMessage]:
        """Retrieve messages from one conversation."""
        with self._lock:
            return list(self._sessions.get(session_id, []))

    def add_exchange(
        self,
        session_id: str,
        user_message: str,
        assistant_reply: str,
    ) -> None:
        """Save the user's message and the AI's reply."""
        with self._lock:
            if session_id not in self._sessions:
                raise ValueError("Session does not exist.")

            history = self._sessions[session_id]
            history.extend([
                HumanMessage(content=user_message),
                AIMessage(content=assistant_reply),
            ])

            self._sessions[session_id] = history[-MAX_HISTORY_MESSAGES:]

    def clear_history(self, session_id: str) -> bool:
        """Clear history while keeping the session available."""
        with self._lock:
            if session_id not in self._sessions:
                return False

            self._sessions[session_id] = []
            return True

    def delete_session(self, session_id: str) -> bool:
        """Delete the entire session."""
        with self._lock:
            return self._sessions.pop(session_id, None) is not None


session_store = SessionStore()
