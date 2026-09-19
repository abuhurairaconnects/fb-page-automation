import re
import logging
from typing import Dict, Any, Optional
from services.sheets_service import sheets_service

logger = logging.getLogger(__name__)

class OrderSessionManager:
    def __init__(self):
        # In-memory session tracking for each user by PSID
        # {user_id: {"step": "idle", "data": {...}}}
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def get_session(self, user_id: str) -> Dict[str, Any]:
        if user_id not in self.sessions:
            self.sessions[user_id] = {
                "step": "idle",
                "data": {
                    "name": None,
                    "phone": None,
                    "address": None,
                    "product": None,
                    "quantity": 1,
                    "total_amount": 0
                }
            }
        return self.sessions[user_id]

    def reset_session(self, user_id: str):
        if user_id in self.sessions:
            del self.sessions[user_id]

    def extract_phone(self, text: str) -> Optional[str]:
        """Validates and extracts 11-digit Bangladeshi phone numbers (supports English & Bengali numerals)."""
        # Matches formats like: 01712345678, ০১৭১২৩৪৫৬৭৮, +8801712345678, 8801712345678, 018-12345678
        bn_digits = "০১২৩৪৫৬৭৮৯"
        en_digits = "0123456789"
        mapping = str.maketrans(bn_digits, en_digits)
        text_normalized = str(text).translate(mapping)

        cleaned = re.sub(r"[\s\-]", "", text_normalized)
        match = re.search(r"(?:\+?88)?(01[3-9]\d{8})\b", cleaned)
        if match:
            return match.group(1)
        return None

    def start_order(self, user_id: str, product_name: str, price: str = "0") -> str:
        """Starts order collection process for a selected product."""
        session = self.get_session(user_id)
        session["step"] = "collecting_name"
        session["data"]["product"] = product_name
        session["data"]["total_amount"] = price
        return (
            f"🎉 চমৎকার! '{product_name}' অর্ডার করতে চাইলে অনুগ্রহ করে আপনার পুরো নামটি লিখুন:"
        )

    def process_order_step(self, user_id: str, user_text: str) -> Optional[str]:
        """
        Processes multi-step order flow if user is actively placing an order.
        Returns response string if handled by order manager, or None if handled by general AI.
        """
        session = self.get_session(user_id)
        step = session.get("step", "idle")

        if step == "idle":
            return None

        clean_text = user_text.strip()

        # Step 1: Name
        if step == "collecting_name":
            session["data"]["name"] = clean_text
            session["step"] = "collecting_phone"
            return (
                f"ধন্যবাদ {clean_text}! এবার আপনার সচল ১১ ডিজিটের মোবাইল নম্বরটি দিন (যেমন: 017XXXXXXXX):"
            )

        # Step 2: Phone
        elif step == "collecting_phone":
            phone = self.extract_phone(clean_text)
            if not phone:
                return (
                    "⚠️ দুঃখিত! ফোন নম্বরটি সঠিক মনে হচ্ছে না। অনুগ্রহ করে একটি সঠিক ১১ ডিজিটের মোবাইল নম্বর লিখুন (যেমন: 01712345678):"
                )
            session["data"]["phone"] = phone
            session["step"] = "collecting_address"
            return (
                "ধন্যবাদ! এবার ডেলিভারির জন্য আপনার সম্পূর্ণ ঠিকানাটি লিখুন (জেলা, থানা ও এলাকা/বাসা নম্বর):"
            )

        # Step 3: Address
        elif step == "collecting_address":
            if len(clean_text) < 5:
                return "অনুগ্রহ করে আপনার সম্পূর্ণ ডেলিভারি ঠিকানা বিস্তারিতভাবে লিখুন:"
            session["data"]["address"] = clean_text
            session["step"] = "confirming"

            data = session["data"]
            summary = (
                f"📋 আপনার অর্ডারের তথ্য:\n"
                f"▪ পণ্য: {data.get('product', 'পণ্য')}\n"
                f"▪ নাম: {data.get('name')}\n"
                f"▪ মোবাইল: {data.get('phone')}\n"
                f"▪ ঠিকানা: {data.get('address')}\n"
                f"▪ পেমেন্ট: ক্যাশ অন ডেলিভারি (পণ্য হাতে পেয়ে টাকা দেবেন)\n\n"
                f"অর্ডার কনফার্ম করতে 'হ্যাঁ' বা 'CONFIRM' লিখুন, অথবা কোনো কিছু পরিবর্তন করতে চাইলে জানান।"
            )
            return summary

        # Step 4: Confirmation
        elif step == "confirming":
            lower = clean_text.lower()
            if any(w in lower for w in ["হ্যাঁ", "yes", "confirm", "হবে", "ok", "ঠিক আছে", "confirm order"]):
                # Save to Google Sheet
                saved = sheets_service.add_order(session["data"])
                self.reset_session(user_id)
                if saved:
                    return (
                        "✅ অভিনন্দন! আপনার অর্ডারটি সফলভাবে গৃহীত হয়েছে। আমাদের সেলস টিম শীঘ্রই আপনাকে কল করে ডেলিভারি নিশ্চিত করবে। সাথে থাকার জন্য ধন্যবাদ! ❤️"
                    )
                else:
                    return (
                        "✅ আপনার অর্ডারটি রেকর্ড করা হয়েছে। আমাদের প্রতিনিধি দ্রুত আপনার সাথে যোগাযোগ করবেন। ধন্যবাদ!"
                    )
            elif any(w in lower for w in ["না", "cancel", "বাতিল", "no"]):
                self.reset_session(user_id)
                return "অর্ডার বাতিল করা হয়েছে। যেকোনো তথ্যের জন্য যেকোনো সময় মেসেজ দিতে পারেন!"
            else:
                return "অর্ডার কনফার্ম করতে 'হ্যাঁ' অথবা বাতিল করতে 'না' লিখুন।"

        return None

# Global instance
order_manager = OrderSessionManager()
