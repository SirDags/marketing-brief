import feedparser
import requests
from datetime import datetime, timedelta
import time
import os

# Securely pulls key from GitHub Secrets in the cloud, defaulting to local string if run offline
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "cc8cb909596d4316b825653bb7496faf")
MY_CLIENTS = ["specsavers", "kerrygold", "bus eireann", "o'briens wines"]

rss_feeds = {
    "AdWorld Ireland": "https://www.adworld.ie/feed/",
    "ThinkBusiness IE": "https://www.thinkbusiness.ie/feed/",
    "The Drum UK": "https://www.thedrum.com/news/feed",
    "MarketingTech Global": "https://www.marketingtechnews.net/feed/",
    "Performance Marketing World": "https://www.performancemarketingworld.com/rss",
    "Digital News Asia": "https://www.digitalnewsasia.com/feed"
}

all_articles = []
social_posts = []

# Helper utility to parse various RSS date formats safely into ISO strings
def parse_rss_date(entry):
    try:
        if 'published_parsed' in entry and entry.published_parsed:
            return time.strftime('%Y-%m-%d', entry.published_parsed)
        elif 'updated_parsed' in entry and entry.updated_parsed:
            return time.strftime('%Y-%m-%d', entry.updated_parsed)
    except:
        pass
    return datetime.utcnow().strftime('%Y-%m-%d')

# --- EXTRACT STANDARD RSS FEEDS ---
print("Extracting live industry RSS arrays...")
for source_name, url in rss_feeds.items():
    try:
        parsed_feed = feedparser.parse(url)
        for article in parsed_feed.entries[:10]:
            all_articles.append({
                "title": article.title,
                "link": article.link,
                "source": source_name,
                "date": parse_rss_date(article)
            })
    except:
        pass

# --- EXTRACT TARGETED GOOGLE BRAND NEWS ---
print("Querying Google News RSS parameters for active brands...")
for client in MY_CLIENTS:
    formatted_query = client.replace(" ", "+")
    google_rss_url = f"https://news.google.com/rss/search?q={formatted_query}+marketing+OR+advertising&hl=en-IE&gl=IE&ceid=IE:en"
    try:
        google_feed = feedparser.parse(google_rss_url)
        for entry in google_feed.entries[:5]:
            clean_link = entry.link
            try:
                r = requests.head(entry.link, timeout=3, allow_redirects=True)
                if r.url: clean_link = r.url
            except: pass
            all_articles.append({
                "title": entry.title,
                "link": clean_link,
                "source": "Google News Index",
                "date": parse_rss_date(entry)
            })
    except:
        pass

# --- EXTRACT GLOBAL API DATA ---
print("Querying global advertising news streams from NewsAPI...")
if NEWS_API_KEY and NEWS_API_KEY != "YOUR_API_KEY_HERE":
    api_url = f"https://newsapi.org/v2/everything?q=advertising+OR+marketing&language=en&sortBy=publishedAt&pageSize=30&apiKey={NEWS_API_KEY}"
    try:
        response = requests.get(api_url).json()
        if "articles" in response:
            for article in response["articles"]:
                if article["title"] and "[Removed]" not in article["title"]:
                    iso_date = article["publishedAt"][:10] if article["publishedAt"] else datetime.utcnow().strftime('%Y-%m-%d')
                    all_articles.append({
                        "title": article["title"],
                        "link": article["url"],
                        "source": article["source"]["name"],
                        "date": iso_date
                    })
    except:
        pass

