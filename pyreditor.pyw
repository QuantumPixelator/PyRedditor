import tkinter as tk
import customtkinter as ctk  # Import customtkinter
import praw
import json
import requests
import re
import os
import threading

class RedditMediaDownloader(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("PyRedditor")
        self.geometry("400x650")
        self.configure(bg="#2E2E2E")

        header_font = ("Arial", 12, "underline")
        label_font = ("Arial", 10)

        def create_label(text, font=None, fg="#FFFFFF"):
            return tk.Label(self, text=text, font=font, fg=fg, bg="#2E2E2E")

        self.cred_path = "credentials.json"
        if os.path.exists(self.cred_path):
            with open(self.cred_path) as f:
                cred = json.load(f)
        else:
            cred = {}

        create_label("Reddit Credentials", font=header_font).pack(pady=5)

        # Adjusted to use customTkinter widgets
        create_label("Client ID:", font=label_font).pack()
        self.client_id_entry = ctk.CTkEntry(self)
        self.client_id_entry.insert(0, cred.get('client_id', ''))
        self.client_id_entry.pack(pady=2)

        create_label("Client Secret:", font=label_font).pack()
        self.client_secret_entry = ctk.CTkEntry(self, show="*")
        self.client_secret_entry.insert(0, cred.get('client_secret', ''))
        self.client_secret_entry.pack(pady=2)

        create_label("Password:", font=label_font).pack()
        self.password_entry = ctk.CTkEntry(self, show="*")
        self.password_entry.insert(0, cred.get('password', ''))
        self.password_entry.pack(pady=2)

        create_label("Username:", font=label_font).pack()
        self.username_entry = ctk.CTkEntry(self)
        self.username_entry.insert(0, cred.get('username', ''))
        self.username_entry.pack(pady=2)

        create_label("User Agent:", font=label_font).pack()
        self.user_agent_entry = ctk.CTkEntry(self)
        self.user_agent_entry.insert(0, cred.get('user_agent', ''))
        self.user_agent_entry.pack(pady=2)

        create_label("Subreddit:", font=label_font).pack(pady=5)
        self.subreddit_entry = ctk.CTkEntry(self)
        self.subreddit_entry.pack(pady=2)

        create_label("Limit:", font=label_font).pack()
        self.limit_entry = ctk.CTkEntry(self)
        self.limit_entry.pack(pady=2)
        
        create_label("Sort by:", font=label_font).pack()
        self.sort_var = tk.StringVar(self)
        self.sort_var.set("top")
        self.sort_menu = tk.OptionMenu(self, self.sort_var, "top", "new", "hot", "rising")
        self.sort_menu.pack(pady=2)

        create_label("Time Filter:", font=label_font).pack()
        self.when_var = tk.StringVar(self)
        self.when_var.set("all")
        self.when_menu = tk.OptionMenu(self, self.when_var, "all", "year", "month", "week", "day", "hour")
        self.when_menu.pack(pady=2)

        self.downloaded_label = create_label("Files downloaded: 0", font=label_font)
        self.downloaded_label.pack(pady=5)


        # Adjusted buttons to use customTkinter rounded buttons
        self.start_button = ctk.CTkButton(self, text="Start Download", command=self.start_download_thread)
        self.start_button.pack(pady=5)

        self.stop_button = ctk.CTkButton(self, text="Stop Download", command=self.stop_download, state=tk.DISABLED)
        self.stop_button.pack(pady=5)

        self.download_thread = None
        self.stop_download_flag = False

    def start_download_thread(self):
        self.download_thread = threading.Thread(target=self.start_download)
        self.download_thread.start()
        self.stop_button.configure(state=tk.NORMAL)
        self.downloaded_label.configure(fg="yellow")

    def stop_download(self):
        self.stop_download_flag = True

    def start_download(self):
        cred = {
            "client_id": self.client_id_entry.get(),
            "client_secret": self.client_secret_entry.get(),
            "password": self.password_entry.get(),
            "username": self.username_entry.get(),
            "user_agent": self.user_agent_entry.get()
        }
        subreddit = self.subreddit_entry.get()
        sort = self.sort_var.get()
        limit = int(self.limit_entry.get())
        when = self.when_var.get()

        with open(self.cred_path, 'w') as f:
            json.dump(cred, f)

        reddit = praw.Reddit(**cred)

        self.download_images(reddit, subreddit, sort=sort, limit=limit, when=when)

    def download_images(self, reddit, sub, sort='top', limit=300, when='all'):
        downloaded_count = 0
        path = os.path.join("images", sub)
        if not os.path.exists(path):
            os.makedirs(path)

        subreddit = reddit.subreddit(sub)
        
        # Check if the sorting method is 'top' or 'controversial' before using the 'when' parameter
        if sort in ['top', 'controversial']:
            gen = getattr(subreddit, sort)(time_filter=when, limit=limit)
        else:
            gen = getattr(subreddit, sort)(limit=limit)
        url_pattern = re.compile(r'https://(external-)?preview\.redd\.it/(?P<name>.+\.(?:jpg|png))')
        for i in gen:
            if self.stop_download_flag:
                break
            if not i.is_self:
                att = dir(i)
                if 'is_gallery' in att and i.gallery_data:
                    image_ids = [x['media_id'] for x in i.gallery_data['items']]
                    for x in image_ids:
                        images = i.media_metadata[x]['p']
                        if images:
                            url = max(images, key=lambda y: y['y'])['u']
                            img = requests.get(url).content
                            match = url_pattern.search(url)
                            if match:
                                name = match.group('name')
                                with open(os.path.join(path, name), 'wb') as f:
                                    f.write(img)
                                downloaded_count += 1
                elif 'preview' in att and i.preview['images']:
                    url = i.preview['images'][0]['source']['url']
                    img = requests.get(url).content
                    match = url_pattern.search(url)
                    if match:
                        name = match.group('name')
                        with open(os.path.join(path, name), 'wb') as f:
                            f.write(img)
                        downloaded_count += 1

            self.downloaded_label.configure(text=f"Files downloaded: {downloaded_count}")

        self.stop_download_flag = False
        self.downloaded_label.configure(fg="#FFFFFF")
        self.stop_button.configure(state=tk.DISABLED)
        
app = RedditMediaDownloader()
app.mainloop()
