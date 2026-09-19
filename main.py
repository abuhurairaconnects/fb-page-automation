import asyncio
import logging
from fastapi import FastAPI, Request, Response, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from config import settings
from services.facebook_service import facebook_service
from services.sheets_service import sheets_service
from services.ai_service import ai_service

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("FBAutomation")

app = FastAPI(
    title="Facebook Page AI Automation Bot",
    description="Automated comments, private replies, Messenger chatbot & Google Sheets order management",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Facebook Page AI Automation",
        "version": "1.0.0",
        "products_count": len(sheets_service.get_products())
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "google_sheet_connected": len(sheets_service.get_products()) > 0,
        "facebook_token_set": settings.PAGE_ACCESS_TOKEN != "placeholder_token",
        "gemini_api_key_set": settings.GEMINI_API_KEY is not None
    }

@app.get("/webhook")
async def verify_webhook(request: Request):
    """
    Meta Webhook Verification Endpoint.
    Meta makes a GET request here when subscribing the webhook in the App Dashboard.
    """
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    logger.info(f"[Webhook Verify] mode={mode}, token={token}")

    if mode and token:
        if mode == "subscribe" and token == settings.VERIFY_TOKEN:
            logger.info("[Webhook Verify] ভেরিফিকেশন সফল হয়েছে!")
            return PlainTextResponse(content=challenge, status_code=200)
        else:
            logger.warning("[Webhook Verify] ভেরিফাই টোকেন মিলেনি!")
            raise HTTPException(status_code=403, detail="Verification token mismatch")

    return PlainTextResponse(content="Bad Request", status_code=400)


async def process_messenger_event(sender_id: str, message_text: str, mid: str):
    """Processes an incoming Messenger chat message in the background."""
    if facebook_service._is_already_processed(mid):
        return

    logger.info(f"[Messenger Message Received] From {sender_id}: {message_text}")
    bot_reply = await ai_service.handle_messenger_chat(sender_id, message_text)
    logger.info(f"[Messenger Bot Reply] To {sender_id}: {bot_reply}")
    await facebook_service.send_message(sender_id, bot_reply)


async def process_comment_event(change_value: dict):
    """Processes an incoming Facebook post comment in the background."""
    item = change_value.get("item")
    verb = change_value.get("verb")
    
    if item != "comment" or verb != "add":
        return

    comment_id = change_value.get("comment_id")
    comment_text = change_value.get("message", "")
    from_user = change_value.get("from", {})
    user_id = from_user.get("id")

    # Ignore comments made by the page itself
    if settings.PAGE_ID and str(user_id) == str(settings.PAGE_ID):
        return

    # Check deduplication
    if facebook_service._is_already_processed(comment_id):
        return

    logger.info(f"[New Comment on Post] ID: {comment_id} | User: {user_id} | Text: '{comment_text}'")

    # 1. Analyze with AI
    public_reply, send_inbox, inbox_message = await ai_service.analyze_and_reply_comment(comment_text)

    # 2. Reply publicly to comment
    if public_reply:
        await facebook_service.reply_to_comment(comment_id, public_reply)

    # 3. Send private reply into user's Messenger inbox if requested
    if send_inbox and inbox_message:
        await facebook_service.send_private_reply(comment_id, inbox_message)


@app.post("/webhook")
async def webhook_handler(request: Request, background_tasks: BackgroundTasks):
    """
    Meta Webhook Event Intake Endpoint.
    Meta delivers events (new messages, comments) via POST here.
    """
    try:
        data = await request.json()
    except Exception:
        return Response(content="INVALID_JSON", status_code=400)

    object_type = data.get("object")

    # 1. Page events (Messages or Feed/Comments)
    if object_type == "page":
        for entry in data.get("entry", []):
            # Check for Messenger chat messages
            if "messaging" in entry:
                for event in entry["messaging"]:
                    sender_id = event.get("sender", {}).get("id")
                    message = event.get("message", {})
                    postback = event.get("postback")

                    # Ignore echo messages sent by the page itself
                    if message.get("is_echo"):
                        continue

                    # Don't respond to ourselves if sender is page
                    if settings.PAGE_ID and str(sender_id) == str(settings.PAGE_ID):
                        continue

                    text = message.get("text")
                    mid = message.get("mid", "")

                    # Handle Quick Replies
                    if message.get("quick_reply"):
                        text = message["quick_reply"].get("payload") or text

                    # Handle Postback buttons (Get Started, menu buttons)
                    if postback:
                        text = postback.get("payload") or postback.get("title") or "Get Started"
                        if not mid:
                            mid = f"postback_{sender_id}_{event.get('timestamp', '')}"

                    # Handle media / image attachments without text
                    if not text and message.get("attachments"):
                        text = "ছবি পাঠিয়ে জানতে চাচ্ছি এর দাম ও বিস্তারিত কী?"
                        if not mid:
                            mid = f"attach_{sender_id}_{event.get('timestamp', '')}"

                    if not mid:
                        mid = f"msg_{sender_id}_{event.get('timestamp', '')}"

                    if sender_id and text:
                        background_tasks.add_task(process_messenger_event, sender_id, text, mid)

            # Check for Feed / Comments on posts
            if "changes" in entry:
                for change in entry["changes"]:
                    field = change.get("field")
                    if field == "feed":
                        value = change.get("value", {})
                        background_tasks.add_task(process_comment_event, value)

        return Response(content="EVENT_RECEIVED", status_code=200)

    return Response(content="UNKNOWN_OBJECT", status_code=404)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