# --- EXTRACT SOCIAL CHANNELS & REDDIT ---
print("Scouring public social channels and Reddit communities...")
for client in MY_CLIENTS:
    formatted_query = client.replace(" ", "+")
    
    # 1. Reddit Conversations
    reddit_rss = f"https://www.reddit.com/search.rss?q={formatted_query}&sort=new"
    try:
        reddit_feed = feedparser.parse(reddit_rss)
        for entry in reddit_feed.entries[:5]:
            social_posts.append({
                "title": entry.title,
                "link": entry.link,
                "source": "Reddit Discussion",
                "client": client,
                "date": parse_rss_date(entry)
            })
    except:
        pass

    # 2. Google Indexed Social Profiles
    social_index_url = f"https://news.google.com/rss/search?q={formatted_query}+(site:twitter.com+OR+site:x.com+OR+site:instagram.com+OR+site:linkedin.com+OR+site:youtube.com)&hl=en-IE&gl=IE&ceid=IE:en"
    try:
        social_feed = feedparser.parse(social_index_url)
        for entry in social_feed.entries[:5]:
            clean_link = entry.link
            try:
                r = requests.head(entry.link, timeout=3, allow_redirects=True)
                if r.url: clean_link = r.url
            except: pass
            
            platform = "Social Post"
            if "x.com" in clean_link or "twitter.com" in clean_link: platform = "X / Twitter"
            elif "linkedin.com" in clean_link: platform = "LinkedIn Insight"
            elif "youtube.com" in clean_link: platform = "YouTube Video"
            elif "instagram.com" in clean_link: platform = "Instagram Link"

            social_posts.append({
                "title": entry.title,
                "link": clean_link,
                "source": platform,
                "client": client,
                "date": parse_rss_date(entry)
            })
    except:
        pass

# --- GENERATE CODE TEMPLATES WITH DATA-DATE ATTRIBUTES ---
industry_cards_html = ""
card_counter = 0
for article in all_articles:
    title = article["title"]
    link = article["link"]
    source = article["source"]
    pub_date = article["date"]
    title_lower = title.lower()
    
    if any(word in title_lower for word in ["ireland", "dublin", "irish", "cork", "rte", "asai", "specsavers", "kerrygold", "ornua", "bus eireann", "o'briens"]):
        country, flag = "IE", "🇮🇪"
    elif any(word in title_lower for word in ["uk", "london", "europe", "bbc", "manchester", "drum"]):
        country, flag = "UK", "🇬🇧"
    elif any(word in title_lower for word in ["singapore", "asia", "apac", "tokyo", "china", "india"]):
        country, flag = "ASIA", "🌏"
    else:
        country, flag = "US", "🇺🇸"
        
    card_counter += 1
    if card_counter == 1:
        industry_cards_html += f"""
        <div data-country="{country}" data-date="{pub_date}" class="news-card bg-white rounded-3xl overflow-hidden shadow-sm hover:shadow-xl transition-all duration-300 border border-gray-200 md:col-span-2 lg:col-span-3 flex flex-col lg:flex-row min-h-[350px]">
            <div class="bg-slate-900 lg:w-1/2 p-8 flex flex-col justify-between text-white border-b lg:border-b-0 lg:border-r border-gray-800">
                <div><span class="bg-red-600 text-white px-3 py-1 rounded-full text-xs font-bold uppercase tracking-widest">Featured Brief</span><p class="text-xs text-slate-400 mt-4 font-mono">{source} • {pub_date}</p></div>
                <div class="text-xs font-semibold text-red-500 tracking-wider mt-4">{flag} PRIMARY CONTEXT: {country}</div>
            </div>
            <div class="p-8 flex flex-col justify-between lg:w-1/2 bg-gradient-to-br from-white to-slate-50">
                <div>
                    <h2 class="text-2xl md:text-3xl font-serif font-black text-slate-900 tracking-tight leading-tight hover:text-red-600 transition-colors"><a href="{link}" target="_blank">{title}</a></h2>
                    <p class="text-slate-600 text-sm mt-4 leading-relaxed font-sans">Top dynamic market brief overview. Inspect source metrics directly via standard hub link anchors.</p>
                </div>
                <div class="pt-4 border-t border-slate-100 mt-6 text-xs text-slate-400 font-mono">Priority Direct Delivery // Dublin HQ</div>
            </div>
        </div>"""
    else:
        industry_cards_html += f"""
        <div data-country="{country}" data-date="{pub_date}" class="news-card bg-white rounded-2xl overflow-hidden shadow-sm hover:shadow-md transition-all duration-200 border border-gray-200 flex flex-col justify-between p-6">
            <div>
                <div class="flex justify-between items-start gap-2"><span class="text-xs font-mono text-slate-400 uppercase tracking-wider">{source} • {pub_date}</span><span class="text-base">{flag}</span></div>
                <h2 class="text-lg font-bold font-serif text-slate-900 mt-3 hover:text-red-600 transition-colors leading-snug"><a href="{link}" target="_blank">{title}</a></h2>
            </div>
            <div class="pt-4 border-t border-gray-100 mt-6 flex justify-between items-center text-xs font-mono text-slate-400"><span>Region: {country}</span><span class="bg-slate-100 px-2 py-0.5 rounded text-slate-600 font-sans text-[10px] font-bold">READ →</span></div>
        </div>"""

