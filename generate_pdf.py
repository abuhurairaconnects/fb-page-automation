import os
import subprocess

html_code = """<!DOCTYPE html>
<html lang="bn">
<head>
  <meta charset="UTF-8">
  <title>Raw Fabric AI Bot - প্রেজেন্টেশন ও ডিফেন্স গাইড</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@300;400;500;600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    @page {
      size: A4;
      margin: 12mm 14mm 12mm 14mm;
    }
    * {
      box-sizing: border-box;
      -webkit-print-color-adjust: exact !important;
      print-color-adjust: exact !important;
    }
    body {
      font-family: 'Hind Siliguri', 'Inter', Arial, sans-serif;
      line-height: 1.5;
      color: #1e293b;
      background-color: #ffffff;
      margin: 0;
      padding: 0;
      font-size: 13px;
    }
    .cover {
      background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 45%, #312e81 100%);
      color: #ffffff;
      padding: 26px 24px;
      border-radius: 12px;
      margin-bottom: 18px;
      box-shadow: 0 10px 25px rgba(15, 23, 42, 0.15);
    }
    .badge-top {
      display: inline-block;
      background: rgba(255, 255, 255, 0.18);
      backdrop-filter: blur(5px);
      padding: 4px 12px;
      border-radius: 20px;
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 0.5px;
      margin-bottom: 8px;
      text-transform: uppercase;
      border: 1px solid rgba(255, 255, 255, 0.25);
    }
    .cover h1 {
      font-size: 24px;
      font-weight: 700;
      margin: 0 0 6px 0;
      color: #ffffff;
      line-height: 1.25;
    }
    .cover .subtitle {
      font-size: 13.5px;
      color: #c7d2fe;
      margin: 0 0 16px 0;
      font-weight: 500;
    }
    .meta-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 10px;
      background: rgba(15, 23, 42, 0.45);
      padding: 10px 14px;
      border-radius: 8px;
      border: 1px solid rgba(255, 255, 255, 0.15);
    }
    .meta-item {
      font-size: 11.5px;
    }
    .meta-item span {
      color: #94a3b8;
      display: block;
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .meta-item strong {
      color: #ffffff;
      font-size: 12.5px;
    }
    
    .section {
      margin-bottom: 16px;
      page-break-inside: avoid;
    }
    .section-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 15.5px;
      font-weight: 700;
      color: #0f172a;
      border-bottom: 2px solid #e2e8f0;
      padding-bottom: 4px;
      margin-top: 0;
      margin-bottom: 10px;
    }
    .section-title .icon {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 25px;
      height: 25px;
      background: #ede9fe;
      color: #4f46e5;
      border-radius: 6px;
      font-size: 13px;
    }
    
    .card {
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 10px 12px;
      margin-bottom: 8px;
      page-break-inside: avoid;
    }
    .card-highlight {
      background: #f0fdf4;
      border: 1px solid #bbf7d0;
    }
    .card-alert {
      background: #fffbeb;
      border: 1px solid #fde68a;
    }
    .card-tech {
      background: #f8fafc;
      border-left: 4px solid #4f46e5;
    }
    
    .pitch-quote {
      background: #f5f3ff;
      border-left: 4px solid #6366f1;
      padding: 10px 14px;
      border-radius: 0 8px 8px 0;
      font-size: 12.5px;
      color: #312e81;
      margin-bottom: 12px;
      line-height: 1.55;
    }
    
    .grid-2 {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }
    
    .badge {
      display: inline-block;
      padding: 2px 7px;
      border-radius: 4px;
      font-size: 10.5px;
      font-weight: 600;
    }
    .badge-blue { background: #dbeafe; color: #1e40af; }
    .badge-green { background: #dcfce7; color: #166534; }
    .badge-purple { background: #f3e8ff; color: #6b21a8; }
    .badge-amber { background: #fef3c7; color: #92400e; }
    
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 6px 0;
      font-size: 12px;
    }
    th, td {
      padding: 6px 8px;
      text-align: left;
      border: 1px solid #e2e8f0;
    }
    th {
      background: #f1f5f9;
      color: #334155;
      font-weight: 600;
    }
    tr:nth-child(even) {
      background: #f8fafc;
    }
    
    .qa-item {
      margin-bottom: 8px;
      border-bottom: 1px dashed #cbd5e1;
      padding-bottom: 6px;
      page-break-inside: avoid;
    }
    .qa-question {
      font-weight: 700;
      color: #1e293b;
      margin-bottom: 2px;
      display: flex;
      align-items: flex-start;
      gap: 6px;
    }
    .qa-question .q-tag {
      background: #e0e7ff;
      color: #3730a3;
      padding: 1px 5px;
      border-radius: 4px;
      font-size: 10px;
      font-weight: 700;
    }
    .qa-answer {
      color: #334155;
      padding-left: 26px;
      font-size: 12px;
      line-height: 1.45;
    }

    .page-break {
      page-break-before: always;
    }
    
    .footer {
      text-align: center;
      font-size: 10.5px;
      color: #64748b;
      margin-top: 12px;
      border-top: 1px solid #e2e8f0;
      padding-top: 6px;
    }
  </style>
</head>
<body>

  <!-- COVER PAGE -->
  <div class="cover">
    <div class="badge-top">AI-Powered Business Automation • Live Production</div>
    <h1>Raw Fabric Facebook AI Automation Bot</h1>
    <div class="subtitle">স্মার্ট ই-কমার্স অটোমেশন: লাইভ গুগল শিট ইনভেন্টরি, জেমিনাই ৩.৫ এআই ও ২৪/৭ ক্লাউড সিস্টেম</div>
    
    <div class="meta-grid">
      <div class="meta-item">
        <span>প্রেজেন্টার / ডেভেলপার</span>
        <strong>আবু হুরায়রা (Abu Huraira)</strong>
      </div>
      <div class="meta-item">
        <span>মডেল ও প্ল্যাটফর্ম</span>
        <strong>Gemini 3.5 Flash-Lite</strong>
      </div>
      <div class="meta-item">
        <span>ক্লাউড হোস্টিং</span>
        <strong>Render (24/7 Active)</strong>
      </div>
      <div class="meta-item">
        <span>প্রজেক্ট টাইপ</span>
        <strong>Full-Stack AI Automation</strong>
      </div>
    </div>
  </div>

  <!-- SECTION 1: 30-SECOND ELEVATOR PITCH -->
  <div class="section">
    <h2 class="section-title"><span class="icon">⚡</span> ৩০ সেকেন্ডের এলিভেটর পিচ (বক্তব্যের শুরু)</h2>
    <div class="pitch-quote">
      "সম্মানিত শিক্ষকবৃন্দ, বর্তমানে বাংলাদেশের লাখ লাখ ফেসবুক পেজের প্রধান সমস্যা হলো—কাস্টমার নক দিলে সময়মতো মানুষ উত্তর দিতে পারে না, আর গতানুগতিক বটগুলো রোবটের মতো বাটন দিয়ে কাস্টমারকে বিরক্ত করে।<br>
      আমাদের তৈরি <strong>Raw Fabric AI Automation Bot</strong> কাস্টমারের লেখার ধরণ—তা বাংলিশ, বাংলা বা ইংরেজি যাই হোক—হুবহু মানুষের মতো আন্তরিক ভঙ্গিতে অনুধাবন করে। এটি লাইভ গুগল শিটের ৫০টি পণ্যের তালিকা থেকে রিয়েল-টাইমে সঠিক দাম ও স্টক জানায়, পোস্ট কমেন্টে স্বয়ংক্রিয় রিপ্লাই দেয় এবং মেসেঞ্জারে কাস্টমারের নাম, ফোন নম্বর ও ঠিকানা যাচাই করে ক্যাশ অন ডেলিভারি অর্ডার চূড়ান্ত করে। সিস্টেমটি সম্পূর্ণ ফ্রিতে ২৪/৭ ক্লাউড সার্ভারে সক্রিয় থাকে।"
    </div>
  </div>

  <!-- SECTION 2: PROBLEM & SOLUTION -->
  <div class="section">
    <h2 class="section-title"><span class="icon">🎯</span> সমস্যা বনাম আমাদের সমাধান (Problem vs Solution)</h2>
    <div class="grid-2">
      <div class="card card-alert">
        <strong style="color: #991b1b; font-size: 13px;">❌ সনাতন ফেসবুক পেজের সীমাবদ্ধতা</strong>
        <ul style="margin: 4px 0 0 0; padding-left: 16px; line-height: 1.5;">
          <li><strong>দেরিতে উত্তর:</strong> রাতে বা ব্যস্ত সময়ে ৩-৪ ঘণ্টা পর উত্তর আসায় কাস্টমার অন্য পেজে চলে যায়।</li>
          <li><strong>রোবোটিক বাটন বিরক্তি:</strong> ManyChat বা ফিক্সড নিয়মে চলা চ্যাটবট মানুষের স্বাভাবিক কথা বোঝে না।</li>
          <li><strong>বাংলিশ ও ভুল বানান না বোঝা:</strong> <code>panjabi ache?</code> বা <code>dam koto</code> লিখলে সনাতন বট বিভ্রান্ত হয়।</li>
          <li><strong>ম্যানুয়াল ডাটা এন্ট্রি:</strong> ইনবক্সের ঠিকানা ও ফোন নম্বর দেখে খাতায় বা এক্সেলে তুলতে অনেক ভুল হয়।</li>
        </ul>
      </div>

      <div class="card card-highlight">
        <strong style="color: #166534; font-size: 13px;">✅ আমাদের স্বয়ংক্রিয় এআই সমাধান</strong>
        <ul style="margin: 4px 0 0 0; padding-left: 16px; line-height: 1.5;">
          <li><strong>ইনস্ট্যান্ট রেসপন্স:</strong> ১-২ সেকেন্ডে ২৪ ঘণ্টা দিন-রাত তাৎক্ষণিক মানবিক উত্তর প্রদান।</li>
          <li><strong>ভাষার টোন অনুকরণ:</strong> গ্রাহক যে ভাষায় বলে (বাংলিশ/বাংলা), বট হুবহু সেই টোনে উত্তর দেয়।</li>
          <li><strong>অ্যালিয়াস ও সিনোনিম ডিকশনারি:</strong> ৫০টি পণ্যের সকল বানানভেদ (panjabi, পাঞ্জাবী, tshirt, মানিব্যাগ) নির্ভুল চেনে।</li>
          <li><strong>স্বয়ংক্রিয় ক্যাশ অন ডেলিভারি ফানেল:</strong> ফোন, নাম, ঠিকানা ভ্যালিডেট করে গুগল শিট ও সিএসভিতে সেভ করে।</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- SECTION 3: SYSTEM ARCHITECTURE -->
  <div class="section">
    <h2 class="section-title"><span class="icon">🏗️</span> টেকনিক্যাল আর্কিটেকচার (Architecture & Flow)</h2>
    <div class="card card-tech">
      <table style="margin: 0;">
        <thead>
          <tr>
            <th style="width: 25%;">কম্পোনেন্ট</th>
            <th style="width: 25%;">ব্যবহৃত প্রযুক্তি</th>
            <th>ভূমিকা ও বিশেষত্ব</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Core Backend</strong></td>
            <td><span class="badge badge-blue">FastAPI (Python 3.12)</span></td>
            <td>হাই-স্পিড অ্যাসিনক্রোনাস ফ্রেমওয়ার্ক, মেটা ওয়েবহুক প্রসেসিং।</td>
          </tr>
          <tr>
            <td><strong>Generative AI</strong></td>
            <td><span class="badge badge-purple">Gemini 3.5 Flash-Lite</span></td>
            <td>Google AI Studio এপিআই; দ্রুত রেসপন্স ও বাংলা-বাংলিশ নিখুঁত অনুধাবন।</td>
          </tr>
          <tr>
            <td><strong>Live Inventory</strong></td>
            <td><span class="badge badge-green">Google Sheets API + CSV</span></td>
            <td>৫০টি পণ্যের স্টক ও মূল্য লাইভ সিঙ্ক; ৩ মিনিটের ক্যাশ টিটিএল (TTL)।</td>
          </tr>
          <tr>
            <td><strong>Meta Platform</strong></td>
            <td><span class="badge badge-blue">Facebook Graph API v21.0</span></td>
            <td>Webhooks: <code>messages</code>, <code>messaging_postbacks</code>, <code>feed</code> (Comments)।</td>
          </tr>
          <tr>
            <td><strong>24/7 Cloud Hosting</strong></td>
            <td><span class="badge badge-amber">Render.com + GitHub Actions</span></td>
            <td>সিঙ্গাপুর রিজিয়ন; শিডিউলড কিপ-অ্যালাইভ পিং দিয়ে সম্পূর্ণ জিরো-কস্টে সচল।</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <div class="page-break"></div>

  <!-- SECTION 4: 5 CORE TECHNICAL INNOVATIONS -->
  <div class="section">
    <h2 class="section-title"><span class="icon">⭐</span> প্রজেক্টের ৫টি শক্তিশালী উদ্ভাবন (Key Innovations)</h2>
    <div class="grid-2">
      <div class="card">
        <strong>১. নন-টেমপ্লেট অ্যাডাপ্টিভ টোন (Adaptive Mirroring)</strong>
        <p style="margin: 3px 0 0 0; color: #475569;">কোনো কপি-পেস্ট স্ক্রিপ্ট নেই। কাস্টমার ফ্রেন্ডলি বাংলিশে লিখলে বটও চটপটে বাংলিশে রিপ্লাই দেয়; কাস্টমার ফরমাল বাংলায় লিখলে বটও শ্রদ্ধা জানিয়ে ফরমাল বাংলায় কথা বলে।</p>
      </div>
      <div class="card">
        <strong>২. স্মার্ট ৫০-প্রোডাক্ট সিনোনিম ও বিভক্তি কাটার ইঞ্জিন</strong>
        <p style="margin: 3px 0 0 0; color: #475569;">বাঙালি গ্রাহকরা বিভক্তি যুক্ত করে লেখে (যেমন: <em>পাঞ্জাবির, টিশার্টের, চিনোটা</em>)। বট স্বয়ংক্রিয়ভাবে বিভক্তি বাদ দিয়ে এবং লুক-অ্যারাউন্ড রেগেক্স ব্যবহার করে ১০০% নির্ভুল পণ্য শনাক্ত করে।</p>
      </div>
      <div class="card">
        <strong>৩. বাংলা সংখ্যা নরম্যালাইজার (Bengali Digits Converter)</strong>
        <p style="margin: 3px 0 0 0; color: #475569;">কাস্টমার বাংলা কিবোর্ড দিয়ে <code>০১৮৬৯১৭১৮১৮</code> লিখলেও বট এটিকে <code>01869171818</code>-এ কনভার্ট করে সঠিক ১১ ডিজিট মোবাইল নম্বর যাচাই করে অর্ডার লিপিবদ্ধ করে।</p>
      </div>
      <div class="card">
        <strong>৪. ডুয়াল কমেন্ট অটোমেশন (Public + Private Reply)</strong>
        <p style="margin: 3px 0 0 0; color: #475569;">ফেসবুক পোস্টের নিচে কাস্টমার কমেন্ট করলে সাথে সাথে কমেন্টে অমায়িক পাবলিক রিপ্লাই দেয় এবং একই সাথে কাস্টমারের মেসেঞ্জার ইনবক্সে বিস্তারিত ও অর্ডার লিংক পাঠিয়ে দেয়।</p>
      </div>
    </div>
  </div>

  <!-- SECTION 5: LIVE DEMO CHEAT SHEET -->
  <div class="section">
    <h2 class="section-title"><span class="icon">📱</span> লাইভ ডেমো কৌশল (The Live Demo Master Script)</h2>
    <p style="margin-top: 0; margin-bottom: 6px;">প্রেজেন্টেশনে মোবাইল দিয়ে সরাসরি আপনার পেজের মেসেঞ্জারে মেসেজ পাঠিয়ে এই ৪টি টেস্ট দর্শকদের সামনে প্রমাণ করুন:</p>
    
    <table>
      <thead>
        <tr>
          <th style="width: 20%;">টেস্ট ধাপ</th>
          <th style="width: 35%;">কাস্টমার হিসেবে যা লিখবেন</th>
          <th>বট যা করে দেখাবে (প্রমাণ)</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>১. বাংলিশ প্রশ্ন</strong></td>
          <td><code>vai navy blue shirt ki hobe? dam koto?</code></td>
          <td>এআই বাংলিশে উত্তর দেবে এবং ৪৫০/৮৫০ টাকার আসল দাম নিশ্চিত করবে।</td>
        </tr>
        <tr>
          <td><strong>২. বানানভেদ টেস্ট</strong></td>
          <td><code>পাঞ্জাবী আছে ভাইয়া? ডেলিভারি কত?</code></td>
          <td>'পাঞ্জাবী' চিনে ফরমাল পাঞ্জাবির দাম ২২০০ টাকা ও ঢাকার চার্জ ৬০ টাকা জানাবে।</td>
        </tr>
        <tr>
          <td><strong>৩. এক বাক্যে অর্ডার</strong></td>
          <td><code>আমার নাম তানভীর, ফোন ০১৮৬৯১৭১৮১৮, ধানমন্ডি ৩২ এ পাঠান</code></td>
          <td>বাংলা সংখ্যা থেকে মোবাইল ও ঠিকানা এক্সট্র্যাক্ট করে অর্ডার সামারি দেবে।</td>
        </tr>
        <tr>
          <td><strong>৪. কনফার্মেশন</strong></td>
          <td><code>হ্যাঁ কনফার্ম করেন</code></td>
          <td>অর্ডার ফাইনাল করে জানাবে এবং ডাটাবেজ ফাইলে নতুন রো যোগ হবে।</td>
        </tr>
      </tbody>
    </table>
  </div>

  <!-- SECTION 6: VIVA / DEFENSE Q&A -->
  <div class="section">
    <h2 class="section-title"><span class="icon">🎓</span> ভাইভা ও ডিফেন্স প্রশ্নোত্তর (Top 5 Viva Questions)</h2>
    
    <div class="qa-item">
      <div class="qa-question">
        <span class="q-tag">প্রশ্ন ১</span> ManyChat বা ফেসবুকের বিল্ট-ইন অটোমেশনের চেয়ে আপনার সিস্টেম কেন আধুনিক?
      </div>
      <div class="qa-answer">
        <strong>উত্তর:</strong> সনাতন বটের সব উত্তর ফিক্সড বাটন বা রুলসে বাঁধা থাকে। গ্রাহক একটু ঘুরিয়ে প্রশ্ন করলেই তারা ব্যর্থ হয়। আমাদের সিস্টেমটি <strong>Google Gemini 3.5 Generative AI</strong> ব্যবহার করে। এটি মানুষের আবেগ, ভাষা ও জটিল প্রশ্নের প্রেক্ষাপট বুঝে কাস্টমাইজড উত্তর দেয় এবং সরাসরি গুগল শিট ইনভেন্টরির সাথে সংযুক্ত।
      </div>
    </div>

    <div class="qa-item">
      <div class="qa-question">
        <span class="q-tag">প্রশ্ন ২</span> গুগলের এআই যদি কখনো ইন্টারনেট ধীরগতির কারণে ডাউন থাকে, তখন কী হবে?
      </div>
      <div class="qa-answer">
        <strong>উত্তর:</strong> আমরা সিস্টেমে একটি <strong>Smart Fallback Engine</strong> তৈরি করেছি। এআই সাময়িক ফেইল করলেও আমাদের লোকাল ৫০টি পণ্যের সিনোনিম ও রেগেক্স ম্যাচিং ইঞ্জিন স্বয়ংক্রিয়ভাবে দায়িত্ব নিয়ে কাস্টমারকে সঠিক দাম, স্টক ও ডেলিভারির তথ্য দিয়ে অর্ডার নিয়ে নেবে।
      </div>
    </div>

    <div class="qa-item">
      <div class="qa-question">
        <span class="q-tag">প্রশ্ন ৩</span> আপনার কম্পিউটার বন্ধ রাখলে বট কীভাবে কাজ করছে?
      </div>
      <div class="qa-answer">
        <strong>উত্তর:</strong> সিস্টেমটিকে আমরা <strong>Render ক্লাউড সার্ভারে</strong> লাইভ হোস্ট করেছি এবং <strong>GitHub Actions</strong> দিয়ে ১০ মিনিট পর পর অটো-পিং চালু রেখেছি। ফলে পিসি, ইন্টারনেট বন্ধ থাকলেও ক্লাউড সার্ভার আজীবন ২৪ ঘণ্টা সজাগ থাকে।
      </div>
    </div>

    <div class="qa-item">
      <div class="qa-question">
        <span class="q-tag">প্রশ্ন ৪</span> গুগল শিটে নতুন পণ্য যোগ করলে কোডে কি কোনো পরিবর্তন করতে হয়?
      </div>
      <div class="qa-answer">
        <strong>উত্তর:</strong> না স্যার! আমাদের সিস্টেমে <strong>3-minute Cache TTL</strong> মেকানিজম রয়েছে। গুগল শিটে মালিক নতুন প্রোডাক্ট বা দাম পরিবর্তন করলে ৩ মিনিটের মধ্যে বট স্বয়ংক্রিয়ভাবে নতুন ডাটা রিফ্রেশ করে নেয়। কোনো কোড বা সার্ভার রিস্টার্টের প্রয়োজন নেই।
      </div>
    </div>
  </div>

  <div class="footer">
    Raw Fabric AI E-commerce Automation System • Developed by Abu Huraira • Powered by FastAPI & Google Gemini AI
  </div>

</body>
</html>
"""

html_path = os.path.abspath("FB_Bot_Presentation_and_Defense_Guide.html")
pdf_path = os.path.abspath("FB_Bot_Presentation_and_Defense_Guide.pdf")

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_code)
print(f"HTML generated: {html_path}")

# Generate PDF using Microsoft Edge headless
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if not os.path.exists(edge_path):
    edge_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

cmd = [
    edge_path,
    "--headless",
    "--disable-gpu",
    "--run-all-compositor-stages-before-draw",
    f"--print-to-pdf={pdf_path}",
    html_path
]

res = subprocess.run(cmd, capture_output=True, text=True)
if os.path.exists(pdf_path):
    print(f"PDF generated successfully: {pdf_path} ({os.path.getsize(pdf_path)} bytes)")
else:
    print(f"PDF generation failed: {res.stderr}")
