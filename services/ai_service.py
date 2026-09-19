import logging
import json
import re
from typing import Dict, Any, Tuple, Optional, List
from config import settings
from services.sheets_service import sheets_service

logger = logging.getLogger(__name__)

# Initialize official google-genai Client
genai_client = None
try:
    from google import genai
    from google.genai import types
    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here":
        genai_client = genai.Client(api_key=settings.GEMINI_API_KEY)
        logger.info("[AIService] Gemini Client সফলভাবে অ্যাক্টিভ হয়েছে।")
except Exception as e:
    logger.warning(f"[AIService] Gemini Client লোড করা যায়নি: {e}")


class AIService:
    def __init__(self):
        self.model_name = "gemini-3.5-flash-lite"
        # Keeps last 10 messages for each user: {user_id: [{"role": "user"|"model", "text": "..."}]}
        self.chat_histories: Dict[str, List[Dict[str, str]]] = {}
        # Keeps current order draft: {user_id: {"name": ..., "phone": ..., "address": ..., "product": ..., "quantity": 1, "total_amount": "0"}}
        self.order_drafts: Dict[str, Dict[str, Any]] = {}

    def _clean_json_str(self, raw_text: str) -> str:
        """Strips markdown code fences and cleans JSON response."""
        cleaned = raw_text.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        first_brace = cleaned.find("{")
        last_brace = cleaned.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            cleaned = cleaned[first_brace:last_brace + 1]
        return cleaned

    def _get_products_summary(self) -> str:
        """Formats all 50 products into a concise reference for the AI with aliases."""
        products = sheets_service.get_products()
        lines = []
        for p in products:
            name = p.get("name", "")
            bn_name = p.get("bn_name", name)
            price = p.get("price", "")
            stock = "ইন স্টক" if p.get("available") else "আউট অব স্টক"
            aliases = ", ".join(p.get("aliases", [])[:4])
            lines.append(f"- {name} ({bn_name} / {aliases}) | মূল্য: {price} টাকা | স্টক: {stock}")
        return "\n".join(lines)

    def _extract_phone(self, text: str) -> Optional[str]:
        """Extracts valid 11-digit Bangladeshi phone number (supports English & Bengali numerals)."""
        bn_digits = "০১২৩৪৫৬৭৮৯"
        en_digits = "0123456789"
        mapping = str.maketrans(bn_digits, en_digits)
        text_normalized = str(text).translate(mapping)

        cleaned = re.sub(r"[\s\-]", "", text_normalized)
        match = re.search(r"(?:\+?88)?(01[3-9]\d{8})\b", cleaned)
        return match.group(1) if match else None

    def _detect_language_style(self, text: str) -> str:
        """Detects whether user is speaking in Banglish, Bangla, or English."""
        if bool(re.search(r"[\u0980-\u09FF]", text)):
            return "bangla"
        
        banglish_keywords = {
            "dam", "koto", "koren", "hobe", "ache", "bhai", "bhaiya", "vai", "vaia", "apnar", 
            "amr", "chaile", "nibona", "nibo", "ki", "r", "valo", "kemon", "pathan", "lagbe", 
            "khub", "sundor", "dorkar", "ashole", "kothay", "ekhon", "thik", "ha", "na", 
            "naam", "thikana", "dhaka", "baire", "taka", "apnader", "stock", "ase", "panjabi"
        }
        words = set(re.findall(r"[a-zA-Z]+", text.lower()))
        if words.intersection(banglish_keywords):
            return "banglish"
        
        return "english"

    def _match_product(self, text: str) -> Optional[Dict[str, Any]]:
        """
        High-precision matcher that scores user query against all 50 products using aliases.
        Supports Bengali suffixes (র, এর, টা, টি), English/Banglish stems, and direct aliases.
        """
        stop_words = {
            "জি", "হ্যাঁ", "ha", "yes", "ji", "ok", "না", "no", "দাম", "কত", "price", "koto",
            "কি", "r", "আছে", "hobe", "পাব", "নেন", "আসি", "accha", "thik", "ache", "hello",
            "hi", "সালাম", "ভাই", "ভাইয়া", "bhai", "vai", "নিতে", "চাই", "chai", "nibo", "একদম", "একটা",
            "kobe", "pabo", "deya", "jabe", "details", "ডিটেইলস", "ডেলিভারি", "delivery", "charge", "ase"
        }

        products = sheets_service.get_products()
        clean = text.lower().replace("?", " ").replace("!", " ").replace("।", " ").replace("-", " ").strip()
        suffixes = ["ের", "র", "টা", "টি", "গুলো", "গুলোর", "গুলোয়", "গুলা", "ডা", "ডি", "er", "ta", "ti", "gulo", "gula"]

        best_match = None
        max_score = 0

        for p in products:
            score = 0
            en = p.get("name", "").lower()
            bn = p.get("bn_name", "").lower()
            aliases = [a.lower() for a in p.get("aliases", [])]

            # 1. Check against aliases (with word boundaries and Bengali/English suffixes)
            for alias in aliases:
                alias_clean = alias.replace("-", " ").strip()
                pattern = r"(?<!\w)" + re.escape(alias_clean) + r"(?:er|s|ের|র|টা|টি|গুলো|গুলা)?(?!\w)"
                if re.search(pattern, clean):
                    score = max(score, 30)

            # 2. Tokenized word matching
            words = [w for w in clean.split() if w not in stop_words and len(w) >= 3]
            for w in words:
                base_w = w
                for s in suffixes:
                    if base_w.endswith(s) and len(base_w) > len(s) + 2:
                        base_w = base_w[:-len(s)]
                        break

                if len(base_w) < 3 or base_w in stop_words:
                    continue

                for alias in aliases:
                    alias_clean = alias.replace("-", " ").strip()
                    for aw in alias_clean.split():
                        if aw == base_w:
                            score += 12
                        elif len(base_w) >= 4 and base_w in aw:
                            score += 7

                for ew in en.replace("-", " ").split():
                    if ew == base_w:
                        score += 10
                    elif len(base_w) >= 4 and base_w in ew:
                        score += 5

                for bw in bn.replace("-", " ").split():
                    if bw == base_w:
                        score += 10
                    elif len(base_w) >= 4 and base_w in bw:
                        score += 5

            if score > max_score:
                max_score = score
                best_match = p

        return best_match if max_score >= 10 else None

    async def analyze_and_reply_comment(
        self, comment_text: str, post_text: str = ""
    ) -> Tuple[str, bool, str]:
        products_info = self._get_products_summary()

        if genai_client:
            prompt = f"""
তুমি একজন দক্ষ, বাস্তব মানবিক ফেসবুক শপ ওনার / পেজ ম্যানেজার। তুমি কাস্টমারদের সাথে একদম মানুষের মতো প্রাণবন্ত ও আন্তরিকভাবে কথা বলো।

গুরুত্বপূর্ণ নির্দেশনা:
১. কোনো বাধা-ধরা বা বাঁধাধরা টেমপ্লেট, রোবোটিক মেসেজ বা কপি-পেস্ট টেক্সট কখনো ব্যবহার করবে না।
২. কাস্টমার যেই ভাষায় এবং যে টোনে কথা বলেছে—ঠিক সেই ভাষায় ও টোনে উত্তর দাও (বাংলিশ, বাংলা, ইংরেজি)।
৩. কাস্টমার ঠিক যা জানতে চেয়েছে, সরাসরি শুধু সেই বিষয়ের উত্তর দাও।
৪. কাস্টমার যদি দাম, সাইজ, স্টক, ডেলিভারি জানতে চায় বা কিনতে আগ্রহ প্রকাশ করে, তবে:
   - কমেন্টে ফ্রেন্ডলি সরাসরি উত্তর বা ইঙ্গিত দাও এবং বলো যে ইনবক্সে বিস্তারিত দেওয়া হয়েছে।
   - 'send_inbox': true সেট কর।
   - 'inbox_message'-এ এমন একটি মেসেজ তৈরি কর যা দেখে মনে হবে একজন মানুষ এইমাত্র তাকে ইনবক্স করেছে।
৫. কোনো প্রোডাক্ট যদি আউট অব স্টক (Out of stock) থাকে, তবে জানিয়ে দাও যে এটি আপাতত শেষ হয়ে গেছে এবং রিস্টক হলে জানানো হবে।
৬. কাস্টমার যদি শুধু প্রশংসা বা সাধারণ মন্তব্য করে (যেমন: 'nice', 'সুন্দর'), তবে ইনবক্স বিরক্ত না করে শুধু কমেন্টেই অমায়িক ধন্যবাদ দাও (send_inbox: false)।

আমাদের প্রোডাক্ট লিস্ট ও মূল্য (৫০টি পণ্য):
{products_info}

পোস্টের বিবরণ: {post_text if post_text else 'প্রোডাক্ট পোস্ট'}
কাস্টমারের কমেন্ট: "{comment_text}"

JSON ফরম্যাটে উত্তর দাও:
{{
  "public_reply": "কাস্টমারের অ্যাঙ্গেল ও ভাষায় মানুষের মতো কমেন্ট রিপ্লাই",
  "send_inbox": true,
  "inbox_message": "মানুষের মতো পার্সোনালাইজড ইনবক্স মেসেজ"
}}
"""
            try:
                response = genai_client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                )
                cleaned_json = self._clean_json_str(response.text)
                data = json.loads(cleaned_json)
                return (
                    data.get("public_reply", "ধন্যবাদ আপনার আগ্রহের জন্য! বিস্তারিত ইনবক্সে চেক করুন। 😊"),
                    data.get("send_inbox", True),
                    data.get("inbox_message", "")
                )
            except Exception as e:
                logger.error(f"[AIService] জেমিনাই কমেন্ট এরর: {e}")

        # Dynamic Non-Template Fallback
        lang = self._detect_language_style(comment_text)
        lower = comment_text.lower()
        matched_prod = self._match_product(comment_text)

        prod_bn = matched_prod.get("bn_name", matched_prod.get("name", "পণ্য")) if matched_prod else "পণ্য"
        prod_en = matched_prod.get("name", "Product") if matched_prod else "Product"
        prod_price = matched_prod.get("price", "") if matched_prod else ""
        is_avail = matched_prod.get("available", True) if matched_prod else True

        is_buying_intent = any(k in lower for k in [
            "dam", "price", "দাম", "koto", "কত", "details", "ডিটেইলস", "inbox", "ইনবক্স",
            "order", "অর্ডার", "size", "সাইজ", "colour", "color", "কালার", "need", "chai", "চাই", "available", "fabric"
        ])

        if matched_prod and not is_avail:
            if lang == "banglish":
                pub_reply = f"Sorry bhai! {prod_en} ti ekhon out of stock ache, khub druto restock kora hobe. Inbox check koren details janacchi. 😊"
                send_inbox = True
                inbox_msg = f"As-salamu alaykum bhai! {prod_en} ti ei muhurte stock out hoye geche. Restock hole notify korbo, othoba onno kono product dekhte chaile bolun! ❤️"
            elif lang == "english":
                pub_reply = f"Sorry! The {prod_en} is currently out of stock, but will be restocked soon! Check your inbox. 😊"
                send_inbox = True
                inbox_msg = f"Hello! The {prod_en} is temporarily out of stock. We'll notify you as soon as it arrives! ❤️"
            else:
                pub_reply = f"আন্তরিকভাবে দুঃখিত! {prod_bn}-টি বর্তমানে স্টক আউট রয়েছে, তবে খুব দ্রুত রিস্টক হবে ইনশাআল্লাহ। 😊"
                send_inbox = False
                inbox_msg = ""
            return pub_reply, send_inbox, inbox_msg

        if lang == "banglish":
            if is_buying_intent:
                p_label = prod_en if matched_prod else "Product"
                pub_reply = f"Hey bhai! {p_label}-er price {prod_price} taka. Apnar inbox-e aro details pathiye diyechi, ektu check koren please! 😊"
                send_inbox = True
                inbox_msg = f"As-salamu alaykum bhai! Post-e comment korar jonno thanks. {p_label}-er price {prod_price} taka (In Stock). Cash on delivery-te order korte chaile apnar name, phone number r thikana pathiye din, amra ready kore pathiye dibo! ❤️"
            else:
                pub_reply = "Anek dhonnobad bhai apnar sundor montobber jonno! Valo thakben. ❤️"
                send_inbox = False
                inbox_msg = ""
        elif lang == "english":
            if is_buying_intent:
                p_label = prod_en if matched_prod else "Product"
                pub_reply = f"Hello! The {p_label} is in stock and priced at {prod_price} BDT. We've dropped you a DM with full details, please check! 😊"
                send_inbox = True
                inbox_msg = f"Hi there! Thanks for your interest in our {p_label}. It's currently in stock for {prod_price} BDT. We provide cash on delivery nationwide! If you'd like to place an order, simply reply with your name, phone number, and delivery address. ❤️"
            else:
                pub_reply = "Thank you so much for your kind words! We really appreciate your support. ❤️"
                send_inbox = False
                inbox_msg = ""
        else: # Pure Bangla
            if is_buying_intent:
                pub_reply = f"আসসালামু আলাইকুম! {prod_bn}-এর মূল্য মাত্র {prod_price} টাকা (ইন স্টক)। আপনার ইনবক্সে বিস্তারিত তথ্য পাঠিয়ে দিয়েছি, দয়া করে চেক করে নিন। 😊"
                send_inbox = True
                inbox_msg = f"আসসালামু আলাইকুম!\nপোস্টে আগ্রহ প্রকাশের জন্য ধন্যবাদ। {prod_bn}-টি এখন স্টকে আছে, মূল্য {prod_price} টাকা।\n\nক্যাশ অন ডেলিভারিতে অর্ডার করতে চাইলে আপনার নাম, সচল মোবাইল নম্বর ও ঠিকানা জানিয়ে দিন। আমরা দ্রুত পাঠিয়ে দেব! ❤️"
            else:
                pub_reply = "অনেক ধন্যবাদ আপনার সুন্দর মন্তব্যের জন্য! আমাদের সাথে থাকুন। ❤️"
                send_inbox = False
                inbox_msg = ""

        return pub_reply, send_inbox, inbox_msg

    async def handle_messenger_chat(self, user_id: str, user_text: str) -> str:
        """
        Handles incoming Messenger conversation with deep context and accurate product matching.
        """
        if user_id not in self.chat_histories:
            self.chat_histories[user_id] = []
        if user_id not in self.order_drafts:
            self.order_drafts[user_id] = {
                "name": None, "phone": None, "address": None, "product": None, "quantity": 1, "total_amount": "0"
            }

        history = self.chat_histories[user_id]
        order_draft = self.order_drafts[user_id]
        products_info = self._get_products_summary()

        history_str = ""
        for h in history[-8:]:
            role_label = "Customer" if h["role"] == "user" else "Shop Assistant"
            history_str += f"{role_label}: {h['text']}\n"

        if genai_client:
            prompt = f"""
তুমি একজন বাংলাদেশি ফেসবুক পেজের বাস্তব, অভিজ্ঞ ও চটপটে শপ ম্যানেজার। পেজের নাম Raw Fabric। তুমি কাস্টমারের সাথে মেসেঞ্জারে লাইভ চ্যাট করছো।

⚠️ অত্যন্ত গুরুত্বপূর্ণ নিয়ম (MUST FOLLOW):
১. কোনো বাঁধাধরা টেমপ্লেট বা রোবোটিক স্ক্রিপ্ট ব্যবহার করা সম্পূর্ণ নিষিদ্ধ। প্রতিটি উত্তর কাস্টমারের কথার সাথে মিলিয়ে একদম ইউনিক ও প্রাকৃতিক হবে।
২. কাস্টমারের ভাষা ও টোন সম্পূর্ণভাবে হুবহু অনুকরণ (Mirror) কর:
   - কাস্টমার যদি ইনফরমাল বা ফ্রেন্ডলি বাংলিশে কথা বলে, তুমিও চটপটে, ফ্রেন্ডলি ও আন্তরিক বাংলিশে বা কথ্য বাংলায় কথা বলো।
   - কাস্টমার যদি ফর্মাল বাংলায় বলে, তুমিও সম্মান দিয়ে প্রফেশনাল বাংলায় বলো।
   - কাস্টমার যদি ইংরেজিতে বলে, তুমিও স্বাভাবিক ইংরেজিতে উত্তর দাও।
৩. কাস্টমার যে নির্দিষ্ট প্রশ্নটি করেছে, সরাসরি শুধু সেই প্রশ্নের উত্তর দাও। যদি পাঞ্জাবি নিয়ে জিজ্ঞেস করে, তবে পাঞ্জাবির কথাই বলবে। পাঞ্জাবি জিজ্ঞেস করলে কখনোই টি-শার্ট বা অন্য পণ্যের কথা বলবে না!
৪. কাস্টমার যে পণ্যটির কথা বলবে (যেমন পাঞ্জাবি, শার্ট, জিন্স, ওয়ালেট ইত্যাদি), লিস্টে সেটির আসল নাম, দাম ও স্টক দেখে সঠিক তথ্য দাও।
   - স্টক যদি 'আউট অব স্টক' থাকে, তবে বিনয়ের সাথে জানাও যে এটি আপাতত শেষ হয়ে গেছে।
   - যদি ইন স্টক থাকে, তবে দাম ও বৈশিষ্ট্য জানিয়ে অর্ডারে উৎসাহিত কর।
৫. কাস্টমার যদি 'জি', 'হ্যাঁ' বলে সম্মতি জানায়, তবে তার নাম, ফোন নম্বর ও ডেলিভারি ঠিকানা চেয়ে নাও।
৬. কাস্টমার যখন নাম, ১১ ডিজিট ফোন ও ঠিকানা দেবে, তা 'extracted_info'-তে সংরক্ষণ কর এবং ক্যাশ অন ডেলিভারিতে অর্ডার কনফার্ম করতে সম্মতি চাও।
৭. কাস্টমার যখন চূড়ান্তভাবে 'হ্যাঁ', 'yes', 'confirm', 'পাঠিয়ে দেন' বলে সম্মতি দেবে, তখন 'is_order_confirmed': true সেট করবে।

আমাদের প্রোডাক্ট তালিকা ও মূল্য (৫০টি পণ্য):
{products_info}

ডেলিভারি নিয়ম: ঢাকা শহরে ৬০ টাকা, ঢাকার বাইরে ১২০ টাকা। সম্পূর্ণ ক্যাশ অন ডেলিভারি।

বর্তমান অর্ডারের ইতিমধ্যে পাওয়া তথ্য:
{json.dumps(order_draft, ensure_ascii=False)}

আগের কথোপকথন:
{history_str}

কাস্টমারের নতুন মেসেজ:
Customer: "{user_text}"

JSON ফরম্যাটে উত্তর দাও:
{{
  "reply": "কাস্টমারের ভাষা ও টোন মিলিয়ে মানুষের মতো নিখুঁত উত্তর",
  "extracted_info": {{
    "name": "কাস্টমারের নাম (যদি পাওয়া যায় বা আগে থাকে, অন্যথায় null)",
    "phone": "১১ ডিজিটের ফোন নম্বর (যদি পাওয়া যায় বা আগে থাকে, অন্যথায় null)",
    "address": "ডেলিভারি ঠিকানা (যদি পাওয়া যায় বা আগে থাকে, অন্যথায় null)",
    "product": "যে পণ্য নিতে চায় (যদি জানা থাকে, অন্যথায় null)",
    "quantity": 1
  }},
  "is_order_confirmed": false
}}
"""
            try:
                response = genai_client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                )
                cleaned_json = self._clean_json_str(response.text)
                data = json.loads(cleaned_json)
                reply = data.get("reply", "")

                extracted = data.get("extracted_info", {})
                for key in ["name", "phone", "address", "product", "quantity"]:
                    if extracted.get(key):
                        order_draft[key] = extracted[key]

                if not order_draft.get("phone"):
                    detected_phone = self._extract_phone(user_text)
                    if detected_phone:
                        order_draft["phone"] = detected_phone

                if data.get("is_order_confirmed"):
                    matched = self._match_product(order_draft.get("product", ""))
                    if matched:
                        order_draft["total_amount"] = str(matched.get("price", "0"))

                    sheets_service.add_order(order_draft)
                    self.order_drafts[user_id] = {
                        "name": None, "phone": None, "address": None, "product": None, "quantity": 1, "total_amount": "0"
                    }

                history.append({"role": "user", "text": user_text})
                history.append({"role": "model", "text": reply})
                return reply
            except Exception as e:
                logger.error(f"[AIService] জেমিনাই চ্যাট এরর: {e}")

        # Smart, Highly Context-Aware Fallback Engine
        lang = self._detect_language_style(user_text)
        lower = user_text.lower().strip()
        detected_phone = self._extract_phone(user_text)
        if detected_phone:
            order_draft["phone"] = detected_phone

        # Detect product from text (only if meaningful words exist)
        matched_prod = self._match_product(user_text)
        if matched_prod:
            order_draft["product"] = matched_prod.get("bn_name", matched_prod.get("name"))
            order_draft["total_amount"] = str(matched_prod.get("price", "0"))

        current_prod = order_draft.get("product")
        current_price = order_draft.get("total_amount", "0")

        # 1. Check if user is confirming previous offer (e.g. "জি", "হ্যাঁ", "ha", "yes", "ji", "হবে")
        is_agreeing = lower in ["জি", "হ্যাঁ", "ha", "yes", "ji", "হবে", "চাই", "অর্ডার করব", "নেন", "আসি", "accha", "thik ache"]
        if is_agreeing and not order_draft.get("phone"):
            if current_prod:
                if lang == "banglish":
                    reply = f"Great bhai! Apnar {current_prod}-er order ti confirm korte anugroho kore apnar pura naam, 11-digit phone number r thikana ta pathiye din."
                else:
                    reply = f"অসংখ্য ধন্যবাদ! আপনার {current_prod}-এর অর্ডারটি কনফার্ম করতে অনুগ্রহ করে আপনার পুরো নাম, সচল ১১ ডিজিটের মোবাইল নম্বর এবং সম্পূর্ণ ডেলিভারি ঠিকানাটি পাঠিয়ে দিন।"
            else:
                reply = "জি ধন্যবাদ! আপনি কোন পণ্যটি অর্ডার করতে চান এবং আপনার ডেলিভারি ঠিকানা ও ফোন নম্বরটি একটু লিখে দিন।"
            history.append({"role": "user", "text": user_text})
            history.append({"role": "model", "text": reply})
            return reply

        # 2. Check if customer provided Name, Phone, and Address (e.g. "তানভীর, 01712345678, মিরপুর ১০" or "নাম তানভীর")
        if detected_phone:
            # Try comma-separated
            if "," in user_text:
                parts = [p.strip() for p in user_text.split(",") if p.strip()]
                for p in parts:
                    if not re.search(r"\d", p) and len(p) >= 2 and not order_draft.get("name"):
                        order_draft["name"] = p
                    elif not re.search(r"01[3-9]\d{8}", p) and len(p) >= 4 and not order_draft.get("address"):
                        order_draft["address"] = p
            else:
                # Regex match
                name_match = re.search(r"(?:naam|name|নাম|আমি)\s+([A-Za-z\u0980-\u09FF\s]+?)(?:,|\.|\bphone|\b01|\bthikana|$)", user_text, re.IGNORECASE)
                if name_match:
                    order_draft["name"] = name_match.group(1).strip()
                addr_match = re.search(r"(?:,\s*|\bthikana\s*|\baddress\s*)([A-Za-z0-9\u0980-\u09FF\s\/\#\-]+?)(?:\s+e pathan|\s+te pathan|\s+pathan|$)", user_text, re.IGNORECASE)
                if addr_match:
                    order_draft["address"] = addr_match.group(1).strip()

        # Final Confirmation Check
        is_final_confirm = any(w in lower for w in ["confirm", "পাঠান", "পাঠিয়ে দেন", "confirm order", "কনফার্ম"])
        if is_final_confirm and order_draft.get("phone"):
            p_ordered = order_draft.get("product") or "নির্বাচিত পণ্য"
            sheets_service.add_order(order_draft)
            self.order_drafts[user_id] = {
                "name": None, "phone": None, "address": None, "product": None, "quantity": 1, "total_amount": "0"
            }
            if lang == "banglish":
                reply = f"Great bhai! Apnar {p_ordered}-er order ti confirm hoye geche. Amader team theke call kore delivery time janiye deya hobe. Raw Fabric-er shathe thakar jonno dhonnobad! ❤️"
            elif lang == "english":
                reply = f"Awesome! Your order for {p_ordered} has been placed successfully. Our team will contact you shortly before delivery. Thank you for choosing Raw Fabric! ❤️"
            else:
                reply = f"আলহামদুলিল্লাহ! আপনার {p_ordered}-এর অর্ডারটি নিশ্চিত করা হয়েছে। খুব দ্রুত আমাদের সেলস টিম থেকে কল করে ডেলিভারি কনফার্ম করা হবে। Raw Fabric-এর সাথে থাকার জন্য আন্তরিক ধন্যবাদ! ❤️"
            history.append({"role": "user", "text": user_text})
            history.append({"role": "model", "text": reply})
            return reply

        # If user gave phone & name/address in this message
        if detected_phone and (order_draft.get("name") or order_draft.get("address")):
            p_name = order_draft.get("product") or "পণ্য"
            n = order_draft.get("name") or "ভাই"
            addr = order_draft.get("address") or "দেওয়া ঠিকানায়"
            if lang == "banglish":
                reply = f"Great {n}! Apnar {p_name}-er order ti (Total {current_price} tk + Delivery) {addr} te confirm korbo ki? Cash on delivery te jabe."
            elif lang == "english":
                reply = f"Got it {n}! Should we confirm your order for {p_name} to {addr}? Payment is cash on delivery."
            else:
                reply = f"ধন্যবাদ {n}! আপনার {p_name}-এর অর্ডারটি {addr}-এর ঠিকানায় সম্পূর্ণ ক্যাশ অন ডেলিভারিতে কনফার্ম করব কি?"
            history.append({"role": "user", "text": user_text})
            history.append({"role": "model", "text": reply})
            return reply

        # 3. Product Availability & Price Queries
        if matched_prod:
            prod_name = matched_prod.get("bn_name", matched_prod.get("name"))
            prod_en = matched_prod.get("name")
            pr = matched_prod.get("price")
            avail = matched_prod.get("available", True)

            # Check if asking about stock / availability ("পাঞ্জাবি আছে?", "পাঞ্জাবি নিতে চাই", "পাঞ্জাবি দেখান")
            is_asking_avail = any(w in lower for w in ["আছে", "ache", "hobe", "হবে", "পাব", "pawa", "available", "ase", "দেখান", "dekhan"])
            is_asking_buy = any(w in lower for w in ["নিতে চাই", "nibo", "kinbo", "কিনব", "chai", "চাই", "অর্ডার", "order"])
            is_asking_price = any(w in lower for w in ["দাম", "dam", "price", "কত", "koto"])

            if not avail:
                if lang == "banglish":
                    reply = f"Sorry bhai! Amader {prod_en} ti ei muhurte out of stock ache, khub druto restock kora hobe. Onno kono item lagbe ki?"
                else:
                    reply = f"আন্তরিকভাবে দুঃখিত! আমাদের {prod_name}-টি এই মুহূর্তে স্টক আউট রয়েছে, তবে খুব দ্রুত রিস্টক হবে। অন্য কোনো পণ্য সম্পর্কে জানতে চান কি?"
            elif is_asking_buy or is_asking_avail:
                if lang == "banglish":
                    reply = f"Ji bhai! Amader {prod_en} stock-e available ache, price {pr} taka. Apni ki cash on delivery-te order korte chan?"
                else:
                    reply = f"জি অবশ্যই! আমাদের {prod_name} স্টকে অ্যাভেইলেবল আছে, মূল্য মাত্র {pr} টাকা। আপনি কি ক্যাশ অন ডেলিভারিতে অর্ডার করতে চান?"
            elif is_asking_price:
                if lang == "banglish":
                    reply = f"{prod_en}-er price matro {pr} taka bhai (In Stock). Cash on delivery-te order korte chaile janan!"
                else:
                    reply = f"{prod_name}-এর মূল্য মাত্র {pr} টাকা (ইন স্টক)। পণ্য হাতে পেয়ে ক্যাশ অন ডেলিভারিতে নিতে পারবেন। আপনি কি অর্ডার করতে চান?"
            else:
                reply = f"আমাদের {prod_name} স্টকে রয়েছে, মূল্য {pr} টাকা। এ সম্পর্কে কোনো সাইজ বা বিস্তারিত জানতে চাইলে বলুন!"

            history.append({"role": "user", "text": user_text})
            history.append({"role": "model", "text": reply})
            return reply

        # 4. Delivery policy
        if any(w in lower for w in ["delivery", "charge", "ডেলিভারি", "চার্জ", "kobe pabo", "কবে পাব"]):
            if lang == "banglish":
                reply = "Dhakar moddhe delivery charge 60 taka (1-2 days) r Dhakar baire 120 taka (2-3 days). Full cash on delivery paben!"
            elif lang == "english":
                reply = "Delivery is 60 BDT inside Dhaka (1-2 days) and 120 BDT outside Dhaka (2-3 days). Full cash on delivery!"
            else:
                reply = "ঢাকা সিটির ভেতরে ডেলিভারি চার্জ ৬০ টাকা এবং ঢাকার বাইরে ১২০ টাকা। পণ্য হাতে পেয়ে চেক করে সম্পূর্ণ ক্যাশ অন ডেলিভারিতে টাকা পরিশোধ করতে পারবেন।"
        elif any(w in lower for w in ["hi", "hello", "হাই", "হ্যালো", "salam", "সালাম"]):
            if lang == "banglish":
                reply = "As-salamu alaykum bhai! Raw Fabric-e shagotom. Amader kon product somporke jante chan bolun?"
            elif lang == "english":
                reply = "Hello! Welcome to Raw Fabric. How can I assist you with our products today?"
            else:
                reply = "আসসালামু আলাইকুম! Raw Fabric-এ আপনাকে স্বাগতম। আমাদের পাঞ্জাবি, শার্ট, জিন্স বা অন্য কোনো পণ্য সম্পর্কে কী তথ্য জানতে চান বলুন?"
        else:
            if lang == "banglish":
                reply = "As-salamu alaykum bhai! Raw Fabric-e apnake shagotom. Amader kon product somporke jante chan ba order korte chan bolun, ami help korchi."
            else:
                reply = "আসসালামু আলাইকুম! Raw Fabric-এ আপনাকে স্বাগতম। আমাদের কোন পণ্যটি সম্পর্কে জানতে বা অর্ডার করতে চান বলুন, আমি আনন্দচিত্তে সাহায্য করছি।"

        history.append({"role": "user", "text": user_text})
        history.append({"role": "model", "text": reply})
        return reply

# Global instance
ai_service = AIService()
