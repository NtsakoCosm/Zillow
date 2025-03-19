import asyncio
import datetime
import html
import json
from threading import Lock
import re
from  patchright.async_api import async_playwright,Browser,Page
import random

PATTERNS = ["https://www.zillow.com/homedetails/","zillow.com/homedetails/"]
data = []
dataLock = Lock()
clicked_links = []

   
     
async def mouse(page,x,y,delay):
    await page.mouse.move(x,y)
    
    #await asyncio.sleep((delay/1500) )

async def click(page:Page,x,y,delay,scroll=False):
    await page.mouse.click(x,y)
    #await asyncio.sleep(delay/1000)

async def get_hovered_url(page:Page, x, y):


    """
    Get the URL of the closest <a> element at the given mouse coordinates
    if it matches the specified patterns.
    """
    await page.wait_for_timeout(1000)  # Wait for any hover effects to take place

    url = await page.evaluate("""
        ([x, y]) => {
            let elem = document.elementFromPoint(x, y);
            while (elem && elem.tagName !== 'A') {
                elem = elem.parentElement;  // Traverse up the DOM tree
            }
            return elem ? elem.href : null;  // Return the URL if an <a> element is found
        }
    """, [x, y])

    if url and any(url.startswith(pattern) for pattern in PATTERNS):
        return url
    return None

async def scrape(page:Page,x=0,y=0):
    details = {}
    def safe_extract(pattern, text, group=1, flags=0, cast_func=None):
        match = re.search(pattern, text, flags)
        if match:
            value = match.group(group).strip()
            if cast_func:
                try:
                    return cast_func(value)
                except Exception:
                    return value
            return value
        else:
            return "None Found"
    
    try:
        await page.wait_for_selector('.layout-static-column-container',
                                                               
                                    timeout=10000)
    except:
        pass
        
                                
    element = await page.query_selector('.layout-static-column-container')

    
    
    if element:
       
        
        text = await element.inner_text()
        # Patterns to extract each piece of information
        price_pattern   = r'\$\d{1,3}(?:,\d{3})*'
        address_pattern = r'\d+\s+.*,\s*[A-Za-z\s]+,\s*[A-Z]{2}\s*\d{5}'
        beds_pattern    = r'(\d+)\s*beds'
        baths_pattern   = r'(\d+)\s*baths'
        sqft_pattern    = r'(\d{1,3}(?:,\d{3})*)\s*sqft'
        acres_pattern   = r'(\d+(?:\.\d+)?)\s*acres'
        # Extract price with error handling
        price_match = re.search(price_pattern, text)
        price = price_match.group() if price_match else "None Found"

        # Extract address with error handling and clean it
        address_match = re.search(address_pattern, text)
        if address_match:
            address = address_match.group()
            address = re.sub(r'\s+', ' ', address).strip()  # Replace multiple spaces/newlines with a single space
            address = address.replace("\xa0", " ")           # Replace non-breaking spaces with a normal space
        else:
            address = "None Found"

        # Extract beds with error handling
        beds_match = re.search(beds_pattern, text, re.IGNORECASE)
        beds = int(beds_match.group(1)) if beds_match else "None Found"

        # Extract baths with error handling
        baths_match = re.search(baths_pattern, text, re.IGNORECASE)
        baths = int(baths_match.group(1)) if baths_match else "None Found"

        # Extract sqft with error handling
        sqft_match = re.search(sqft_pattern, text, re.IGNORECASE)
        if sqft_match:
            sqft = int(sqft_match.group(1).replace(',', ''))
        else:
            acres_match = re.search(acres_pattern, text, re.IGNORECASE)
            if acres_match:
                acres_value = float(acres_match.group(1))
                sqft = int(acres_value * 43560)  # Convert acres to square feet
            else:
                sqft = "None Found"
        #Additional Details:
        #Monthly payment breakdown
        details["monthly_payment"] = safe_extract(r'Estimated monthly payment\s*\$([\d,]+)', text)
        details["principal_interest"] = safe_extract(r'Principal & interest\s*\$([\d,]+)', text)
        details["mortgage_insurance"] = safe_extract(r'Mortgage insurance\s*\$([\d,]+)', text)
        details["property_taxes_payment"] = safe_extract(r'Property taxes\s*\$([\d,]+)', text)
        details["home_insurance"] = safe_extract(r'Home insurance\s*\$([\d,]+)', text)
        details["hoa_fees"] = safe_extract(r'HOA fees\s*([\w\/]+)', text)
        # Climate risks (Flood, Fire, Wind, Air, Heat)
        climate_risks = re.findall(r'(Flood Factor|Fire Factor|Wind Factor|Air Factor|Heat Factor)\s+(\w+)\s+(\d+\/10)', text)
        details["climate_risks"] = {}
        for risk in climate_risks:
            details["climate_risks"][risk[0]] = {"description": risk[1], "rating": risk[2]}
        #Information
        details["whats_special"] = safe_extract(r"What's special\s*(.*?)\s*\d+\s*day", text, flags=re.DOTALL)
        # This regex looks for text starting from "Facts & features" up to "Services availability"
        facts_features_match = re.search(r'Facts & features(.*?)Services availability', text, re.DOTALL | re.IGNORECASE)
        if facts_features_match:
            facts_features_text = facts_features_match.group(1).strip()
        else:
            facts_features_text = "None Found"

        # Step 2. Parse key–value pairs from the extracted block.
        # This approach looks for lines that contain a colon ":".
        features_dict = {}
        for line in facts_features_text.splitlines():
            line = line.strip()
            # Skip blank lines and lines without a colon
            if not line or ':' not in line:
                continue
            key, value = line.split(":", 1)
            features_dict[key.strip()] = value.strip()

        details["price"]=price
        details["rent_zestimate"] = safe_extract(r'Rent Zestimate®\s*\$([\d,]+)\/mo', text)
        details["features"] = features_dict
        details["address"]=address
        details["beds"]=beds
        details["baths"]=baths
        details["sqft"]=sqft
        details["url"] = page.url
        image_urls = await page.eval_on_selector_all(
        'div[data-testid="hollywood-gallery"] img',
        'elements => elements.map(e => e.src)'
        )
        details["image_urls"] = image_urls
        with dataLock:
            if details not in data:
                data.append(details)

        
        
        print(details)
        
        return details
        
       
        
    else: 
        return None
    
    
    
    #await asyncio.sleep(300)

