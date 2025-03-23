import pandas as pd
import re
import json
import time
import random
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException



# How to use:

# 1. Import the modules
# 2. Call extract_comments() with:
#    - video_url: YouTube URL (regular or Shorts)
#    - max_comments: Number of comments to extract (default 100)
#    - max_scrolls: Number of scroll attempts (default 10)






# Author: Shivansh Pratap Singh (CSE)
# GitHub: https://github.com/ShiiiivanshSingh
# LinkedIn: https://www.linkedin.com/in/shivansh-pratap-singh-23b3b92b1
# Twitter: https://x.com/de_mirage_fan



















def setup_driver():
    options = Options()
    
    # u can uncomment this line to run without opening a browser window
    # options.add_argument("--headless=new")
   



 options.add_argument("--window-size=1920,1080")
    
    # these settings help avoid detection as a bot as youtube is good at detecting bots 
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0"
    ]
    options.add_argument(f"--user-agent={random.choice(user_agents)}")
    # mimics a real user sneaky beaky
    try:
        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    except Exception as e:
        print(f"Error setting up WebDriver: {e}")
        print("Make sure you have Chrome and ChromeDriver installed.")
        return None

def extract_video_id(url):
    # Get video ID 
    patterns = [
        r'(?:v=|\/videos\/|embed\/|youtu.be\/|\/v\/|\/e\/|watch\?v%3D|&v=)([^#\&\?\n]+)',
        r'\/shorts\/([^#\&\?\n\/]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def extract_comments(video_url, max_comments=100, max_scrolls=10):
  
    is_shorts = '/shorts/' in video_url.lower()
    video_id = extract_video_id(video_url)
    if not video_id:
        print("Error: Could not extract video ID from the URL")
        return []
    
    # Convert to standard watch URL for simplicity
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    print(f"Starting browser to extract comments from: {url}")
    print(f"Original URL type: {'YouTube Shorts' if is_shorts else 'Regular YouTube video'}")
    
    driver = setup_driver()
    
    if not driver:
        print("Could not initialize WebDriver.")
        return []
    
    comments = []
    
    try:
       
        driver.get(url)
        print("Waiting for page to load...")
        time.sleep(random.uniform(3, 5))
        try:
            accept_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Accept') or contains(text(), 'Accept') or contains(text(), 'agree')]"))
            )
            accept_button.click()
            print("Accepted cookies")
            time.sleep(1) #cookieee
        except TimeoutException:
            print("No cookie consent dialog found or timed out")
        
        # Scroll down
        print("Scrolling to load comments section...")
        driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(2)
        driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(2)
        
        
        if is_shorts:
            try:
                print("Looking for comments button on Shorts video...")
                selectors = [
                    "ytd-engagement-panel-section-list-renderer[target-id='engagement-panel-comments-section']",
                    "ytd-button-renderer:has(yt-formatted-string:contains('Comments'))",
                    "[aria-label='Comments']",
                    "button[aria-label*='comment']"
                ]
                
                for selector in selectors:
                    try:
                        comment_buttons = WebDriverWait(driver, 5).until(
                            EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                        )
                        if comment_buttons:
                            print(f"Found comments button using selector: {selector}")
                            for button in comment_buttons:
                                if button.is_displayed():
                                    print("Clicking on comments button...")
                                    button.click()
                                    time.sleep(2)
                                    break
                            break
                    except:
                        continue
            except Exception as e:
                print(f"Error finding comments button: {e}")
        
        # Wait for comments to appear on the page
        try:
            print("Waiting for comments to load...")
            comment_selectors = [
                "ytd-comment-thread-renderer",
                "ytd-comment-renderer",
                ".comment-renderer"
            ]
            
            found_comments = False
            for selector in comment_selectors:
                try:
                    WebDriverWait(driver, 8).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    print(f"Comments section found using selector: {selector}")
                    found_comments = True
                    break
                except:
                    continue
            
            if not found_comments:
                raise TimeoutException("No comment elements found with any selector")
                
        except TimeoutException:
            print("Timed out waiting for comments to load")
            
            # Take a screenshot for debugging if comments aren't found
            try:
                driver.save_screenshot("youtube_debug.png")
                print("Saved debug screenshot to youtube_debug.png")
            except:
                pass
                
            driver.quit()
            return []
        
        # Scroll down multiple times to load more comments
        print(f"Loading more comments (up to {max_scrolls} scrolls)...")
        previous_comments_count = 0
        
        for i in range(max_scrolls):
            # Try to find comments with different selectors
            comment_elements = []
            for selector in comment_selectors:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    comment_elements = elements
                    break
            
            current_count = len(comment_elements)
            
            # Stop scrolling if we have enough comments or no new ones are loading
            if current_count >= max_comments or (i > 2 and current_count == previous_comments_count):
                break
                
            print(f"Scroll {i+1}/{max_scrolls}: Found {current_count} comments so far")
            previous_comments_count = current_count
            
            # Scroll to the bottom to load more comments
            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(random.uniform(1.5, 3))
        
        # Extract the text from each comment
        print("Extracting comment text...")
        content_selectors = [
            "ytd-comment-thread-renderer #content-text", 
            "ytd-comment-renderer #content-text",
            ".comment-renderer-text-content",
            "[id^='comment-content']"
        ]
        
        extracted_comments = False
        for selector in content_selectors:
            comment_elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if comment_elements:
                for element in comment_elements:
                    comment_text = element.text.strip()
                    if comment_text:
                        comments.append(comment_text)
                
                    # Stop if we reach the requested number of comments
                    if len(comments) >= max_comments:
                        print(f"Reached maximum comment count ({max_comments})")
                        break
                
                extracted_comments = True
                break
        
        if not extracted_comments:
            print("Could not extract comments using any of the known selectors")
        else:
            print(f"Successfully extracted {len(comments)} comments")
        
    except Exception as e:
        print(f"Error during extraction: {e}")
    finally:
        print("Closing browser...")
        driver.quit()
    
    return comments

