from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup


@dataclass
class Quote:
    text: str
    author: str
    tags: list[str]


def main(output_csv_path: str) -> None:
    pass


if __name__ == "__main__":
    main("quotes.csv")
