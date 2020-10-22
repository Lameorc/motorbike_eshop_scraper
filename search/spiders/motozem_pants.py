import json
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

        self.start_time = str(datetime.now())


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

        # TODO: this does not actually work, since it fails to get text from children
        #       probably need to use beautiful soup or something
        desc = " ".join(response.css("div.description").getall())

        desc_text = lxml.html.fromstring(desc).text_content()
        self.logger.debug("desc_text: %s", desc_text)
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
            "matched keywords": matched_keywords,
            "interesting": all(matched_keywords.values()),
        }
        yield result
        j = json.dumps(result, ensure_ascii=False, indent=2)
        with open(f"all_results_{self.start_time}.json", "a+") as f:
            f.write(j)

        if result["interesting"]:
            with open(f"interesting_results_{self.start_time}.json", "a+") as f:
                f.write(j)





