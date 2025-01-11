from scrapfly import ScrapeConfig, ScrapflyClient, ScrapeApiResponse
from typing import Dict
import asyncio
import json
import scrapfly

SCRAPFLY = ScrapflyClient(key="scp-live-531e8d4e1e5f454d876762fb4d715dfe")

# scrapfly config
BASE_CONFIG = {
    # bypass web scraping blocking
    "asp": True,
    # set the proxy location to France
    "country": "fr",
}


def parse_ad(result: ScrapeApiResponse):
    """parse ad data from nextjs cache"""
    next_data = result.selector.css("script[id='__NEXT_DATA__']::text").get()
    # extract ad data from the ad page
    ad_data = json.loads(next_data)["props"]["pageProps"]["ad"]
    return ad_data


async def scrape_ad(url: str, _retries: int = 0) -> Dict:
    """Scrape ad page."""
    print(f"Scraping ad {url}")
    ad_data = None  # Initialize ad_data to avoid UnboundLocalError
    try:
        result = await SCRAPFLY.async_scrape(ScrapeConfig(url, **BASE_CONFIG))
        ad_data = parse_ad(result)
    except scrapfly.errors.UpstreamHttpClientError as e:
        if e.http_status_code == 410:
            print(f"URL {url} is gone (410). Skipping.")
            return {}
        else:
            print(f"Error scraping {url}: {e}")
    except ModuleNotFoundError as e:
        print("You must install the parsel package to enable this feature.")
    except Exception as e:
        print(f"Retrying failed request for {url}: {e}")
        if _retries < 2:
            return await scrape_ad(url, _retries=_retries + 1)
    return ad_data if ad_data else {}

async def run():
    ad_data = []
    to_scrape = [
        scrape_ad(url)
        for url in [
            "https://www.leboncoin.fr/ad/ventes_immobilieres/2809308201",
            "https://www.leboncoin.fr/ad/ventes_immobilieres/2820947069",
            "https://www.leboncoin.fr/ad/ventes_immobilieres/2643327428"
        ]
    ]
    for response in asyncio.as_completed(to_scrape):
        ad_data.append(await response)

    # save to JSON file
    with open("ads.json", "w", encoding="utf-8") as file:
        json.dump(ad_data, file, indent=2, ensure_ascii=False)


asyncio.run(run())
