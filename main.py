"""Set user flairs."""

import re
import time
import configparser
import praw
import configuration

class Flairbot:
    """Main class"""

    def __init__(self):
        """Initial setup"""

        self.reddit = praw.Reddit(user_agent=configuration.user_agent,
                                  client_id=configuration.client_id,
                                  client_secret=configuration.client_secret,
                                  refresh_token=configuration.refresh_token)

        self.subreddit = self.reddit.subreddit(configuration.subreddit)

        while True:
            try:
                self.read_config()
            except BaseException as error:
                print("An exception was thrown!")
                print(str(error))
            time.sleep(5)

    def read_config(self):
        """Read config"""

        self.config = configparser.ConfigParser(allow_no_value=True)
        self.config.read_string(self.subreddit.wiki[configuration.remote_config_path].content_md)

        self.fetch_pms()

    def fetch_pms(self):
        """Get PMs for account"""

        valid = r"[A-Za-z0-9_-]+"

        for msg in self.reddit.inbox.unread():
            author = str(msg.author)
            valid_user = re.match(valid, author)
            if msg.subject == configuration.message_subject and valid_user:
                self.process_pm(msg.body, author, msg)

    def process_pm(self, msg, author, msgobj):
        """Process the PMs"""

        if self.check_flair_status("allow", msg):
            self.set_flair(author, msg, self.config.get("allow", msg), False)
        elif self.check_flair_status("ban", msg):
            self.set_flair(author, msg, self.config.get("ban", msg), True)

        msgobj.mark_read()

    def check_flair_status(self, section, key):
        """Check if the flair is allowed"""

        try:
            self.config.get(section, key)
            return True
        except configparser.NoOptionError:
            return False

    def set_flair(self, user, flair, text, ban):
        """Set the flairs"""

        for current_user_flair in self.subreddit.flair(redditor=user):
            current_user_flair_class = current_user_flair["flair_css_class"] or ""
            current_user_flair_text = current_user_flair["flair_text"] or ""

        if ban:
            self.subreddit.banned.add(user, ban_reason=configuration.ban_reason)
            self.reddit.redditor(user).message(configuration.ban_message_subject,
                                               configuration.ban_message_body)
            return
        else:
            for the_user in self.subreddit.banned(redditor=user):
                if the_user.note == configuration.ban_reason:
                    self.subreddit.banned.remove(user)

        if current_user_flair_class.find("text-") != 0:
            self.subreddit.flair.set(user, text, flair + "-img")
        elif current_user_flair_class.find("text-red") == 0:
            self.subreddit.flair.set(user, current_user_flair_text, "text-red-" + flair + "-img")
        elif current_user_flair_class.find("text-blue") == 0:
            self.subreddit.flair.set(user, current_user_flair_text, "text-blue-" + flair + "-img")
        elif current_user_flair_class.find("text-pink") == 0:
            self.subreddit.flair.set(user, current_user_flair_text, "text-pink-" + flair + "-img")
        elif current_user_flair_class.find("text-brown") == 0:
            self.reddit.redditor(user).message(configuration.shame_message_subject,
                                               configuration.shame_message_body)

if __name__ == '__main__':
    Flairbot()
