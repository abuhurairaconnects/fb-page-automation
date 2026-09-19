import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def run_wizard():
    print("=" * 65)
    print("🛠️  ফেসবুক এআই অটোমেশন সেটআপ উইজার্ড")
    print("=" * 65)
    print("এই উইজার্ডটি আপনার পেজ এবং গুগল শিট কানেক্ট করার জন্য .env ফাইল তৈরিতে সাহায্য করবে।")
    print("(যেকোনো ফিল্ডে কিছু না লিখে এন্টার চাপলে ডিফল্ট মান ব্যবহৃত হবে)\n")

    env_path = ".env"
    existing = {}
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    existing[k.strip()] = v.strip()

    # 1. Gemini API Key
    curr_gemini = existing.get("GEMINI_API_KEY", "")
    print(f"১. Gemini API Key (Google AI Studio থেকে প্রাপ্ত)")
    if curr_gemini and curr_gemini != "your_gemini_api_key_here":
        print(f"   বর্তমান মান: {curr_gemini[:6]}...{curr_gemini[-4:]}")
    new_gemini = input("   আপনার Gemini API Key দিন (অথবা এন্টার চাপুন): ").strip()
    gemini_key = new_gemini if new_gemini else (curr_gemini or "your_gemini_api_key_here")

    # 2. Facebook Page Access Token
    curr_fb = existing.get("PAGE_ACCESS_TOKEN", "")
    print(f"\n২. Facebook Page Access Token")
    if curr_fb and curr_fb != "placeholder_token":
        print(f"   বর্তমান মান: {curr_fb[:10]}...")
    new_fb = input("   আপনার Page Access Token দিন (অথবা এন্টার চাপুন): ").strip()
    fb_token = new_fb if new_fb else (curr_fb or "placeholder_token")

    # 3. Facebook Page ID
    curr_page_id = existing.get("PAGE_ID", "")
    print(f"\n৩. Facebook Page Numeric ID (যেমন: 1029384756)")
    if curr_page_id:
        print(f"   বর্তমান মান: {curr_page_id}")
    new_page_id = input("   আপনার Page ID দিন (অথবা এন্টার চাপুন): ").strip()
    page_id = new_page_id if new_page_id else curr_page_id

    # 4. Webhook Verify Token
    curr_verify = existing.get("VERIFY_TOKEN", "my_super_secret_verify_token")
    print(f"\n৪. Webhook Verify Token (ফেসবুক ওয়েববুক ভেরিফিকেশন কোড)")
    print(f"   প্রস্তাবিত: {curr_verify}")
    new_verify = input("   নতুন কোড দিতে চাইলে লিখুন (অথবা এন্টার চাপুন): ").strip()
    verify_token = new_verify if new_verify else curr_verify

    # 5. Google Sheet ID
    curr_sheet = existing.get("GOOGLE_SHEET_ID", "")
    print(f"\n৫. Google Sheet URL বা স্প্রেডশীট আইডি")
    print("   উদাহরণ: https://docs.google.com/spreadsheets/d/1BxiMVs0.../edit থেকে মাঝের আইডিটি")
    if curr_sheet:
        print(f"   বর্তমান মান: {curr_sheet}")
    new_sheet = input("   আপনার Google Sheet ID দিন (অথবা এন্টার চাপুন): ").strip()
    # Extract ID if user pasted full URL
    if "spreadsheets/d/" in new_sheet:
        new_sheet = new_sheet.split("spreadsheets/d/")[1].split("/")[0]
    sheet_id = new_sheet if new_sheet else curr_sheet

    # Save to .env
    content = f"""# ==========================================
# Facebook / Meta Graph API Credentials
# ==========================================
PAGE_ACCESS_TOKEN={fb_token}
VERIFY_TOKEN={verify_token}
PAGE_ID={page_id}
GRAPH_API_VERSION=v21.0

# ==========================================
# Google Gemini AI API
# ==========================================
GEMINI_API_KEY={gemini_key}

# ==========================================
# Google Sheets Integration
# ==========================================
GOOGLE_CREDS_FILE=service_account.json
GOOGLE_SHEET_ID={sheet_id}
SHEET_PRODUCTS_TAB=Products
SHEET_ORDERS_TAB=Orders

# ==========================================
# Server Configuration
# ==========================================
PORT=8000
HOST=0.0.0.0
DEBUG=True
"""
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("\n" + "=" * 65)
    print("✅ আপনার .env ফাইলটি সফলভাবে আপডেট করা হয়েছে!")
    print("=" * 65)
    print(f"পরবর্তী ধাপ:")
    print(f"১. Google Service Account এর 'service_account.json' ফাইলটি এই ফোল্ডারে রাখুন।")
    print(f"২. সার্ভার চালু করতে রান করুন: python main.py")
    print(f"৩. ngrok দিয়ে লাইভ লিংক পেতে রান করুন: ngrok http 8000")
    print("=" * 65)

if __name__ == "__main__":
    run_wizard()
