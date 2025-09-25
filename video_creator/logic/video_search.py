from youtubesearchpython import VideosSearch

def search_for_videos(keywords: str, limit: int = 10) -> list:
    """
    Searches YouTube for videos based on keywords.

    Args:
        keywords: The search terms.
        limit: The maximum number of results to return.

    Returns:
        A list of dictionaries, where each dictionary contains
        information about a video (title, link, thumbnails).
    """
    try:
        videos_search = VideosSearch(keywords, limit=limit)
        results = videos_search.result()

        video_list = []
        if results and 'result' in results:
            for video in results['result']:
                video_list.append({
                    'title': video.get('title', 'No Title'),
                    'link': video.get('link', 'No Link'),
                    'thumbnails': video.get('thumbnails', [])
                })
        return video_list

    except Exception as e:
        print(f"An error occurred during video search: {e}")
        return []

if __name__ == '__main__':
    # Example usage for testing
    search_term = "cat videos"
    videos = search_for_videos(search_term, limit=5)

    if videos:
        print(f"Found {len(videos)} videos for '{search_term}':")
        for i, video_info in enumerate(videos, 1):
            print(f"{i}. Title: {video_info['title']}")
            print(f"   Link: {video_info['link']}")
            # To keep it simple, let's just print the URL of the first thumbnail
            if video_info['thumbnails']:
                print(f"   Thumbnail: {video_info['thumbnails'][0]['url']}")
            print("-" * 20)
    else:
        print(f"No videos found for '{search_term}'.")