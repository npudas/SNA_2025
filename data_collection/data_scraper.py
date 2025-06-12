import os
import datetime
import time
import urllib.request
from playwright.sync_api import sync_playwright
import json
from lxml import html
import re
from tqdm import tqdm

def collect_x_data(x_url, output_dir, time_stamp): #TODO: Add timeout error handling
    _xhr_calls = []

    def intercept_response(response):
        if response.request.resource_type == "xhr":
            _xhr_calls.append(response)
        return response
    
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()
        
        page.on("response", intercept_response)
        page.goto(x_url)
        page.wait_for_selector("[data-testid='tweet']")

        tweet_calls = [f for f in _xhr_calls if "tweet" in f.url]
        for xhr in tweet_calls:
            try:
                data = xhr.json()
                file_name = os.path.join(output_dir, f"x_data_{time_stamp}.json")
                with open(file_name, 'w') as file:
                    json.dump(data, file, indent=4)
                #print(f"Collected X data: {file_name}")
                break
            except Exception as e:
                print(f"Error collecting X data: {e}")


def collect_youtube_data(youtube_url, output_dir, time_stamp): #TODO: Add timeout error handling
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()

        page.goto(youtube_url, wait_until="networkidle")
        #page.wait_for_selector('h1.title')  # Wait for the title to load

        page_content = page.content()

        try:
            raw_html_data = page_content
        except Exception as e:
            print(f"Error collecting raw HTML data: {e}")
            raw_html_data = "NA"

        # Regular expressions to extract data
        comments_pattern = r'aria-label="Kommentit (\d+)"'
        likes_pattern = r'"likeCount":"(\d+)"'
        views_pattern = r'"viewCount":"(\d+)"'

        # Extract data using regex
        comments_match = re.search(comments_pattern, raw_html_data)
        likes_match = re.search(likes_pattern, raw_html_data)
        views_match = re.search(views_pattern, raw_html_data)

        # Parse the matched data
        comments = int(comments_match.group(1)) if comments_match else None
        likes = int(likes_match.group(1)) if likes_match else None
        views = int(views_match.group(1)) if views_match else None

        # Create a dictionary to store the results
        extracted_data = {
            "timestamp": time_stamp,
            "comments": comments,
            "likes": likes,
            "views": views
        }

        # Save the results as a JSON file
        try:
            file_name = os.path.join(output_dir, f"youtube_extracted_data_{time_stamp}.json")
            with open(file_name, 'w', encoding='utf-8') as file:
                json.dump(extracted_data, file, indent=4, ensure_ascii=False)
            #print(f"Extracted youtube data saved to: {file_name}")
        except Exception as e:
            print(f"Error saving extracted data: {e}")

def collect_facebook_data(facebook_url, output_dir, time_stamp): #TODO: Add timeout error handling
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()

        page.goto(facebook_url, wait_until="networkidle")
        page_content = page.content()

        try:
            raw_html_data = page_content
        except Exception as e:
            print(f"Error collecting raw HTML data: {e}")
            raw_html_data = "NA"

        # Regular expressions to extract data
        comments_pattern = r'"comments\":{\"total_count\":(\d+)'
        shares_pattern = r'"share_count\":{\"count\":(\d+),\"'
        reactions_pattern = r'"reaction_count\":{\"count\":(\d+)}'
        video_views_pattern = r'"video_post_view_count\":(\d+)'

        # Extract data using regex
        comments_match = re.search(comments_pattern, raw_html_data)
        shares_match = re.search(shares_pattern, raw_html_data)
        reactions_match = re.search(reactions_pattern, raw_html_data)
        video_views_match = re.search(video_views_pattern, raw_html_data)

        # Parse the matched data
        comments = int(comments_match.group(1).replace(',', '')) if comments_match else None
        shares = int(shares_match.group(1).replace(',', '')) if shares_match else None
        reactions = int(reactions_match.group(1).replace(',', '')) if reactions_match else None
        video_views = int(video_views_match.group(1).replace(',', '')) if video_views_match else None

        # Create a dictionary to store the results
        extracted_data = {
            "timestamp": time_stamp,
            "comments": comments,
            "shares": shares,
            "reactions": reactions,
            "video_views": video_views
        }

        # Save the results as a JSON file
        try:
            file_name = os.path.join(output_dir, f"facebook_extracted_data_{time_stamp}.json")
            with open(file_name, 'w', encoding='utf-8') as file:
                json.dump(extracted_data, file, indent=4, ensure_ascii=False)
            #print(f"Extracted facebook data saved to: {file_name}")
        except Exception as e:
            print(f"Error saving extracted data: {e}")
        
def __main__():
    print("Starting data collection...")

    # Load URLs from config.json
    config_file = "config.json"
    try:
        with open(config_file, 'r', encoding='utf-8') as file:
            config = json.load(file)
            x_url = config.get("x_url", "")
            youtube_url = config.get("youtube_url", "")
            facebook_url = config.get("facebook_url", "")
    except Exception as e:
        print(f"Error reading config file: {e}")
        return

    interval = 3600  # 1 hour in seconds
    collect_time = 3 * 24 * 60 * 60  # 3 days in seconds
    samples = collect_time // interval
    collected_samples = 0

    output_dir = f"{os.getcwd()}/data_collection_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}/"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Initialize the progress bar
    with tqdm(total=samples, desc="Data Collection Progress", unit="sample") as pbar:
        while collected_samples < samples:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            collect_x_data(x_url, output_dir, timestamp)
            collect_youtube_data(youtube_url, output_dir, timestamp)
            collect_facebook_data(facebook_url, output_dir, timestamp)
            time.sleep(interval)
            collected_samples += 1
            pbar.update(1)  # Update the progress bar

    print("Data collection completed.")

if __name__ == "__main__":
    __main__()