async def emailPopUpHandler(page:Page):
     if await page.locator("#reg-login-email").is_visible():
                    await click(page=page,x=1200,y=400,delay=0)
                    await asyncio.sleep(0.5)
                    return True
     else:
          return False

async def clickListing(now,page:Page,x,y):
    await click(page,x=x,y=y,delay=0)
    email=await emailPopUpHandler(page=page)
    if email:
        await click(page,x=x,y=y,delay=0)
         
    s = await scrape(page=page,x=x,y=y)
    if s != None:
        
        await click(page,x=1250,y=250,delay=0)
        await asyncio.sleep(random.uniform(0, 1.5))
    print(datetime.datetime.now()- now)
    print(len(data))

async def zScraper(url,now,browser: Browser):
    
    page = await browser.new_page()
    await page.set_viewport_size({"width": 1280,"height": 720})
    page.set_default_timeout(31536000)
    await page.goto(url)
    
    
    for i in range(1,20):
        await click(page=page,x=1270,y=708,delay=0)
        await click(page=page,x=1270,y=708,delay=0)
        for j in range(1,11):
            await emailPopUpHandler(page=page) 
            await clickListing(now,page=page,x=730,y=240)
            await asyncio.sleep(random.uniform(0.5,1.5))
            #Attack
            if await page.locator(".fkecDT .ClRDZ").is_visible():
                await page.locator(".fkecDT .ClRDZ").click()
            await clickListing(now,page=page,x=1070,y=200)
            await asyncio.sleep(random.uniform(0.5,1.5))
            #Attack
            if await page.locator(".fkecDT .ClRDZ").is_visible():
                await page.locator(".fkecDT .ClRDZ").click()
            link =await get_hovered_url(page=page,x=700,y=580)
            if j > 1 or link:
                await clickListing(now,page=page,x=715,y=580)
                await asyncio.sleep(random.uniform(0.5,1.5))
                #Attack
                if await page.locator(".fkecDT .ClRDZ").is_visible():
                    await page.locator(".fkecDT .ClRDZ").click()
            await clickListing(now,page=page,x=1080,y=530)
            await asyncio.sleep(random.uniform(0.5,1.5))
            #Attack
            if await page.locator(".fkecDT .ClRDZ").is_visible():
                await page.locator(".fkecDT .ClRDZ").click()
            #Scroll
            for _ in range(15):
                await click(scroll=True,page=page,x=1270,y=708,delay=500)
                await asyncio.sleep(0.125)
                
        await page.locator('.eWgqmW+ .cYngKx .dmzPQJ').scroll_into_view_if_needed()
        await page.locator('.eWgqmW+ .cYngKx .dmzPQJ').click()
        await asyncio.sleep(2)
        await page.wait_for_load_state(timeout=100000)
             
                           

async def main():
    
    now = datetime.datetime.now()
    
    async with async_playwright() as p:
        browser =  await p.chromium.launch(
                              
            headless=False
           
        )
        
        
        
        
       
        urls = [ 
            
            ("https://www.zillow.com/ca/?searchQueryState=%7B%22isMapVisible%22%3Atrue%2C%22mapBounds%22%3A%7B%22north%22%3A42.009517%2C%22south%22%3A32.528832%2C%22east%22%3A-114.131253%2C%22west%22%3A-124.482045%7D%2C%22filterState%22%3A%7B%22sort%22%3A%7B%22value%22%3A%22globalrelevanceex%22%7D%7D%2C%22isListVisible%22%3Atrue%2C%22mapZoom%22%3A6%2C%22regionSelection%22%3A%5B%7B%22regionId%22%3A9%2C%22regionType%22%3A2%7D%5D%2C%22usersSearchTerm%22%3A%22California%22%2C%22schoolId%22%3Anull%7D",now,browser),
            
            
            ]
        
        tasks = [asyncio.create_task(zScraper(*arg)) for arg in urls]
        await asyncio.gather(*tasks)



if __name__ == "__main__":
    asyncio.run(main())
                        
