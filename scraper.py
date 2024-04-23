import json
import time
import argparse
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from webdriver_manager.chrome import ChromeDriverManager
import re
import random


# Define a function to separate caption from hashtags
def separate_caption_from_hashtags(text):
    # Define a regular expression pattern to match hashtags
    hashtag_pattern = r'#\w+'
    hashtags = re.findall(hashtag_pattern, text)
    caption = re.sub(hashtag_pattern, '', text)
    return caption, hashtags


# Create the parser
parser = argparse.ArgumentParser(description='Process some integers.')

# Add the arguments
parser.add_argument('FileName', metavar='filename', type=str, help='the name of the file to process')

# Parse the arguments
args = parser.parse_args()

# File path to the list of users we want to scrape
file_name = args.FileName
print(file_name)
parse = file_name
print('File Name:', file_name)

#Path to your excel sheets
users = pd.read_excel("/Users/justinsong/hyp/scraper/meta/" + file_name)

data = []
driver = webdriver.Firefox()

driver.get("https://www.instagram.com/")

# wait for the instagram page to load
time.sleep(7)

# Once loaded, look for username and password fields
username = driver.find_element(By.CSS_SELECTOR, "input[name='username']")
password = driver.find_element(By.CSS_SELECTOR, "input[name='password']")

# Clear fields incase there was an autosave option
username.clear()
password.clear()

# Dummy login 
username.send_keys("jsongscrp3")
password.send_keys("Asdgi3526!")
login = driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()



# A pop-up will show up asking to save your login, clikc not now 
time.sleep(7)
notnow = driver.find_element(By.XPATH, "//div[contains(text(), 'Not now')]").click()
# Turn on notif
time.sleep(5)
notnow2 = driver.find_element(By.XPATH, "//button[contains(text(), 'Not Now')]").click()
time.sleep(5)
brokenLinks = []

