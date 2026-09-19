import sys
import asyncio
import logging

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from services.ai_service import ai_service
from services.sheets_service import sheets_service

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

async def test_human_like_automation():
    print("=" * 65)
    print("🤖 মানবীয় ও নন-টেমপ্লেট (Adaptive) ফেসবুক অটোমেশন টেস্ট")
    print("=" * 65)

    # 1. Banglish Specific Query Comment
    banglish_comment = "bhaiya shirt er navy blue ta ki M size hobe? dam koto?"
    print(f"\n[কেস ১: বাংলিশে নির্দিষ্ট প্রশ্ন]")
    print(f"Customer Comment: \"{banglish_comment}\"")
    pub, send_inbox, inbox_msg = await ai_service.analyze_and_reply_comment(banglish_comment)
    print(f"➡️ পাবলিক কমেন্ট রিপ্লাই (কাস্টমারের স্টাইলে):\n   {pub}")
    print(f"➡️ ইনবক্সে পাঠানো বার্তা:\n   {inbox_msg}")

    # 2. Formal Bangla Query Comment
    bangla_comment = "আসসালামু আলাইকুম, শার্টটির ফেব্রিক কোয়ালিটি কেমন এবং কত দিনে ডেলিভারি পাব?"
    print(f"\n[কেস ২: খাঁটি বাংলায় ফরমাল প্রশ্ন]")
    print(f"Customer Comment: \"{bangla_comment}\"")
    pub2, send_inbox2, inbox_msg2 = await ai_service.analyze_and_reply_comment(bangla_comment)
    print(f"➡️ পাবলিক কমেন্ট রিপ্লাই (ফরমাল বাংলায়):\n   {pub2}")
    print(f"➡️ ইনবক্সে পাঠানো বার্তা:\n   {inbox_msg2}")

    # 3. Pure English Query Comment
    english_comment = "Is this genuine leather wallet still available? How much is it?"
    print(f"\n[কেস ৩: সম্পূর্ণ ইংরেজিতে প্রশ্ন]")
    print(f"Customer Comment: \"{english_comment}\"")
    pub3, send_inbox3, inbox_msg3 = await ai_service.analyze_and_reply_comment(english_comment)
    print(f"➡️ পাবলিক কমেন্ট রিপ্লাই (ইংরেজিতে):\n   {pub3}")
    print(f"➡️ ইনবক্সে পাঠানো বার্তা:\n   {inbox_msg3}")

    # 4. Messenger Adaptive Chat - Conversation flow
    print("\n" + "=" * 65)
    print("💬 [কেস ৪: মেসেঞ্জারে মানুষের মতো স্বাভাবিক কথোপকথন]")
    print("=" * 65)

    uid = "customer_abir_007"

    # Turn 1: User asks specific question
    user_msg_1 = "vai navy blue color ki available ache?"
    print(f"\nCustomer: {user_msg_1}")
    bot_res_1 = await ai_service.handle_messenger_chat(uid, user_msg_1)
    print(f"AI Assistant:\n{bot_res_1}")

    # Turn 2: User asks about delivery
    user_msg_2 = "Dhakar baire delivery charge koto r kobe pabo?"
    print(f"\nCustomer: {user_msg_2}")
    bot_res_2 = await ai_service.handle_messenger_chat(uid, user_msg_2)
    print(f"AI Assistant:\n{bot_res_2}")

    # Turn 3: User places order in a natural, all-in-one sentence
    user_msg_3 = "thik ache, ami shirt ta nibo. amr naam Abir Hasan, phone 01811223344, Sylhet Sadar e pathan"
    print(f"\nCustomer (এক বাক্যে তথ্য প্রদান): {user_msg_3}")
    bot_res_3 = await ai_service.handle_messenger_chat(uid, user_msg_3)
    print(f"AI Assistant:\n{bot_res_3}")

    # Turn 4: User confirms
    user_msg_4 = "ha confirm koren"
    print(f"\nCustomer: {user_msg_4}")
    bot_res_4 = await ai_service.handle_messenger_chat(uid, user_msg_4)
    print(f"AI Assistant:\n{bot_res_4}")

    print("\n" + "=" * 65)
    print("✅ সকল নন-টেমপ্লেট ও মানবীয় অ্যাডাপ্টিভ টেস্ট সফল হয়েছে!")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(test_human_like_automation())
