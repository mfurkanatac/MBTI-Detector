import praw
import csv
import time
from prawcore.exceptions import RequestException, ServerError, ResponseException

# Custom retry decorator for handling rate limiting
def retry_if_rate_limited(function):
    def wrapper(*args, **kwargs):
        retries = 0
        max_retries = 50
        while retries < max_retries:
            try:
                return function(*args, **kwargs)
            except (RequestException, ServerError, ResponseException) as e:
                if hasattr(e, 'response') and e.response.status_code == 429:
                    print("Rate limited. Retrying after 5 seconds...")
                    time.sleep(5)
                    retries += 1
                else:
                    raise
        raise Exception("Too many retries. Aborting.")
    return wrapper

# Create a Reddit instance (fill it with your own project's credentials)
# https://towardsdatascience.com/how-to-use-the-reddit-api-in-python-5e05ddfd1e5c
# that website helped me a lot to set up my reddit instance

# to understand praw, make sure to check its documentation. For a junior, hardest thing is to check the documentation but believe me it solves many things.
reddit = praw.Reddit(
    client_id='',
    client_secret='',
    user_agent='',
    username=''
)

# Specify the subreddits (provide a list, not a string since it goes through a for loop even if you are doing one subreddit)
subreddit_names = ["infj", "enfp", "enfj", "isfj", "isfp", "istj", "istp", "estp", "estj", "esfp", "esfj"]

# Loop through each subreddit
for subreddit_name in subreddit_names:
    print(f"Collecting data from r/{subreddit_name}...")
    subreddit = reddit.subreddit(subreddit_name) # Create a subreddit instance

    # Open the CSV file to write the data (of course I could have collected data first and write it afterwards but i did not want to bother the ram too much and if there was a connection problem or electricity cut, I did not want to lose all the data i fetched)
    with open(f"{subreddit_name}.csv", mode="w", newline="", encoding="utf-8") as file:
        # Create a CSV writer
        writer = csv.writer(file)

        # Write the CSV header row
        # normally we do not need username and url columns however I did want to check it if the code works properly. Thats why they are here.
        writer.writerow(['username', 'flair', 'post-comment', 'score', 'url'])

        # Collect data from the subreddit
        limit = 7000000  # Number of posts to retrieve (I maxed this because more data means more accurate training. We are using deep learning after all which needs much more data than machine learning.)
        posts = subreddit.new(limit=limit) # Get the posts from the subreddit

        # Process and store the retrieved posts and comments
        for post in posts:
            # Extract relevant information from the post
            username = post.author.name if post.author else ''
            flair = post.author_flair_text if post.author_flair_text else ''
            post_comment = post.selftext if post.selftext else ''
            score = post.score
            url = post.url

            # Write the post data to the CSV file
            writer.writerow([username, flair, post_comment, score, url])

            # Fetch the comments for the post with retrying
            # https://www.geeksforgeeks.org/decorators-in-python/ to understand decorators, please read
            @retry_if_rate_limited 

            def get_comments(post):
                post.comments.replace_more(limit=None)
                return post.comments.list()

            try:
                comments = get_comments(post)
            except Exception as e:
                print("Error occurred while fetching comments:", e)
                continue

            # Extract comments from the post and write them to the CSV file
            for comment in comments:
                comment_username = comment.author.name if comment.author else ''
                comment_flair = comment.author_flair_text if comment.author_flair_text else ''
                comment_body = comment.body if comment.body else ''
                comment_score = comment.score 
                # notice that we are not saving the url for every comment. As I already stated, I just needed url to check if its going well. Not a crucial information.

                # Write the comment data to the CSV file
                writer.writerow([comment_username, comment_flair, comment_body, comment_score, ''])

    print(f"Data collection from r/{subreddit_name} and CSV writing complete.")

print("All data collection and CSV writing completed.")
