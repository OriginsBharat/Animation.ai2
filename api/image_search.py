import os
from serpapi import GoogleSearch
from dotenv import load_dotenv

def search_for_character_images(query: str) -> list[str]:
    """
    Searches for images of a character using the SerpApi service.

    Args:
        query: The character name or search term.

    Returns:
        A list of original image URLs from the search results.
        Returns an empty list if the API key is not found or an error occurs.
    """
    load_dotenv()
    api_key = os.getenv("SERPAPI_API_KEY")

    if not api_key:
        print("Error: SERPAPI_API_KEY not found in .env file.")
        return []

    params = {
        "q": query,
        "tbm": "isch",  # tbm=isch is for Google Image search
        "ijn": "0",     # Page number
        "api_key": api_key,
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()

        if "error" in results:
            print(f"SerpApi Error: {results['error']}")
            return []

        image_urls = [image.get("original") for image in results.get("images_results", []) if image.get("original")]
        return image_urls
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []

if __name__ == '__main__':
    # Example usage:
    # Make sure you have a .env file in the root directory with:
    # SERPAPI_API_KEY="your_actual_api_key"

    # To run this test, you would need to provide a real API key in a .env file.
    # Since I cannot do that, this is for demonstration purposes.
    print("Testing image search for 'Hollow Knight Hornet'")
    # In a real run, the following line would be executed.
    # image_list = search_for_character_images("Hollow Knight Hornet")
    # if image_list:
    #     print(f"Found {len(image_list)} images.")
    #     # Print the first 5 for brevity
    #     for i, url in enumerate(image_list[:5]):
    #         print(f"{i+1}. {url}")
    # else:
    #     print("No images found or an error occurred.")
    print("Example test finished. Note: No actual API call was made in this simulated test run.")
