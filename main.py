import os
import uuid
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document, get_documents
from schemas import Conversation, Message, ChatRequest, ChatResponse

app = FastAPI(title="Peer Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Peer Assistant Backend is running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response

# Simple rule-based assistant for MVP
SYSTEM_PROMPT = (
    "Sei Peer, un assistente virtuale gentile, pratico e conciso. "
    "Rispondi in italiano, proponi passi chiari, e se utile fornisci elenchi puntati." 
)

def generate_reply(user_text: str) -> str:
    t = user_text.strip().lower()
    if not t:
        return "Dimmi pure come posso aiutarti."
    if any(k in t for k in ["ciao", "buongiorno", "buonasera", "hey"]):
        return "Ciao! Sono Peer. Come posso aiutarti oggi?"
    if "todo" in t or "attività" in t or "task" in t:
        return "Posso aiutarti a creare un elenco di attività. Scrivimi gli elementi e li salverò nella conversazione."
    if "aiuto" in t or "help" in t:
        return "Certo! Dimmi l'obiettivo e ti propongo i prossimi passi pratici."
    if "ricorda" in t or "promemoria" in t:
        return "Posso prendere nota nella chat, così puoi ritrovarla più tardi in questa conversazione."
    # default
    return (
        "Ecco come possiamo procedere:\n"
        "- Spiegami il tuo obiettivo o problema\n"
        "- Ti propongo i prossimi passi\n"
        "- Se vuoi, salvo appunti in questa conversazione"
    )

@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())

    # Ensure a conversation document exists (idempotent)
    conversations = get_documents("conversation", {"session_id": session_id}, limit=1) if db else []
    if not conversations and db:
        conv = Conversation(session_id=session_id, title="Chat con Peer")
        try:
            create_document("conversation", conv)
        except Exception:
            pass

    # Store user message
    user_msg = Message(session_id=session_id, role="user", text=req.user_text)
    try:
        if db:
            create_document("message", user_msg)
    except Exception:
        pass

    reply_text = f"{SYSTEM_PROMPT}\n\n" + generate_reply(req.user_text)

    asst_msg = Message(session_id=session_id, role="assistant", text=reply_text)
    try:
        if db:
            create_document("message", asst_msg)
    except Exception:
        pass

    # Return the latest 20 messages for the session
    messages: Optional[List[Message]] = None
    try:
        if db:
            docs = get_documents("message", {"session_id": session_id})
            # sort by created_at if available
            docs.sort(key=lambda d: d.get("created_at"), reverse=False)
            # coerce to Message-likes for response
            messages = [
                Message(session_id=d.get("session_id",""), role=d.get("role","user"), text=d.get("text",""))
                for d in docs[-20:]
            ]
    except Exception:
        messages = None

    return ChatResponse(session_id=session_id, reply=reply_text, messages=messages)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