client_rows_html = ""
for client in MY_CLIENTS:
    client_articles_html = ""
    for article in all_articles:
        if client in article["title"].lower() or ("ornua" in article["title"].lower() and client == "kerrygold"):
            country = "IE" if any(w in article["title"].lower() for w in ["ireland", "dublin", "irish", "specsavers", "kerrygold", "bus eireann", "o'briens"]) else "US"
            client_articles_html += f"""
            <div data-country="{country}" data-date="{article["date"]}" class="news-card bg-white rounded-2xl overflow-hidden shadow-sm hover:shadow-md transition-all duration-200 border border-gray-200 flex flex-col justify-between p-6">
                <div><div class="flex justify-between items-start gap-2"><span class="text-xs font-mono text-slate-400 uppercase tracking-wider">{article["source"]} • {article["date"]}</span></div><h2 class="text-lg font-bold font-serif text-slate-900 mt-3 hover:text-red-600 transition-colors leading-snug"><a href="{article["link"]}" target="_blank">{article["title"]}</a></h2></div>
                <div class="pt-4 border-t border-gray-100 mt-6 flex justify-between items-center text-xs font-mono text-slate-400"><span>Region: {country}</span><span class="bg-slate-100 px-2 py-0.5 rounded text-slate-600 font-sans text-[10px] font-bold">READ →</span></div>
            </div>"""
    
    label_decor = {"specsavers": "🟢 Specsavers Accounts", "kerrygold": "🟡 Kerrygold // Ornua Portfolio", "bus eireann": "🔴 Bus Éireann Accounts", "o'briens wines": "🍇 O'Briens Wines"}
    client_rows_html += f"""
    <div class="client-brand-row border-b border-slate-200 pb-8 last:border-0">
        <h3 class="text-sm font-mono tracking-widest text-slate-400 uppercase mb-4">{label_decor.get(client, client.upper())}</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 empty:after:content-['No_live_developments_identified_within_this_cross-section_filter.'] empty:after:text-xs empty:after:font-sans empty:after:italic empty:after:text-slate-400 empty:after:py-4">{client_articles_html}</div>
    </div>"""

social_rows_html = ""
for client in MY_CLIENTS:
    social_cards_html = ""
    for post in social_posts:
        if post["client"] == client:
            social_cards_html += f"""
            <div data-date="{post["date"]}" class="news-card bg-slate-900 text-white rounded-2xl shadow-xs border border-slate-800 flex flex-col justify-between p-6 hover:border-red-500 transition-all">
                <div>
                    <div class="flex justify-between items-center"><span class="text-[10px] font-mono uppercase bg-slate-800 text-slate-300 px-2.5 py-1 rounded-md font-bold tracking-wider">💬 {post["source"]} • {post["date"]}</span><span class="text-xs text-slate-500 font-mono">LIVE FEED</span></div>
                    <h2 class="text-base font-medium font-sans mt-4 text-slate-100 hover:text-red-400 transition-colors leading-snug"><a href="{post["link"]}" target="_blank">{post["title"]}</a></h2>
                </div>
                <div class="pt-4 border-t border-slate-800 mt-6 flex justify-end text-[10px] font-mono text-slate-500"><span>VIEW SOURCE POST →</span></div>
            </div>"""
            
    label_decor = {"specsavers": "💬 Specsavers Buzz", "kerrygold": "💬 Kerrygold Sentiment", "bus eireann": "💬 Bus Éireann Public Mentions", "o'briens wines": "💬 O'Briens Wines Social"}
    social_rows_html += f"""
    <div class="social-brand-row border-b border-slate-200 pb-8 last:border-0">
        <h3 class="text-sm font-mono tracking-widest text-slate-400 uppercase mb-4">{label_decor.get(client, client.upper())}</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 empty:after:content-['No_public_social_chatter_detected_on_open_channels_today.'] empty:after:text-xs empty:after:font-sans empty:after:italic empty:after:text-slate-400 empty:after:py-4">{social_cards_html}</div>
    </div>"""

# --- WEB UI RENDER WITH DYNAMIC DATE CONTROL SYSTEM ---
html_start = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Global Marketing Aggregator</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400..900;1,400..900&family=Plus+Jakarta+Sans:ital,wght@0,200..800;1,200..800&display=swap');
        body { font-family: 'Plus Jakarta Sans', sans-serif; }
        font-serif { font-family: 'Playfair Display', serif; }
    </style>
