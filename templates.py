"""SAVEONSUB unified templates — ONE nav, ONE footer per language. Every build script imports this.
Edit here, rebuild all, and every single page gets the update. Zero drift."""
import html

def esc(s): return html.escape(str(s), quote=True)

# ===== ENGLISH NAV =====
def nav_en(rel=""):
    return f'''<nav><div class="wrap navin">
  <a class="logo" href="{rel}index.html">SAVE<em>ON</em>SUB</a>
  <div class="navlinks">
    <a href="{rel}all.html">Subscriptions</a>
    <div class="navdrop">
      <a href="{rel}all.html#categories" class="dropbtn">Categories ▾</a>
      <div class="dropmenu">
        <a href="{rel}c/ai-assistants.html">🤖 AI Assistants</a>
        <a href="{rel}c/ai-image-design.html">🎨 Image &amp; Design</a>
        <a href="{rel}c/ai-video.html">🎬 AI Video</a>
        <a href="{rel}c/ai-voice-music.html">🎙️ Voice &amp; Music</a>
        <a href="{rel}c/ai-code-dev.html">💻 Code &amp; Dev</a>
        <a href="{rel}c/ai-writing.html">✍️ AI Writing</a>
        <a href="{rel}c/workspace-productivity.html">🗂️ Workspace</a>
        <a href="{rel}c/entertainment.html">🍿 Entertainment</a>
        <a href="{rel}c/education-career.html">🎓 Education</a>
        <a href="{rel}c/vpn-security.html">🔒 VPN</a>
        <a href="{rel}c/bundles.html">🎁 Bundles</a>
      </div>
    </div>
    <a href="{rel}all.html#bundles">Bundles</a>
    <a href="{rel}quiz.html">Find My AI</a>
    <a href="{rel}blog/index.html">Guides</a>
    <a href="{rel}faq.html">FAQ</a>
  </div>
  <div class="navright">
    <a href="{rel}track.html" class="navtrack">📦 Track</a>
    <button class="cartbtn" onclick="location.href='{rel}checkout.html'" aria-label="Cart">🛒<span class="cartn" style="display:none">0</span></button>
    <button class="hamb" onclick="navToggle()" aria-label="Menu">☰</button>
  </div>
</div></nav>'''

# ===== ENGLISH FOOTER (5-column) =====
def footer_en(rel=""):
    return f'''<footer><div class="wrap">
  <div class="fcols">
    <div>
      <span class="logo">SAVE<em>ON</em>SUB</span>
      <p style="margin-top:10px;max-width:280px">Bangladesh's Subscription Operating System — official, customer-owned subscriptions paid in BDT — Dhaka, Bangladesh.</p>
    </div>
    <div>
      <b>Store</b>
      <a href="{rel}all.html">All products</a>
      <a href="{rel}all.html#bundles">Bundles</a>
      <a href="{rel}quiz.html">Find My AI</a>
      <a href="{rel}blog/index.html">Guides</a>
      <a href="{rel}offers.html">Offers</a>
    </div>
    <div>
      <b>Help</b>
      <a href="{rel}how-to-order.html">How to order</a>
      <a href="{rel}track.html">Track order</a>
      <a href="{rel}contact.html">Contact</a>
      <a href="{rel}students.html">Student Zone</a>
    </div>
    <div>
      <b>Trust</b>
      <a href="{rel}warranty.html">Warranty</a>
      <a href="{rel}refund.html">Refund</a>
      <a href="{rel}faq.html">FAQ</a>
      <a href="{rel}privacy.html">Privacy</a>
      <a href="{rel}terms.html">Terms</a>
      <a href="{rel}sitemap.html">Sitemap</a>
    </div>
    <div>
      <b>Company</b>
      <a href="{rel}about.html">About us</a>
      <a href="https://wa.me/8801305869242">WhatsApp</a>
      <a href="mailto:support@saveonsub.com">Email</a>
    </div>
  </div>
  <p class="fine">&copy; 2026 SAVEONSUB &middot; . All product names and trademarks belong to their owners. Official prices shown for comparison — verify using official links on product pages.</p>
</div></footer>'''

