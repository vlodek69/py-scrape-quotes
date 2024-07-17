from dataclasses import dataclass

import csv
import requests
from bs4 import BeautifulSoup, Tag

BASE_URL = "https://quotes.toscrape.com/"


@dataclass
class Quote:
    text: str
    author: str
    tags: list[str]


def parse_single_quote(quote_soup: Tag) -> Quote:
    return Quote(
        text=quote_soup.select_one(".text").text,
        author=quote_soup.select_one(".author").text,
        tags=[tag.get_text() for tag in quote_soup.select(".tag")]
    )


def get_single_page_quotes(page_soup: BeautifulSoup) -> [Quote]:
    quotes = page_soup.select(".quote")

    return [parse_single_quote(quote) for quote in quotes]


def get_quotes() -> [Quote]:
    page = requests.get(BASE_URL).content
    first_page_soup = BeautifulSoup(page, 'html.parser')

    all_quotes = get_single_page_quotes(first_page_soup)

    next_page = first_page_soup.select_one(".next > a")

    while next_page:
        page = requests.get(BASE_URL + next_page.attrs["href"]).content
        page_soup = BeautifulSoup(page, 'html.parser')
        all_quotes.extend(get_single_page_quotes(page_soup))

        next_page = page_soup.select_one(".next > a")

    return all_quotes


def main(output_csv_path: str) -> None:
    with open(output_csv_path, 'w', newline='', encoding='utf-8') as quotes_file:
        quotes_writer = csv.writer(quotes_file)
        headers = ["text", "author", "tags"]
        quotes_writer.writerow(headers)

        for quote in get_quotes():
            quotes_writer.writerow([
                quote.text,
                quote.author,
                quote.tags
            ])


if __name__ == "__main__":
    main("quotes.csv")
