from manga_ocr import MangaOcr


mocr = MangaOcr()
text = mocr("book_cover.webp")
print(text)

# search_query = " ".join(results)

# 3. Query Google Books to find the official title
# api_url = f"https://www.googleapis.com/books/v1/volumes?q={search_query}"
# response = requests.get(api_url).json()

# if "items" in response:
#     top_match = response["items"][0]["volumeInfo"]
#     print(f"Title: {top_match['title']}")
#     print(f"Author: {', '.join(top_match.get('authors', []))}")
