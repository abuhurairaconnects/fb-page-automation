import os
import csv
import io
import json
import datetime
import logging
from typing import List, Dict, Any, Optional
import httpx
from config import settings

logger = logging.getLogger(__name__)

# Bilingual translation map for the 50 products
BN_TRANSLATION_MAP = {
    "Cotton T-Shirt": "কটন টি-শার্ট",
    "Slim Fit Denim Jeans": "স্লিম ফিট ডেনিম জিন্স",
    "Formal Punjabi": "ফরমাল পাঞ্জাবি",
    "Leather Oxford Shoes": "লেদার অক্সফোর্ড জুতা",
    "Casual Polo Shirt": "ক্যাজুয়াল পোলো শার্ট",
    "Chino Pants": "চিনো প্যান্ট",
    "Running Sneakers": "রানিং স্নিকার্স",
    "Silk Saree": "সিল্ক শাড়ি",
    "Embroidered Kurti": "এমব্রয়ডারি কুর্তি",
    "Canvas Slip-On Shoes": "ক্যানভাস স্লিপ-অন জুতা",
    "Leather Wallet": "লেদার ওয়ালেট / মানিব্যাগ",
    "Classic Wristwatch": "ক্লাসিক রিস্টওয়াচ / হাতঘড়ি",
    "Stainless Steel Water Bottle": "স্টেইনলেস স্টিল ওয়াটার বোতল",
    "Wireless Bluetooth Earbuds": "ওয়্যারলেস ব্লুটুথ ইয়ারবাডস",
    "Smart Fitness Band": "স্মার্ট ফিটনেস ব্যান্ড",
    "Formal Dress Shirt": "ফরমাল ড্রেস শার্ট",
    "Casual Hoodie": "ক্যাজুয়াল হুডি",
    "Winter Jacket": "উইন্টার জ্যাকেট",
    "Sports Jogger Pants": "স্পোর্টস জগার প্যান্ট",
    "Loafers": "লোফার্স জুতা",
    "Leather Belt": "লেদার বেল্ট",
    "Backpack": "ব্যাকপ্যাক / ব্যাগ",
    "Aviator Sunglasses": "এভিয়েটর সানগ্লাস",
    "Ceramic Coffee Mug": "সিরামিক কফি মগ",
    "Electric Kettle": "ইলেকট্রিক কেটলি",
    "Desk Lamp LED": "ডেস্ক ল্যাম্প এলইডি",
    "Bluetooth Speaker": "ব্লুটুথ স্পিকার",
    "USB-C Fast Charger": "ইউএসবি-সি ফাস্ট চার্জার",
    "Mechanical Keyboard": "মেকানিক্যাল কিবোর্ড",
    "Ergonomic Wireless Mouse": "এরগোনোমিক ওয়্যারলেস মাউস",
    "Laptop Sleeve": "ল্যাপটপ স্লিভ / কভার",
    "Cotton Pajama Set": "কটন পায়জামা সেট",
    "Denim Jacket": "ডেনিম জ্যাকেট",
    "Sandalwood Scented Candle": "স্যান্ডালউড সুগন্ধি মোমবাতি",
    "Non-Stick Frying Pan": "নন-স্টিক ফ্রাইং প্যান",
    "Portable Power Bank 20000mAh": "পাওয়ার ব্যাংক ২০০০০ এমএএইচ",
    "Over-Ear Headphones": "ওভার-ইয়ার হেডফোন",
    "Linen Casual Shirt": "লিনেন ক্যাজুয়াল শার্ট",
    "Leather Formal Belt": "লেদার ফরমাল বেল্ট",
    "Sports Duffel Bag": "স্পোর্টস ডাফেল ব্যাগ",
    "Bath Towel Set": "বাথ টাওয়াল সেট / তোয়ালে",
    "Stainless Steel Cutlery Set": "স্টেইনলেস স্টিল কাটলারি সেট / চামচ",
    "Travel Neck Pillow": "ট্রাভেল নেক পিলো / বালিশ",
    "Graphic Print T-Shirt": "গ্রাফিক প্রিন্ট টি-শার্ট",
    "Semi-Formal Blazer": "সেমি-ফরমাল ব্লেজার",
    "Leather Chelsea Boots": "লেদার চেলসি বুট জুতা",
    "Premium Pajama Pants": "প্রিমিয়াম পায়জামা প্যান্ট",
    "Smart LED Bulb": "স্মার্ট এলইডি বাল্ব",
    "Insulated Travel Tumbler": "ইনসুলেটেড ট্রাভেল ফ্লাস্ক / টাম্বলার",
    "Noise-Cancelling Earplugs": "নয়েজ ক্যান্সেলিং ইয়ারপ্লাগ"
}