# Iterating through the list of users 
for index, user in users.iterrows():
    user_data = {
        "ig_username": [user["Link to IG"]],
        "name": [],
        "title": [],
        "bio": [],
        "linktree": [],
        "posts": {},
    }
    
    # Load the profile of a user
    driver.get(user_data["ig_username"][0])
    time.sleep(random.randint(5, 10))

    # Get the profile information of the user
    try:
        profileDescription = driver.find_element(By.XPATH, '//meta[@name="description"]').get_attribute('content')

        # profileDescription is a string in format Follwers, Following, Posts
        followers_pattern = r'([\d,]+)[KM]? Followers'
        following_pattern = r'([\d,]+) Following'
        posts_pattern = r'([\d,]+)[KM]? [Pp]osts'

        # Use re.search to find the matches in the text
        followers_match = re.search(followers_pattern, profileDescription)
        following_match = re.search(following_pattern, profileDescription)
        posts_match = re.search(posts_pattern, profileDescription)

        user_data["ig_username"].append(followers_match.group()) 
        user_data["ig_username"].append(following_match.group())
        user_data["ig_username"].append(posts_match.group())
        
        og_title = driver.find_element(By.XPATH, '//meta[@property="og:title"]').get_attribute('content')
        match = re.match(r"(.*) \(@(.*)\) • Instagram photos and videos", og_title)
        if match:
            display_name = match.group(1)

        # Add the extracted information to your user_data dictionary
        user_data["name"].append(display_name.split(" | ")[0])
        user_data["title"].append(display_name)
        
        
        bio_element = driver.find_element(By.XPATH, "/html/body/div[2]/div/div/div[2]/div/div/div[1]/div[1]/div[2]/div[2]/section/main/div/header/section/div[3]/h1")
        bio_text = bio_element.get_attribute('innerHTML')  # Extracts plain text content
        clean = re.compile('<.*?>')
        bio = re.sub(clean, '', bio_text)
        user_data["bio"].append(bio)
        
        
        #scroll
    except Exception as e:
        print("cannot find profile", user_data["ig_username"][0])
        brokenLinks.append(user_data["ig_username"][0])
        pass 
    
    try:
        linktree_element = driver.find_element(By.XPATH, "//span[contains(text(), 'linktr.ee')]")
        linktree_url = linktree_element.text
        user_data["linktree"].append(linktree_url)
    except Exception as e:
    # If the linktr.ee element is not found, append 'na' to the list
        user_data["linktree"].append('na')
        pass

    # Scroll through the profile of a user
    scrolldown = driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var scrolldown=document.body.scrollHeight;return scrolldown;")
    match=False
    posts = set()

    # Go through the posts of the user so we can scrape from them
    try:
        postContainer = driver.find_element(By.XPATH, "/html/body/div[2]/div/div/div[2]/div/div/div[1]/div[1]/div[2]/div[2]/section/main/div/div[3]")
        child_divs = postContainer.find_elements(By.TAG_NAME, "div")
        for x in child_divs:
            for c in x.find_elements(By.TAG_NAME, "div"):

                tag = c.find_elements(By.TAG_NAME, "a")
                if len(tag):
                    link = tag[0]
                    post = link.get_attribute('href')
                    if '/p/' in post:
                        posts.add(
                            post
                        )

        for post in posts:
            user_data["posts"][post] = []

        while(match==False):

            # Iterate through our posts to get relevant post information
            for post_link in posts:
                driver.get(post_link)
                time.sleep(3)
        
                # Try finding the description (contains likes and comments sometimes hidden)
                try:
                    if len(user_data["posts"][post_link]) == 4:
                        continue

                    description = driver.find_element(By.XPATH, '//meta[@name="description"]').get_attribute('content')
                    likes_pattern = r'([\d,]+) likes'
                    comments_pattern = r'([\d,]+) comments'

                    # Use re.search to find the matches in the text
                    likes_match = re.search(likes_pattern, description)
                    comments_match = re.search(comments_pattern, description)

                    if (likes_match == None or comments_match == None):
                        user_data["posts"][post_link].append(("likes: ", "likes are hidden"))
                        user_data["posts"][post_link].append(("comments: ", "comments are hidden"))
                    else:
                        user_data["posts"][post_link].append(("likes: ", likes_match.group()))
                        user_data["posts"][post_link].append(("comments: ", comments_match.group()))
                except Exception as e:
                    print("description hidden", post_link)
                    brokenLinks.append(post_link)
                    pass
                
               
                
                try:
                    span_elements = driver.find_elements(By.CSS_SELECTOR, "span.x1lliihq.x1plvlek.xryxfnj.x1n2onr6.x193iq5w.xeuugli.x1fj9vlw.x13faqbe.x1vvkbs.x1s928wv.xhkezso.x1gmr53x.x1cpjm7i.x1fgarty.x1943h6x.x1i0vuye.xvs91rp.xo1l8bm.x5n08af.x10wh9bi.x1wdrske.x8viiok.x18hxmgj")
                    comments = []
    
                    # Iterate over the list of elements and extract text from each one
                    for element in span_elements:
                        comments.append(element.text.strip())  # Use strip() to remove any leading/trailing whitespace
                    
                    user_data["posts"][post_link].append(("comment: ", comments))
                except Exception as e:
                    print(f"No comments")
                    pass
                

                #  # Try finding the caption (not all posts have captions)
                try:
                    caption = driver.find_element(By.XPATH, '//meta[@property="og:title"]').get_attribute('content')
                    print(caption)
                    first_colon_index = caption.find(':')
                    caption_element = caption[first_colon_index + 1:].strip(' "')
                    # Not all posts have captions
                    if caption_element == {}:
                        caption_element == ""
                    
                    caption, hashtags = separate_caption_from_hashtags(caption_element)
                    user_data["posts"][post_link].append(("caption: ", caption))
                    user_data["posts"][post_link].append(("hashtags: ", hashtags))
                except Exception as e:
                    print("caption hidden", post_link)
                    pass

                try:
                    date_tag = driver.find_element(By.CSS_SELECTOR, 'time._aaqe')
                    print(1)
                    date = date_tag.get_attribute('title')
                    print(2)
                    user_data["posts"][post_link].append(("date: ", date))
                except Exception as e:
                    print("Not able to get date")

            last_count = scrolldown
            time.sleep(3)
            scrolldown = driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var scrolldown=document.body.scrollHeight;return scrolldown;")
            time.sleep(3)

        
            if last_count==scrolldown:
                match=True
    

        print("+++++++able to append", user_data)
        data.append(user_data)

        #searchbox
        # print(posts)
        # print(len(posts))
    except Exception as e:
        print("no scrolling here ------- ", user_data)
        print(e)


file_path = "data_" + brand + ".json"

# Open the file in write mode and write the dictionary to it as JSON
with open(file_path, "w") as json_file:
    json.dump(data, json_file)
