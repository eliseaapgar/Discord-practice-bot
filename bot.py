import discord
from discord.ext import commands
import config 
import requests
from bs4 import BeautifulSoup
from datetime import datetime


# Create bot instance with intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=config.COMMAND_PREFIX, intents=intents)

def scrape_franciscan():
    """Scrape saint information from Franciscan Media"""
    try:
        url = 'https://www.franciscanmedia.org/saint-of-the-day/'
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        
        print(f"Franciscan status: {response.status_code}")
        
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Debug: show what h1 tags exist
        all_h1 = soup.find_all('h1')
        print(f"Found {len(all_h1)} h1 tags")
        for h1 in all_h1:
            print(f"  h1: {h1.get('class')} - {h1.get_text()[:50]}")
        
        name_tag = soup.find('h1', class_='entry-title')
        print(f"Name tag with class='entry-title': {name_tag}")
        
        saint_name = name_tag.get_text().strip() if name_tag else None
        
        content_div = soup.find('div', class_='entry-content')
        print(f"Content div found: {content_div is not None}")
        
        description = content_div.get_text().strip() if content_div else None
        
        if saint_name and description:
            description = description[:500] + "..." if len(description) > 500 else description
            return {
                'name': saint_name,
                'description': description,
                'source': 'Franciscan Media'
            }
        
        return None
        
    except Exception as e:
        print(f"Franciscan scraping error: {e}")
        return None
        
def scrape_catholic():
    """Scrape saint information from Catholic.org"""
    try:
        # Step 1: Get the Saint of the Day landing page
        landing_url = 'https://www.catholic.org/saints/sofd.php'
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(landing_url, headers=headers, timeout=5)
        
        print(f"Catholic.org landing page status: {response.status_code}")
        
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the link to today's actual saint page
        saint_link = soup.find('a', href=lambda href: href and 'saint.php?saint_id=' in href)
        
        print(f"Found saint link: {saint_link}")
        
        if not saint_link:
            return None
        
        # Get full URL for the saint page
        saint_url = saint_link.get('href')
        if not saint_url.startswith('http'):
            saint_url = f"https://www.catholic.org{saint_url}"
        
        print(f"Saint page URL: {saint_url}")
        
        #  Scrape actual saint page
        saint_response = requests.get(saint_url, headers=headers, timeout=5)
        
        if saint_response.status_code != 200:
            return None
        
        saint_soup = BeautifulSoup(saint_response.content, 'html.parser')
        
        # Find saint name and description on the individual page
        name_tag = saint_soup.find('h1')
        saint_name = name_tag.get_text().strip() if name_tag else None
        
        print(f"Saint name: {saint_name}")
        
        # Get the description/bio
        paragraphs = saint_soup.find_all('p')
        additional_info = None
        
        if paragraphs:
            # Filter out navigation/junk paragraphs
            filtered_paragraphs = []
            for p in paragraphs:
                text = p.get_text().strip()
                # Skip paragraphs with navigation keywords
                if any(word in text.lower() for word in ['subscribe', 'printable', 'shop', 'copyright', 'author and publisher']):
                    continue
                # Only include substantial paragraphs (more than 50 characters)
                if len(text) > 50:
                    filtered_paragraphs.append(text)
                # Stop after we have 4 good paragraphs
                if len(filtered_paragraphs) >= 4:
                    break
            
            if filtered_paragraphs:
                additional_info = ' '.join(filtered_paragraphs)
            
                # Truncate smartly at sentence boundary if too long
                max_length = 1500
                if len(additional_info) > max_length:
                    # Find the last period within the limit
                    truncated = additional_info[:max_length]
                    last_period = truncated.rfind('.')
                
                    if last_period > 0:
                        # Cut at the last complete sentence
                        additional_info = additional_info[:last_period + 1]
                    else:
                        # No period found, just cut and add ellipsis
                        additional_info = truncated + "..."
                
        if saint_name:
            return {
                'name': saint_name,
                'additional_info': additional_info,
                'source': 'Catholic.org'
            }
        
        return None
        
    except Exception as e:
        print(f"Catholic.org scraping error: {e}")
        return None

@bot.event
async def on_ready():
    """Called when bot successfully connects to Discord"""
    print(f'{bot.user} has connected to Discord!')

@bot.command(name='hello')
async def hello(ctx):
    """Simple test command"""
    await ctx.send('Howdy! I am your friendly Catholic Discord bot. Did you pray today?')

@bot.command(name='saint')
async def saint(ctx):
    """Gets today's Saint of the Day from multiple sources"""
    try:
        async with ctx.typing():
            franciscan_data = scrape_franciscan()
            catholic_data = scrape_catholic()

        if not franciscan_data and not catholic_data:
            await ctx.send('Could not retrieve Saint of the Day. Please try again later.')
            return
        
        message = "**Saint of the Day**\n\n"

        # If we have Franciscan data, use it as primary
        if franciscan_data:
            message += f"**{franciscan_data['name']}**\n"
            message += f"{franciscan_data['description']}\n\n"
            message += f"*Source: {franciscan_data['source']}*\n"
        
        # If we ONLY have Catholic data (no Franciscan), use it as primary
        elif catholic_data and not franciscan_data:
            message += f"**{catholic_data['name']}**\n"
            if catholic_data.get('additional_info'):
                message += f"{catholic_data['additional_info']}\n\n"
            message += f"*Source: {catholic_data['source']}*\n"
        
        # If we have BOTH sources and different saints
        if franciscan_data and catholic_data:
            if catholic_data['name'] != franciscan_data.get('name'):
                message += f"\n**Additional Saint Today:**\n"
                message += f"**{catholic_data['name']}**\n"
                if catholic_data.get('additional_info'):
                    message += f"{catholic_data['additional_info']}\n\n"
                message += f"*Source: {catholic_data['source']}*\n"
        
        await ctx.send(message)
    
    except Exception as e:
        await ctx.send("An error occurred while fetching saint information.")
        print(f"Saint command error: {e}")    
  
@bot.command(name='testfranciscan')
async def test_franciscan(ctx):
    """Test Franciscan scraper"""
    result = scrape_franciscan()
    await ctx.send(f"Franciscan result: {result}")

@bot.command(name='testcatholic')
async def test_catholic(ctx):
    """Test Catholic.org scraper"""
    result = scrape_catholic()
    await ctx.send(f"Catholic result: {result}")

# Run the bot
if __name__ == '__main__':
    bot.run(config.DISCORD_TOKEN)