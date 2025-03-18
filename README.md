# Zillow Listings Scraper

This project is an asynchronous web scraper built in Python that automates interactions with Zillow listings. It simulates real user behavior by moving the mouse, clicking, and typing, then extracts detailed property information such as price, address, beds, baths, square footage, and more.

---

## Features

- **Asynchronous Operations**: Uses Python's `asyncio` for concurrent execution.
- **Browser Automation**: Leverages Playwright (via `patchright.async_api`) to control a Chromium browser.
- **User Interaction Simulation**: Mimics mouse movements, clicks, and keyboard inputs.
- **Data Extraction**: Scrapes property details including pricing, address, features, monthly payment estimates, and climate risk factors.
- **Dynamic Navigation**: Iterates through multiple Zillow pages and handles pop-up dialogs.

---

## Requirements

- **Python**: Version 3.7 or higher
- **Dependencies**:
  - [Playwright](https://playwright.dev/python/)
  - [patchright](https://pypi.org/project/patchright/) (an asynchronous wrapper for Playwright)
  
---

## Installation

1. **Clone the repository** or copy the code to your local machine.
    https://github.com/NtsakoCosm/zillow.git
2. **Install required packages**:
   ```bash
   
   pip install requirements.txt

## Issues:

1. I had alot of problems dealing with selectors on this site, so i use regrex heavily , that could cause alot of problems but currently the scraper looks stable.

2. I am still looking to optimize this script as it is very slow compared to my other scrapers