import wikipedia
import python_weather
import asyncio
import requests
import ollama
import os
import yfinance as yf
from ddgs import DDGS  
from datetime import datetime
from scrapy import Selector

wikipedia.set_lang("en")
messages = []

def search_wikipedia(query):
    
    try:
        return wikipedia.summary(query, sentences=2)
    except Exception:
        
        url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + query.replace(" ", "_")
        headers = {"User-Agent": "MyPythonBot/1.0"}
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                return response.json().get("extract", "No summary found.")
        except:
            return "No information found on Wikipedia."
    return "Error searching Wikipedia."

def reset_memory():
    global messages
    messages = []

def generate_chat_title(text):
    words = text.split()
    return "_".join(words[:3]) if len(words) > 0 else "Untitled_Chat"

def search_web(query, max_results=5):
    results = []
    try:
        with DDGS() as ddgs:
            search_results = list(ddgs.text(query, max_results=max_results))
            for r in search_results:
                results.append(f"{r['title']}\n{r['body']}\n{r['href']}\n")
            
            if search_results:
                
                try:
                    html = requests.get(search_results[0]['href'], timeout=5).text
                    sel = Selector(text=html)
                    scraped_text = " ".join(sel.xpath("//p//text()").getall())
                    results.append("\n--- SCRAPED CONTENT ---\n")
                    results.append(scraped_text[:800])
                except:
                    pass
        return "\n".join(results) if results else "No results found on the web."
    except Exception as e:
        return f"DDGS Error: {str(e)}"

def get_stock_price(symbol):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        currency = info.get("currency", "USD")
        name = info.get("shortName", symbol)
        
        if price:
            return f"📈 {name}: {price} {currency}"
        return "No price found for this symbol."
    except Exception as e:
        return f"Stock Error: {str(e)}"

async def get_weather(location):
    try:
        async with python_weather.Client(unit=python_weather.METRIC) as client:
            weather = await client.get(location)
            return f"The weather in {location}: {weather.temperature}°C, {weather.description}"
    except Exception as e:
        return f"Weather Error: {str(e)}"

def save_log(user, bot, chat_file=None):
    base_folder = os.path.join(os.path.dirname(__file__), "chats")
    if not os.path.exists(base_folder):
        os.makedirs(base_folder)

    file_path = os.path.join(base_folder, chat_file if chat_file else "chat_history.txt")
    
    with open(file_path, "a", encoding="utf-8") as f:
        time = datetime.now().strftime("%H:%M:%S")
        f.write(f"[{time}] You: {user}\n[{time}] Bot: {bot}\n\n")

def get_response(user_input):
    global messages
    user_input_lower = user_input.lower().strip()
    
    
    if "talk in romanian" in user_input_lower:
        wikipedia.set_lang("ro")
        messages.append({"role": "system", "content": "Răspunde doar în limba română."})
        return "Am schimbat limba la română."

    if user_input_lower.startswith("search with wikipedia "):
        return search_wikipedia(user_input[22:])

    if user_input_lower.startswith("what is the weather in "):
        return asyncio.run(get_weather(user_input[23:]))

    if user_input_lower.startswith("search with web "):
        return search_web(user_input[16:])

    if user_input_lower.startswith(("what is ", "who is ")):
        parts = user_input.split(" ", 2)
        if len(parts) > 2:
            return search_wikipedia(parts[2])

    if user_input_lower.startswith("stock "):
        return get_stock_price(user_input[6:].upper())

    
    try:
        messages.append({"role": "user", "content": user_input})
        response = ollama.chat(model="llama3.2:3b", messages=messages)
        bot_response = response["message"]["content"]
        messages.append({"role": "assistant", "content": bot_response})
        return bot_response
    except Exception as e:
        return f"Ollama Error: {str(e)}. Make sure Ollama is running and the model is available."