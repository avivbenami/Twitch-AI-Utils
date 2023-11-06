import json
from datetime import datetime, timezone
import hashlib
import re
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

class StreamManager:
    def __init__(self, config_file="config.json"):
        self.config = self.load_config(config_file)
        self.video_domains = self.config.get("video_domains", [])
        self.user_agent = self.config.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0")
        self.chrome_options = self.setup_chrome_options()

    def load_config(self, config_file):
        try:
            with open(config_file, "r") as file:
                return json.load(file)
        except FileNotFoundError:
            print("Config file not found.")
            raise

    def setup_chrome_options(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        chrome_options.add_argument(f"user-agent={self.user_agent}")
        return chrome_options

    def initialize_webdriver(self, url):
        try:
            driver = webdriver.Chrome(options=self.chrome_options)
            driver.get(url)
            return driver
        except Exception as e:
            print(f"Error initializing WebDriver: {e}")
            return None

    def fetch_stream_time(self, url):
        try:
            driver = self.initialize_webdriver(url)
            page_source = driver.page_source
            driver.close()
            
            soup = BeautifulSoup(page_source, 'html.parser')
            stream_time_data_str = soup.find(attrs={"data-requests": True})["data-requests"]
            stream_time_data_json = json.loads(stream_time_data_str)[0]
            stream_time_str = stream_time_data_json.get("started_at", "").split("+")[0].replace("T", " ")
            stream_time = datetime.strptime(stream_time_str, "%Y-%m-%d %H:%M:%S")
            
            return int(stream_time.replace(tzinfo=timezone.utc).timestamp()), stream_time_str
        except Exception as e:
            print(f"Error fetching stream time: {e}")
            return None, None

    def hash_sha1(self, text):
        return hashlib.sha1(text.encode('utf-8')).hexdigest()[:20]

    def get_m3u8(self, url, audio=False):
        try:
            chunk = "audio_only" if audio else "chunked"
            sid = url.split('/')[-1]
            name = url.split('/')[-3]
            timestamp = str(self.fetch_stream_time(url)[0])
            base_string = f"{name}_{sid}_{timestamp}"
            hashed = self.hash_sha1(base_string)
            final_string = f"{hashed}_{base_string}"
            for video_domain in self.video_domains:

                final_url = f"{video_domain}{final_string}/{chunk}/index-dvr.m3u8"
                print(f"Testing: {final_url}")
                response = requests.head(final_url, headers={'User-Agent': self.user_agent})
                if 'Content-Type' in response.headers and response.headers['Content-Type'] in ['application/x-mpegURL', 'binary/octet-stream']:
                    return final_url
            return None
        except Exception as e:
            print(f"Error fetching M3U8 URL: {e}")
            return None

    def get_stream_urls_and_data(self, name):
        try:
            stream_url = f"https://streamscharts.com/channels/{name}/streams"
            driver = self.initialize_webdriver(stream_url)

            page_source = driver.page_source
            driver.close()
            soup = BeautifulSoup(page_source, 'html.parser')
            stream_ids = re.findall(f'/{name}/streams/([\d]+)', page_source)
            title_elements = soup.find_all('span', attrs={"x-ref": "text"})
            titles = [title.decode_contents()[:100] for title in title_elements]
            durations_pre = [duration.get_text(strip=True) for duration in soup.find_all('div', class_='t_v')]
            durations = [duration for duration in durations_pre if 'h' in duration or 'm' in duration]
            start_times = [span.get_text(strip=True) for span in soup.find_all('span', class_='text-sm font-bold')]
            img_urls = []
            for img_tag in soup.find_all('img', {'width': '65', 'height': '36'}, class_='t_i'):
                img_url = img_tag.get('src') 
                img_urls.append(img_url) 
            data = zip(start_times, durations, titles)
            
            stream_dict = {}
            
            stream_num_index = 0
            for stream_data, img_url in zip(data, img_urls):
                stream_url = f"https://streamscharts.com/channels/{name}/streams/{stream_ids[stream_num_index]}"
                stream_data_dict = {
                    "Start_time": stream_data[0],
                    "Duration": stream_data[1],
                    "Title": stream_data[2],
                    "Img_URL": img_url
                }
                stream_dict[stream_url] = stream_data_dict
                stream_num_index += 1
            
            return stream_dict
        except Exception as e:
            print(f"Error fetching stream URLs: {e}")
            return None