# Exhaustive colloquial synonyms for customer queries in Bengali, Banglish & English
PRODUCT_ALIASES: Dict[str, List[str]] = {
    "Formal Punjabi": ["পাঞ্জাবি", "পাঞ্জাবী", "পান্জাবি", "পান্জাবী", "panjabi", "punjabi", "panjaby", "punjaby", "formal punjabi", "formal panjabi"],
    "Cotton T-Shirt": ["টি-শার্ট", "টিশার্ট", "টি শার্ট", "কটন টি-শার্ট", "কটন টিশার্ট", "tshirt", "t-shirt", "t shirt", "cotton tshirt", "cotton t-shirt"],
    "Graphic Print T-Shirt": ["গ্রাফিক টি-শার্ট", "গ্রাফিক টিশার্ট", "প্রিন্ট টি-শার্ট", "graphic tshirt", "print tshirt", "graphic t-shirt", "print t-shirt"],
    "Slim Fit Denim Jeans": ["জিন্স", "জিন্স প্যান্ট", "ডেনিম জিন্স", "জিনস", "jeans", "denim", "denim jeans", "jeans pant"],
    "Chino Pants": ["চিনো", "চিনো প্যান্ট", "চিনোস", "chino", "chino pant", "chinos", "pant", "pants", "প্যান্ট"],
    "Sports Jogger Pants": ["জগার", "জগার প্যান্ট", "jogger", "joggers", "jogger pant"],
    "Leather Oxford Shoes": ["অক্সফোর্ড জুতা", "অক্সফোর্ড শু", "oxford shoes", "oxford shoe", "লেদার জুতা"],
    "Casual Polo Shirt": ["পোলো", "পোলো শার্ট", "polo", "polo shirt", "casual polo"],
    "Formal Dress Shirt": ["ফরমাল শার্ট", "ড্রেস শার্ট", "formal shirt", "dress shirt"],
    "Linen Casual Shirt": ["লিনেন শার্ট", "লিনেন ক্যাজুয়াল", "linen shirt", "linen"],
    "Running Sneakers": ["স্নিকার্স", "স্নিকার", "রানিং জুতা", "sneakers", "sneaker", "running shoes"],
    "Canvas Slip-On Shoes": ["ক্যানভাস জুতা", "স্লিপ-অন", "slip-on", "canvas shoes"],
    "Loafers": ["লোফার", "লোফার্স", "loafers", "loafer"],
    "Leather Chelsea Boots": ["চেলসি বুট", "বুট জুতা", "বুট", "chelsea boots", "boots", "boot"],
    "Silk Saree": ["শাড়ি", "সিল্ক শাড়ি", "শাড়ি", "saree", "sari", "silk saree"],
    "Embroidered Kurti": ["কুর্তি", "এমব্রয়ডারি কুর্তি", "kurti", "kurty"],
    "Leather Wallet": ["লেদার ওয়ালেট", "ওয়ালেট", "ওয়ালেট", "মানিব্যাগ", "মানি ব্যাগ", "manibag", "wallet", "money bag", "leather wallet"],
    "Classic Wristwatch": ["হাতঘড়ি", "হাত ঘড়ি", "হাতঘড়ি", "ঘড়ি", "ঘড়ি", "wristwatch", "watch", "ghori", "wrist watch"],
    "Stainless Steel Water Bottle": ["ওয়াটার বোতল", "পানির বোতল", "বোতল", "water bottle", "bottle"],
    "Wireless Bluetooth Earbuds": ["ইয়ারবাডস", "ইয়ারবাড", "earbuds", "earbud", "airpods", "wireless earbuds"],
    "Smart Fitness Band": ["ফিটনেস ব্যান্ড", "স্মার্ট ব্যান্ড", "fitness band", "smart band"],
    "Casual Hoodie": ["হুডি", "hoodie", "hoody"],
    "Winter Jacket": ["উইন্টার জ্যাকেট", "শীতের জ্যাকেট", "winter jacket"],
    "Denim Jacket": ["ডেনিম জ্যাকেট", "denim jacket"],
    "Semi-Formal Blazer": ["ব্লেজার", "blazer", "semi formal blazer"],
    "Leather Belt": ["লেদার বেল্ট", "বেল্ট", "belt", "leather belt"],
    "Leather Formal Belt": ["ফরমাল বেল্ট", "formal belt"],
    "Backpack": ["ব্যাকপ্যাক", "ব্যাগ", "backpack", "bag", "school bag"],
    "Sports Duffel Bag": ["ডাফেল ব্যাগ", "duffel bag", "sports bag"],
    "Aviator Sunglasses": ["সানগ্লাস", "রোদচশমা", "চশমা", "sunglasses", "sunglass", "glasses"],
    "Ceramic Coffee Mug": ["কফি মগ", "মগ", "coffee mug", "mug"],
    "Electric Kettle": ["ইলেকট্রিক কেটলি", "কেটলি", "electric kettle", "kettle"],
    "Desk Lamp LED": ["ডেস্ক ল্যাম্প", "টেবিল ল্যাম্প", "desk lamp", "table lamp"],
    "Bluetooth Speaker": ["ব্লুটুথ স্পিকার", "স্পিকার", "speaker", "bluetooth speaker"],
    "USB-C Fast Charger": ["চার্জার", "ফাস্ট চার্জার", "charger", "fast charger", "type c charger", "usb-c"],
    "Mechanical Keyboard": ["কিবোর্ড", "মেকানিক্যাল কিবোর্ড", "keyboard", "mechanical keyboard"],
    "Ergonomic Wireless Mouse": ["মাউস", "ওয়্যারলেস মাউস", "mouse", "wireless mouse"],
    "Laptop Sleeve": ["ল্যাপটপ স্লিভ", "ল্যাপটপ ব্যাগ", "ল্যাপটপ কভার", "laptop sleeve", "laptop cover"],
    "Cotton Pajama Set": ["পায়জামা সেট", "পাজামা সেট", "কটন পায়জামা", "pajama set", "payjama"],
    "Premium Pajama Pants": ["পায়জামা প্যান্ট", "পাজামা", "প্রিমিয়াম পায়জামা", "pajama pants"],
    "Sandalwood Scented Candle": ["সুগন্ধি মোমবাতি", "মোমবাতি", "scented candle", "candle"],
    "Non-Stick Frying Pan": ["ফ্রাইং প্যান", "কড়াই", "frying pan", "pan"],
    "Portable Power Bank 20000mAh": ["পাওয়ার ব্যাংক", "পাওয়ার ব্যাংক", "power bank", "powerbank"],
    "Over-Ear Headphones": ["হেডফোন", "ওভার-ইয়ার হেডফোন", "headphones", "headphone"],
    "Bath Towel Set": ["তোয়ালে", "গামছা", "বাথ টাওয়াল", "towel", "bath towel"],
    "Stainless Steel Cutlery Set": ["কাটলারি সেট", "চামচ", "cutlery set", "spoon set"],
    "Travel Neck Pillow": ["নেক পিলো", "বালিশ", "ট্রাভেল পিলো", "neck pillow", "travel pillow"],
    "Smart LED Bulb": ["স্মার্ট বাল্ব", "এলইডি বাল্ব", "বাল্ব", "smart bulb", "led bulb", "bulb"],
    "Insulated Travel Tumbler": ["ট্রাভেল ফ্লাস্ক", "ফ্লাস্ক", "টাম্বলার", "tumbler", "travel tumbler", "flask"],
    "Noise-Cancelling Earplugs": ["ইয়ারপ্লাগ", "কান বন্ধ করার প্লাগ", "earplugs", "earplug"]
}