</head>
<body class="bg-slate-50/50 text-slate-900 min-h-screen antialiased">

    <header class="bg-white border-b border-slate-200 sticky top-0 z-50 px-8 py-4 flex flex-col xl:flex-row justify-between items-center gap-4 shadow-xs">
        <div class="flex flex-col md:flex-row items-center gap-6 w-full xl:w-auto">
            <div>
                <h1 class="text-2xl font-black tracking-tighter text-slate-900 font-serif">The <span class="text-red-600">AD</span>gregator</h1>
                <p class="text-[11px] font-mono uppercase tracking-widest text-slate-400 mt-0.5">Nico Dagdag Alpha Test</p>
            </div>
            
            <div class="flex bg-slate-100 p-1 rounded-xl border border-slate-200 w-full md:w-auto gap-1">
                <button id="view-industry" onclick="setViewMode('industry')" class="bg-white text-slate-900 px-4 py-2 rounded-lg text-xs font-bold shadow-xs cursor-pointer transition-all">📰 Industry News</button>
                <button id="view-clients" onclick="setViewMode('clients')" class="text-slate-600 px-4 py-2 rounded-lg text-xs font-semibold cursor-pointer hover:text-slate-900 transition-all">💼 Client Tracker</button>
                <button id="view-social" onclick="setViewMode('social')" class="text-slate-600 px-4 py-2 rounded-lg text-xs font-semibold cursor-pointer hover:text-slate-900 transition-all">🔥 Social Media</button>
            </div>
        </div>
        
        <div class="flex flex-wrap items-center gap-4">
            <!-- DATE RANGE PICKER -->
            <div class="flex bg-slate-100 p-1 rounded-xl border border-slate-200">
                <button id="date-all" onclick="filterDate('all')" class="date-btn bg-white text-slate-900 px-3 py-1.5 rounded-lg text-xs font-bold shadow-xs cursor-pointer">🕒 All Time</button>
                <button id="date-year" onclick="filterDate('year')" class="date-btn text-slate-600 px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer hover:bg-white/60 transition-all">Current Year</button>
                <button id="date-30" onclick="filterDate('30')" class="date-btn text-slate-600 px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer hover:bg-white/60 transition-all">Past 30d</button>
                <button id="date-7" onclick="filterDate('7')" class="date-btn text-slate-600 px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer hover:bg-white/60 transition-all">Past 7d</button>
            </div>

            <!-- REGIONAL SELECTOR -->
            <div class="flex bg-slate-100 p-1 rounded-xl border border-slate-200">
                <button id="loc-all" onclick="filterLocation('all')" class="loc-btn bg-white text-slate-900 px-4 py-1.5 rounded-lg text-xs font-bold shadow-xs cursor-pointer">🌐 Global</button>
                <button id="loc-IE" onclick="filterLocation('IE')" class="loc-btn text-slate-600 px-4 py-1.5 rounded-lg text-xs font-semibold cursor-pointer hover:bg-white/60 transition-all">🇮🇪 IE</button>
                <button id="loc-UK" onclick="filterLocation('UK')" class="loc-btn text-slate-600 px-4 py-1.5 rounded-lg text-xs font-semibold cursor-pointer hover:bg-white/60 transition-all">🇬🇧 UK</button>
                <button id="loc-US" onclick="filterLocation('US')" class="loc-btn text-slate-600 px-4 py-1.5 rounded-lg text-xs font-semibold cursor-pointer hover:bg-white/60 transition-all">🇺🇸 US</button>
                <button id="loc-ASIA" onclick="filterLocation('ASIA')" class="loc-btn text-slate-600 px-4 py-1.5 rounded-lg text-xs font-semibold cursor-pointer hover:bg-white/60 transition-all">🌏 ASIA</button>
            </div>
        </div>
    </header>

    <main class="max-w-7xl mx-auto p-6 p-8">"""

html_middle = f"""
        <div id="industry-view" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {industry_cards_html}
        </div>

        <div id="client-view" class="hidden space-y-12">
            {client_rows_html}
        </div>

        <div id="social-view" class="hidden space-y-12">
            {social_rows_html}
        </div>
