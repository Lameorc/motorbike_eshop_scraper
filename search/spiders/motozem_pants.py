import csv
from datetime import datetime

import lxml.html
import scrapy


class MotozemPantsSpider(scrapy.Spider):
    name = 'motozem_pants'
    # allowed_domains = ['www.motozem.cz']
    start_urls = ['https://www.motozem.cz/moto-kalhoty/?aParameter%5B152%5D=152']

    def __init__(self, *args, keywords=None, **kwargs) -> None:
        if keywords is None:
            self.keywords = [
                "chránič",
                "zip",
                "vložka",
                "membrán",
            ]


        self.csv_filename = f"all_results_{str(datetime.now())}.csv"
        self.csv_header =["page", "price", "interesting", *self.keywords]
        with open(self.csv_filename, "w") as f:
            csv_writer = csv.DictWriter(f, self.csv_header)
            csv_writer.writeheader()

    def parse(self, response):
        pants = response.css("a.product")
        for p in pants:
           # yield {"name": p.css("h2::text").get()}
           pants_link = p.attrib["href"]
           yield response.follow(pants_link, callback=self.pants_are_interesting)

        next_page = response.css("a.nextPage::attr(href)").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def pants_are_interesting(self, response):
        matched_keywords = {
            k: False for k in self.keywords
        }

        price = response.css(".total-price-vat::text").get()
        desc = " ".join(response.css("div.description").getall())

        desc_text = lxml.html.fromstring(desc).text_content()
        for k in matched_keywords:
            # if any keyword is in desc, mark it as matched
            if k in desc_text:
                matched_keywords[k] = True

        # this works fine
        params = response.css("div.parameters span.description::text").getall()
        for k, v in matched_keywords.items():
            # faster escape latch, don't check if we've already got it from desc
            if v:
                self.logger.debug(f"Ignoring {k} param check, already in desc")
                continue

            # if any keyword is in any of the params mark it as matched
            if any(k in p for p in params):
                matched_keywords[k] = True

        page = response.url
        result = {
            "page": page,
            "price": float("".join(d for d in price if d.isdigit() or d in [",", "."])),
            "interesting": all(matched_keywords.values()),
            **matched_keywords,
        }
        yield result
        with open(self.csv_filename, "a") as f:
            writer = csv.DictWriter(f, self.csv_header, quoting=csv.QUOTE_NONNUMERIC)
            writer.writerow(result)