# ===== BANGLA NAV (with dropdown categories) =====
def nav_bn(rel=""):
    return f'''<nav><div class="wrap navin">
  <a class="logo" href="{rel}bn.html">SAVE<em>ON</em>SUB</a>
  <div class="navlinks">
    <a href="{rel}all.html">সাবস্ক্রিপশন</a>
    <div class="navdrop">
      <a href="{rel}all.html#categories" class="dropbtn">ক্যাটাগরি ▾</a>
      <div class="dropmenu">
        <a href="{rel}c/ai-assistants.html">🤖 এআই অ্যাসিস্ট্যান্ট</a>
        <a href="{rel}c/ai-image-design.html">🎨 ইমেজ ও ডিজাইন</a>
        <a href="{rel}c/ai-video.html">🎬 এআই ভিডিও</a>
        <a href="{rel}c/ai-voice-music.html">🎙️ ভয়েস ও মিউজিক</a>
        <a href="{rel}c/ai-code-dev.html">💻 কোডিং</a>
        <a href="{rel}c/ai-writing.html">✍️ এআই রাইটিং</a>
        <a href="{rel}c/workspace-productivity.html">🗂️ ওয়ার্কস্পেস</a>
        <a href="{rel}c/entertainment.html">🍿 স্ট্রিমিং</a>
        <a href="{rel}c/education-career.html">🎓 শিক্ষা</a>
        <a href="{rel}c/vpn-security.html">🔒 ভিপিএন</a>
        <a href="{rel}c/bundles.html">🎁 বান্ডেল</a>
      </div>
    </div>
    <a href="{rel}all.html#bundles">বান্ডেল</a>
    <a href="{rel}quiz.html">কুইজ</a>
    <a href="{rel}blog/index.html">গাইড</a>
    <a href="{rel}faq.html">প্রশ্নোত্তর</a>
  </div>
  <div class="navright">
    <a href="{rel}track.html" class="navtrack">📦 ট্র্যাক</a>
    <button class="cartbtn" onclick="location.href='{rel}checkout.html'" aria-label="কার্ট">🛒<span class="cartn" style="display:none">0</span></button>
    <button class="hamb" onclick="navToggle()" aria-label="মেনু">☰</button>
  </div>
</div></nav>'''

# ===== BANGLA FOOTER =====
def footer_bn(rel=""):
    return f'''<footer><div class="wrap">
  <div class="fcols">
    <div>
      <span class="logo">SAVE<em>ON</em>SUB</span>
      <p style="margin-top:10px;max-width:280px">বাংলাদেশের সাবস্ক্রিপশন অপারেটিং সিস্টেম — অফিসিয়াল, গ্রাহক-নিয়ন্ত্রিত সাবস্ক্রিপশন — ঢাকা, বাংলাদেশ।</p>
    </div>
    <div>
      <b>স্টোর</b>
      <a href="{rel}all.html">সব প্রোডাক্ট</a>
      <a href="{rel}all.html#bundles">বান্ডেল</a>
      <a href="{rel}quiz.html">কুইজ</a>
      <a href="{rel}blog/index.html">গাইড</a>
      <a href="{rel}offers.html">অফার</a>
    </div>
    <div>
      <b>সাহায্য</b>
      <a href="{rel}how-to-order.html">কীভাবে অর্ডার</a>
      <a href="{rel}track.html">অর্ডার ট্র্যাক</a>
      <a href="{rel}contact.html">যোগাযোগ</a>
      <a href="{rel}students.html">স্টুডেন্ট</a>
    </div>
    <div>
      <b>ভরসা</b>
      <a href="{rel}warranty.html">ওয়ারেন্টি</a>
      <a href="{rel}refund.html">রিফান্ড</a>
      <a href="{rel}faq.html">প্রশ্নোত্তর</a>
      <a href="{rel}sitemap.html">সাইটম্যাপ</a>
    </div>
    <div>
      <b>কোম্পানি</b>
      <a href="{rel}about.html">আমাদের সম্পর্কে</a>
      <a href="https://wa.me/8801305869242">হোয়াটসঅ্যাপ</a>
    </div>
  </div>
  <p class="fine">&copy; 2026 SAVEONSUB &middot; । সব প্রোডাক্টের নাম ও ট্রেডমার্ক তাদের মালিকদের।</p>
</div></footer>'''