"""

html_end = """</main>

    <script>
        let currentCountry = 'all';
        let currentMode = 'industry';
        let currentDateRange = 'all';

        const TODAY = new Date();

        function syncFilters() {
            const cards = document.querySelectorAll('.news-card');
            
            cards.forEach(card => {
                const cardCountry = card.getAttribute('data-country') || 'IE';
                const cardDateStr = card.getAttribute('data-date');
                
                let matchesCountry = (currentCountry === 'all' || cardCountry === currentCountry);
                let matchesDate = true;

                if (cardDateStr) {
                    const cardDate = new Date(cardDateStr);
                    const timeDiff = TODAY.getTime() - cardDate.getTime();
                    const daysDiff = Math.ceil(timeDiff / (1000 * 3600 * 24));

                    if (currentDateRange === 'year') {
                        matchesDate = (cardDate.getFullYear() === TODAY.getFullYear());
                    } else if (currentDateRange === '30') {
                        matchesDate = (daysDiff >= 0 && daysDiff <= 30);
                    } else if (currentDateRange === '7') {
                        matchesDate = (daysDiff >= 0 && daysDiff <= 7);
                    }
                }

                if (currentMode === 'industry') {
                    if (matchesCountry && matchesDate) {
                        card.style.display = 'flex';
                    } else {
                        card.style.display = 'none';
                    }
                } else {
                    if (matchesDate) {
                        card.style.display = 'flex';
                    } else {
                        card.style.display = 'none';
                    }
                }
            });
        }

        function setViewMode(mode) {
            currentMode = mode;
            const indView = document.getElementById('industry-view');
            const cliView = document.getElementById('client-view');
            const socView = document.getElementById('social-view');
            
            const indBtn = document.getElementById('view-industry');
            const cliBtn = document.getElementById('view-clients');
            const socBtn = document.getElementById('view-social');

            indView.classList.add('hidden');
            cliView.classList.add('hidden');
            socView.classList.add('hidden');
            
            indBtn.className = "text-slate-600 px-4 py-2 rounded-lg text-xs font-semibold cursor-pointer hover:text-slate-900 transition-all";
            cliBtn.className = "text-slate-600 px-4 py-2 rounded-lg text-xs font-semibold cursor-pointer hover:text-slate-900 transition-all";
            socBtn.className = "text-slate-600 px-4 py-2 rounded-lg text-xs font-semibold cursor-pointer hover:text-slate-900 transition-all";

            if (mode === 'industry') {
                indView.classList.remove('hidden');
                indBtn.className = "bg-white text-slate-900 px-4 py-2 rounded-lg text-xs font-bold shadow-xs cursor-pointer transition-all";
            } else if (mode === 'clients') {
                cliView.classList.remove('hidden');
                cliBtn.className = "bg-white text-slate-900 px-4 py-2 rounded-lg text-xs font-bold shadow-xs cursor-pointer transition-all";
            } else if (mode === 'social') {
                socView.classList.remove('hidden');
                socBtn.className = "bg-white text-slate-900 px-4 py-2 rounded-lg text-xs font-bold shadow-xs cursor-pointer transition-all";
            }
            syncFilters();
        }

        function filterLocation(countryCode) {
            currentCountry = countryCode;
            const buttons = document.querySelectorAll('.loc-btn');
            buttons.forEach(btn => {
                btn.className = "loc-btn text-slate-600 px-4 py-1.5 rounded-lg text-xs font-semibold cursor-pointer hover:bg-white/60 transition-all";
            });
            event.currentTarget.className = "loc-btn bg-white text-slate-900 px-4 py-1.5 rounded-lg text-xs font-bold shadow-xs cursor-pointer";
            syncFilters();
        }

        function filterDate(rangeCode) {
            currentDateRange = rangeCode;
            const buttons = document.querySelectorAll('.date-btn');
            buttons.forEach(btn => {
                btn.className = "date-btn text-slate-600 px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer hover:bg-white/60 transition-all";
            });
            event.currentTarget.className = "date-btn bg-white text-slate-900 px-3 py-1.5 rounded-lg text-xs font-bold shadow-xs cursor-pointer";
            syncFilters();
        }
    </script>

</body>
</html>"""

with open("index.html", "w", encoding="utf-8") as file:
    file.write(html_start + html_middle + html_end)

print("\nSuccess! GitHub cloud integration environment ready for deployment.")
