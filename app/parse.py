import logging
import sys
from dataclasses import dataclass

import csv

import requests
from bs4 import BeautifulSoup, Tag


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

BASE_URL = "https://quotes.toscrape.com/"


@dataclass
class Quote:
    text: str
    author: str
    tags: list[str]


@dataclass
class Author:
    name: str
    born: str
    description: str


def parse_single_quote(quote_soup: Tag) -> Quote:
    return Quote(
        text=quote_soup.select_one(".text").text,
        author=quote_soup.select_one(".author").text,
        tags=[tag.get_text() for tag in quote_soup.select(".tag")],
    )


def prettify_description(text: str) -> str:
    """Mainly to remove unexpected whitespace characters"""
    return " ".join(text.split()).replace("''", '"')


def parse_single_author(author_href: str) -> Author:
    page = requests.get(BASE_URL + author_href).content
    author_page_soup = BeautifulSoup(page, "html.parser")

    author = Author(
        name=author_page_soup.select_one(".author-title").text,
        born=author_page_soup.select_one(".author-born-date").text
        + " "
        + author_page_soup.select_one(".author-born-location").text,
        description=prettify_description(
            author_page_soup.select_one(".author-description").text
        ),
    )

    logging.info(f"Adding author: {author}")

    return author


def get_single_page_quotes(page_soup: BeautifulSoup) -> [Quote]:
    quotes = page_soup.select(".quote")

    return [parse_single_quote(quote) for quote in quotes]


def get_single_page_authors(
    page_soup: BeautifulSoup, cached_author_hrefs: [str] = None
) -> [Author]:
    authors_soup = page_soup.select("a[href^='/author/']")
    authors = []

    for author in authors_soup:
        author_href = author.get("href")
        if author_href not in cached_author_hrefs:
            authors.append(parse_single_author(author_href))
            cached_author_hrefs.append(author_href)
        else:
            logging.info(
                f'Author already added ({author_href.split("/")[-1]})'
            )

    return authors


def get_authors_and_quotes() -> ([Author], [Quote]):
    """Authors and quotes scraping done in a single cycle for minimizing the
    number of requests"""
    page = requests.get(BASE_URL).content
    first_page_soup = BeautifulSoup(page, "html.parser")

    cached_author_hrefs = []
    all_authors = get_single_page_authors(first_page_soup, cached_author_hrefs)

    all_quotes = get_single_page_quotes(first_page_soup)

    next_page = first_page_soup.select_one(".next > a")

    while next_page:
        logging.info(
            f'Starting scraping page #{next_page.get("href").split("/")[2]}'
        )

        page = requests.get(BASE_URL + next_page.get("href")).content
        page_soup = BeautifulSoup(page, "html.parser")

        all_authors.extend(
            get_single_page_authors(page_soup, cached_author_hrefs)
        )
        all_quotes.extend(get_single_page_quotes(page_soup))

        next_page = page_soup.select_one(".next > a")

    return all_authors, all_quotes


def main(output_csv_path: str) -> None:
    authors, quotes = get_authors_and_quotes()
    with open(
        output_csv_path, "w", newline="", encoding="utf-8"
    ) as quotes_file, open(
        f"authors_of_{output_csv_path}", "w", newline="", encoding="utf-8"
    ) as authors_file:
        quotes_writer = csv.writer(quotes_file)
        quotes_headers = ["text", "author", "tags"]
        quotes_writer.writerow(quotes_headers)
        for quote in quotes:
            quotes_writer.writerow([quote.text, quote.author, quote.tags])

        authors_writer = csv.writer(authors_file)
        authors_headers = ["name", "born", "description"]
        authors_writer.writerow(authors_headers)
        for author in authors:
            authors_writer.writerow(
                [author.name, author.born, author.description]
            )


if __name__ == "__main__":
    main("quotes.csv")
