import time
import logging
from typing import Optional, List, Dict, Any
import httpx
from config import settings

logger = logging.getLogger(__name__)

class FacebookService:
    def __init__(self):
        self.base_url = f"https://graph.facebook.com/{settings.GRAPH_API_VERSION}"
        self.processed_ids: Dict[str, float] = {}  # {id: timestamp} for deduplication
        self.cache_ttl = 3600  # keep processed IDs for 1 hour

    def _is_already_processed(self, item_id: str) -> bool:
        """Prevents duplicate processing if Meta retries a webhook delivery."""
        now = time.time()
        # Clean expired items
        expired = [k for k, v in self.processed_ids.items() if now - v > self.cache_ttl]
        for k in expired:
            del self.processed_ids[k]

        if item_id in self.processed_ids:
            return True
        self.processed_ids[item_id] = now
        return False

    async def send_message(
        self,
        recipient_id: str,
        text: str,
        quick_replies: Optional[List[Dict[str, str]]] = None
    ) -> bool:
        """
        Sends a standard Messenger message to a user by their PSID (Page-Scoped ID).
        """
        url = f"{self.base_url}/me/messages"
        params = {"access_token": settings.PAGE_ACCESS_TOKEN}
        
        if text and len(text) > 1900:
            text = text[:1890] + "\n..."

        message_payload: Dict[str, Any] = {"text": text}
        if quick_replies:
            message_payload["quick_replies"] = [
                {
                    "content_type": "text",
                    "title": qr.get("title", ""),
                    "payload": qr.get("payload", qr.get("title", ""))
                }
                for qr in quick_replies
            ]

        payload = {
            "recipient": {"id": recipient_id},
            "messaging_type": "RESPONSE",
            "message": message_payload
        }

        if settings.PAGE_ACCESS_TOKEN == "placeholder_token":
            logger.info(f"[FacebookService - Mock Send Message to {recipient_id}]:\n{text}")
            return True

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, params=params, json=payload)
                if res.status_code == 200:
                    logger.info(f"[FacebookService] মেসেজ সফলভাবে পাঠানো হয়েছে: {recipient_id}")
                    return True
                else:
                    logger.error(f"[FacebookService] মেসেজ পাঠাতে মেটা ত্রুটি ({res.status_code}): {res.text}")
                    return False
        except Exception as e:
            logger.error(f"[FacebookService] মেসেজ সেন্ড করার সময় এক্সেপশন: {e}")
            return False

    async def reply_to_comment(self, comment_id: str, reply_text: str) -> bool:
        """
        Publishes a public reply to a comment on a Facebook post.
        Endpoint: POST /{comment_id}/comments
        """
        url = f"{self.base_url}/{comment_id}/comments"
        params = {"access_token": settings.PAGE_ACCESS_TOKEN}
        payload = {"message": reply_text}

        if settings.PAGE_ACCESS_TOKEN == "placeholder_token":
            logger.info(f"[FacebookService - Mock Public Comment Reply to {comment_id}]:\n{reply_text}")
            return True

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, params=params, json=payload)
                if res.status_code == 200:
                    logger.info(f"[FacebookService] কমেন্টে পাবলিক রিপ্লাই দেওয়া হয়েছে: {comment_id}")
                    return True
                else:
                    logger.error(f"[FacebookService] কমেন্ট রিপ্লাই ত্রুটি ({res.status_code}): {res.text}")
                    return False
        except Exception as e:
            logger.error(f"[FacebookService] কমেন্ট রিপ্লাই এক্সেপশন: {e}")
            return False

    async def send_private_reply(self, comment_id: str, private_text: str) -> bool:
        """
        Sends a private message to the user who made the comment (into their Messenger inbox).
        Endpoint: POST /me/messages with recipient: {"comment_id": comment_id}
        Note: Meta policy allows only 1 private reply per comment.
        """
        url = f"{self.base_url}/me/messages"
        params = {"access_token": settings.PAGE_ACCESS_TOKEN}
        payload = {
            "recipient": {"comment_id": comment_id},
            "message": {"text": private_text}
        }

        if settings.PAGE_ACCESS_TOKEN == "placeholder_token":
            logger.info(f"[FacebookService - Mock Private Inbox Reply for comment {comment_id}]:\n{private_text}")
            return True

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, params=params, json=payload)
                if res.status_code == 200:
                    logger.info(f"[FacebookService] ইনবক্সে প্রাইভেট রিপ্লাই সফলভাবে পাঠানো হয়েছে (Comment ID: {comment_id})")
                    return True
                else:
                    logger.error(f"[FacebookService] ইনবক্স প্রাইভেট রিপ্লাই ত্রুটি ({res.status_code}): {res.text}")
                    return False
        except Exception as e:
            logger.error(f"[FacebookService] প্রাইভেট রিপ্লাই এক্সেপশন: {e}")
            return False

# Global instance
facebook_service = FacebookService()