def save_comments_to_csv(comments, filename):
    # Save the comments to a CSV file
    if not comments:
        return False
        
    try:
        df = pd.DataFrame(comments, columns=['Comment'])
        df.to_csv(filename, index=False, encoding='utf-8-sig')  # utf-8-sig helps with Excel compatibility
        return True
    except Exception as e:
        print(f"Error saving CSV: {e}")
        return False

if __name__ == "__main__":
    print("\nYouTube Comment Scraper (Selenium Version)")
    print("------------------------------------------")
    print("Note: This script requires Chrome to be installed.")
    print("This version will open a browser window to scrape comments.")
    print("Supports both regular YouTube videos and YouTube Shorts URLs.")
    
    video_url = input("\nEnter the YouTube video URL: ")
    
    max_comments_input = input("Enter maximum number of comments to extract (default is 100): ")
    max_comments = 100
    if max_comments_input.strip() and max_comments_input.isdigit():
        max_comments = int(max_comments_input)
    
    max_scrolls_input = input("Enter maximum number of scrolls (default is 10): ")
    max_scrolls = 10
    if max_scrolls_input.strip() and max_scrolls_input.isdigit():
        max_scrolls = int(max_scrolls_input)
    
    print("\nStarting comment extraction...")
    print("A Chrome browser window will open - please don't close it.")
    print("The process may take a minute or two.")
    
    comments = extract_comments(video_url, max_comments, max_scrolls)
    
    if comments:
        output_file = f'youtube_comments_{int(time.time())}.csv'
        if save_comments_to_csv(comments, output_file):
            print(f"\nSuccess! Extracted {len(comments)} comments and saved to '{output_file}'")
        else:
            print("\nExtracted comments but failed to save to CSV file.")
    else:
        print("\nNo comments were extracted. Possible reasons:")
        print("1. The video might have comments disabled")
        print("2. The browser couldn't load the comments section")
        print("3. There might be an issue with your Chrome or ChromeDriver setup") 