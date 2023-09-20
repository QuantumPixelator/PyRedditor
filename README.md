# PyRedditor 0.2
Download images from a subreddit. You can choose how many posts to scan, filter according to time, and how to sort.
##
## Important: 

**In order to use the script, you need to use your own credentials.** See this page for simple, quick instructions:

https://www.reddit.com/prefs/apps
##

Example:

    {"client_id": "YOUR_CLIENT_ID", "client_secret": "YOUR_CLIENT_SECRET", "password": "YOUR_ACCOUNT_PASSWORD", "username": "YOUR_ACCOUNT_USERNAME", "user_agent": "YOUR_USER_AGENT"}
    
Images will be downloaded into "images" folder, and then with the subreddit's name. The imges folder is inside the folder where the script is running.

#### Dependencies:
1. praw `pip install praw`
2. requests `pip install requests`


##### Original Code:

I don't know who wrote the original cli code, I found it on the Internet somewhere. It's the basis for the GUI version by me. Thanks to the original author(s).