# ===== COMMON HEAD ELEMENTS =====
def head_common(rel=""):
    return f'''<link rel="icon" href="{rel}assets/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{rel}assets/apple-touch-icon.png">
<link rel="manifest" href="{rel}assets/site.webmanifest">
<meta property="og:image" content="https://saveonsub.com/assets/og-image.png">
<link rel="stylesheet" href="{rel}assets/style.css">'''

# ===== FLOATING BUTTONS =====
def fabs_en(rel=""):
    return f'''<button class="fab fab-wa" onclick="location.href='https://wa.me/8801305869242?text=Hi!'" aria-label="WhatsApp">💬 WhatsApp</button>
<a class="fab fab-quiz" href="{rel}quiz.html" aria-label="Find my AI quiz">🧭 Find My AI</a>'''

def fabs_bn(rel=""):
    return f'''<button class="fab fab-wa" onclick="location.href='https://wa.me/8801305869242?text=Hi!'" aria-label="হোয়াটসঅ্যাপ">💬 হোয়াটসঅ্যাপ</button>
<a class="fab fab-quiz" href="{rel}quiz.html" aria-label="কুইজ">🧭 কুইজ</a>'''

# ===== PAGE SHELL (for trust pages) =====
PAGE_SHELL_EN = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="https://saveonsub.com/{slug}.html">
<link rel="alternate" hreflang="en-bd" href="https://saveonsub.com/{slug}.html">
<link rel="alternate" hreflang="bn-bd" href="https://saveonsub.com/{bn_slug}">
<link rel="alternate" hreflang="x-default" href="https://saveonsub.com/{slug}.html">
<meta name="geo.region" content="BD"><meta name="geo.placename" content="Dhaka">
<meta property="og:title" content="{title}"><meta property="og:description" content="{desc}">
<meta property="og:type" content="website"><meta property="og:url" content="https://saveonsub.com/{slug}.html">
<meta property="og:locale" content="en_BD">
<meta name="theme-color" content="#06181a">{robots}
''' + head_common('') + '''
{schema}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
''' + nav_en() + '''
<main id="main"><div class="wrap" style="max-width:820px">
  <div class="crumbs"><a href="index.html">Home</a> › {crumb}</div>
  {body}
</div></main>
''' + fabs_en() + '''
''' + footer_en() + '''
<script src="assets/app.js"></script>
</body>
</html>'''

PAGE_SHELL_BN = '''<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="https://saveonsub.com/{slug}">
<link rel="alternate" hreflang="bn-bd" href="https://saveonsub.com/{slug}">
<link rel="alternate" hreflang="en-bd" href="https://saveonsub.com/{en_slug}">
<link rel="alternate" hreflang="x-default" href="https://saveonsub.com/{en_slug}">
<meta name="geo.region" content="BD"><meta name="geo.placename" content="Dhaka">
<meta property="og:title" content="{title}"><meta property="og:description" content="{desc}">
<meta property="og:type" content="website"><meta property="og:url" content="https://saveonsub.com/{slug}">
<meta property="og:locale" content="bn_BD">
<meta name="theme-color" content="#06181a">{robots}
''' + head_common('../') + '''
{schema}
</head>
<body>
<a class="skip" href="#main">মূল কন্টেন্টে যান</a>
''' + nav_bn('../') + '''
<main id="main"><div class="wrap" style="max-width:820px">
  <div class="crumbs"><a href="../bn.html">হোম</a> › {crumb}</div>
  {body}
</div></main>
''' + fabs_bn('../') + '''
''' + footer_bn('../') + '''
<script src="../assets/app.js"></script>
</body>
</html>'''