def normalize_bn_digits(text: str) -> str:
    """Converts Bengali numerals (০-৯) to English digits (0-9)."""
    bn_digits = "০১২৩৪৫৬৭৮৯"
    en_digits = "0123456789"
    mapping = str.maketrans(bn_digits, en_digits)
    return str(text).translate(mapping)

class SheetsService:
    def __init__(self):
        self.orders_file = "orders.csv"
        self.products_cache: List[Dict[str, Any]] = []
        self.last_sync_time: float = 0
        self.cache_ttl: float = 180  # 3 minutes auto-refresh TTL
        self._init_local_orders()
        self.sync_products_from_sheet()

    def _init_local_orders(self):
        """Ensures orders.csv exists with proper headers."""
        if not os.path.exists(self.orders_file):
            try:
                with open(self.orders_file, "w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        "তারিখ ও সময় (Date & Time)",
                        "কাস্টমারের নাম (Customer Name)",
                        "ফোন নম্বর (Phone Number)",
                        "ডেলিভারি ঠিকানা (Delivery Address)",
                        "পণ্য (Product Name)",
                        "পরিমাণ (Quantity)",
                        "মোট টাকা (Total Amount BDT)",
                        "পেমেন্ট স্ট্যাটাস (Payment Status)"
                    ])
            except Exception as e:
                logger.error(f"[SheetsService] orders.csv তৈরি করতে সমস্যা: {e}")

    def sync_products_from_sheet(self) -> List[Dict[str, Any]]:
        """Fetches live products directly from the user's Google Sheet."""
        import time
        sheet_id = settings.GOOGLE_SHEET_ID or "1m3BaNq8mWi0DmwbMHefJ_uPoPXWIlX9zxNQwxxSnf7k"
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
        
        try:
            r = httpx.get(url, follow_redirects=True, timeout=10.0)
            if r.status_code == 200:
                reader = csv.DictReader(io.StringIO(r.text))
                items = []
                for row in reader:
                    name = row.get("Products") or row.get("Product Name")
                    price = row.get("Price")
                    avail_str = str(row.get("isAvailable", "Yes")).strip().lower()
                    avail = avail_str in ["yes", "true", "1"]
                    if name and price:
                        bn_name = BN_TRANSLATION_MAP.get(name, name)
                        items.append({
                            "name": name,
                            "bn_name": bn_name,
                            "price": str(price).strip(),
                            "available": avail,
                            "stock": "ইন স্টক" if avail else "আউট অব স্টক",
                            "aliases": PRODUCT_ALIASES.get(name, [name, bn_name])
                        })
                if items:
                    self.products_cache = items
                    self.last_sync_time = time.time()
                    # Also persist to local products.json
                    with open("products.json", "w", encoding="utf-8") as f:
                        json.dump(items, f, ensure_ascii=False, indent=2)
                    logger.info(f"[SheetsService] গুগল শিট থেকে লাইভ {len(items)}টি প্রোডাক্ট আপডেট হয়েছে!")
                    return items
        except Exception as e:
            logger.warning(f"[SheetsService] গুগল শিট থেকে লাইভ সিঙ্ক এরর: {e}")

        # Fallback to local products.json if offline
        if os.path.exists("products.json"):
            try:
                with open("products.json", "r", encoding="utf-8") as f:
                    self.products_cache = json.load(f)
                    self.last_sync_time = time.time()
            except Exception:
                pass
        return self.products_cache

    def get_products(self) -> List[Dict[str, Any]]:
        import time
        now = time.time()
        if not self.products_cache or (now - self.last_sync_time > self.cache_ttl):
            self.sync_products_from_sheet()
        return self.products_cache

    def add_order(self, order_data: Dict[str, Any]) -> bool:
        now = datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")
        name = order_data.get("name", "অজানা")
        phone = normalize_bn_digits(order_data.get("phone", "অজানা"))
        address = order_data.get("address", "অজানা")
        product = order_data.get("product", "অজানা")
        quantity = order_data.get("quantity", 1)
        total_amount = order_data.get("total_amount", "0")
        status = "পেন্ডিং (ক্যাশ অন ডেলিভারি)"

        row = [now, name, phone, address, product, quantity, total_amount, status]
        try:
            with open(self.orders_file, "a", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(row)
            logger.info(f"[SheetsService] নতুন অর্ডার সেভ হয়েছে: {name} - {phone} ({product})")
            return True
        except Exception as e:
            logger.error(f"[SheetsService] orders.csv-তে লিখতে এরর: {e}")
            return False

# Global instance
sheets_service = SheetsService()
