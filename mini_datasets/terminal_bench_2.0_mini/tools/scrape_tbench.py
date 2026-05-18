#!/usr/bin/env python3
"""Scrape table data from tbench.ai leaderboard pages and export as CSV.

Usage:
    python scrape_tbench.py "https://www.tbench.ai/leaderboard/terminal-bench/2.0/terminus-2/2.0.0/gpt-5.3-codex%40openai"
    python scrape_tbench.py "https://www.tbench.ai/..." -o ./results
"""

import argparse
import csv
import os
import re
import sys
from html.parser import HTMLParser
from urllib.parse import unquote, urlparse


class TableExtractor(HTMLParser):
    """Extract all <table> elements and their content from HTML."""

    def __init__(self):
        super().__init__()
        self.tables = []
        self._current_table = None
        self._current_row = None
        self._current_cell = None
        self._depth = 0
        self._table_depth = -1
        self._in_cell = False

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            if self._table_depth < 0:
                self._current_table = []
                self._table_depth = self._depth
            self._depth += 1
        elif tag == 'tr':
            if self._table_depth >= 0:
                self._current_row = []
            self._depth += 1
        elif tag in ('td', 'th'):
            if self._table_depth >= 0:
                self._in_cell = True
                self._current_cell = []
            self._depth += 1
        else:
            self._depth += 1

    def handle_endtag(self, tag):
        self._depth -= 1
        if tag == 'table':
            if self._depth == self._table_depth:
                if self._current_table is not None:
                    self.tables.append(self._current_table)
                self._current_table = None
                self._table_depth = -1
        elif tag == 'tr':
            if self._table_depth >= 0 and self._current_row is not None:
                self._current_table.append(self._current_row)
                self._current_row = None
        elif tag in ('td', 'th'):
            if self._in_cell and self._current_cell is not None:
                text = ''.join(self._current_cell).strip()
                # Collapse whitespace
                text = re.sub(r'\s+', ' ', text)
                self._current_row.append(text)
                self._in_cell = False
                self._current_cell = None

    def handle_data(self, data):
        if self._in_cell and self._current_cell is not None:
            self._current_cell.append(data)


def extract_tables_from_html(html):
    """Parse HTML and return all tables as list of list of lists."""
    parser = TableExtractor()
    parser.feed(html)
    return parser.tables


def remove_separator_rows(tables):
    """Remove rows that are just visual separators (all cells match a dashes/equals pattern)."""
    cleaned = []
    for table in tables:
        clean_table = []
        for row in table:
            if row and all(re.match(r'^[\-\=\s\|]+$', cell) for cell in row):
                continue
            clean_table.append(row)
        if clean_table:
            cleaned.append(clean_table)
    return cleaned


def sanitize_filename(name):
    """Replace characters unsafe for filenames with '-'. Covers / \\ : * ? " < > |."""
    return re.sub(r'[\\/:*?"<>|]', '-', name)


def build_output_name(url):
    """Derive output filename from the last path segment of the URL, URL-decoded."""
    path = urlparse(url).path
    name = path.rstrip('/').rsplit('/', 1)[-1]
    name = unquote(name)
    name = sanitize_filename(name)
    if not name:
        name = "output"
    return f"{name}.csv"


def write_tables_to_csv(tables, output_dir, url):
    """Write extracted tables to CSV. If multiple tables, append suffixes to filenames."""
    if not tables:
        print("No tables found.", file=sys.stderr)
        return

    os.makedirs(output_dir, exist_ok=True)
    filename = build_output_name(url)
    base, ext = os.path.splitext(filename)

    for i, table in enumerate(tables):
        if len(tables) > 1:
            filepath = os.path.join(output_dir, f"{base}_{i}{ext}")
        else:
            filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(table)

        print(f"Saved {len(table)} rows ({len(table[0]) if table else 0} columns) -> {filepath}")


def main():
    parser = argparse.ArgumentParser(
        description="Scrape table data from a tbench.ai leaderboard URL and export to CSV."
    )
    parser.add_argument("url", help="URL of the leaderboard page to scrape")
    parser.add_argument(
        "-o", "--output-dir", default=".",
        help="Output directory path (default: current directory)"
    )
    args = parser.parse_args()

    # Use requests if available, otherwise try urllib
    try:
        import requests
        resp = requests.get(args.url, timeout=30, headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            )
        })
        resp.raise_for_status()
        html = resp.text
    except ImportError:
        import urllib.request
        req = urllib.request.Request(args.url, headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            )
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode('utf-8')

    tables = extract_tables_from_html(html)
    tables = remove_separator_rows(tables)
    write_tables_to_csv(tables, args.output_dir, args.url)


if __name__ == "__main__":
    main()