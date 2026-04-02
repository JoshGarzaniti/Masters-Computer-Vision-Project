# -*- coding: utf-8 -*-
"""
Masters Tournament Past Winners Scraper
"""

import asyncio
import pandas as pd
from playwright.async_api import async_playwright

BASE_URL = "https://www.masters.com/en_US/tournament/past_winners.html"

async def scrape_masters_players():
    all_rows = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) "
                "Gecko/20100101 Firefox/134.0"
            ),
            viewport={"width": 1280, "height": 800},
            locale="en-US"
        )
        page = await context.new_page()

        await page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_selector(".tournament-year-select", timeout=30000)
        await page.wait_for_timeout(2000)

        # Dismiss cookie banner — try multiple selectors
        try:
            for selector in [
                "button.close",
                ".close-btn",
                "button[aria-label='Close']",
                ".cookie-close",
                "[class*='cookie'] button",
                "[class*='consent'] button",
            ]:
                btn = await page.query_selector(selector)
                if btn and await btn.is_visible():
                    await btn.click()
                    await page.wait_for_timeout(500)
                    break
            else:
                await page.locator(".cookie-banner >> button").first.click()
                await page.wait_for_timeout(500)
        except:
            pass

        # Scrape 2025 separately since it's already loaded on page load
        print("  Scraping 2025 (default page load)...")
        await page.wait_for_selector(".winners-table tbody tr", timeout=10000)
        player_cells = await page.query_selector_all(
            ".winners-table tbody tr td:nth-child(2)"
        )
        for cell in player_cells:
            name = (await cell.inner_text()).strip()
            if name:
                all_rows.append({"Name": name, "Year": 2025})

        # Scrape 1995 — first year of era 2, loads automatically when tab is clicked
        print("  Scraping 1995 (first load of era tab)...")
        await page.click(".tournament-year-select")
        await page.wait_for_timeout(1000)
        await page.click(".yearNav > li:nth-child(2)", force=True)
        await page.wait_for_timeout(1000)
        await page.wait_for_selector(".winners-table tbody tr", timeout=10000)
        player_cells = await page.query_selector_all(
            ".winners-table tbody tr td:nth-child(2)"
        )
        for cell in player_cells:
            name = (await cell.inner_text()).strip()
            if name:
                all_rows.append({"Name": name, "Year": 1995})

        # Scrape 1965 — first year of era 3, loads automatically when tab is clicked
        print("  Scraping 1965 (first load of era tab)...")
        await page.click(".tournament-year-select")
        await page.wait_for_timeout(1000)
        await page.click(".yearNav > li:nth-child(3)", force=True)
        await page.wait_for_timeout(1000)
        await page.wait_for_selector(".winners-table tbody tr", timeout=10000)
        player_cells = await page.query_selector_all(
            ".winners-table tbody tr td:nth-child(2)"
        )
        for cell in player_cells:
            name = (await cell.inner_text()).strip()
            if name:
                all_rows.append({"Name": name, "Year": 1965})

        # Main era loop — each era explicitly clicks its own tab first
        eras = [
            (".yearNav > li:nth-child(1)", "2025-1996", True),  # skip 2025, already done
            (".yearNav > li:nth-child(2)", "1995-1966", True),  # skip 1995, already done
            (".yearNav > li:nth-child(3)", "1965-1934", True),  # skip 1965, already done
        ]

        for era_selector, era_label, skip_first in eras:

            # Open the dropdown
            await page.click(".tournament-year-select")
            await page.wait_for_timeout(1000)

            # Always click the era tab to make sure we're on the right one
            await page.click(era_selector, force=True)
            await page.wait_for_timeout(500)

            # Collect years from the visible year-list
            year_lis = await page.query_selector_all("div.nav.show .year-list li")
            years = []
            for li in year_lis:
                text = (await li.inner_text()).strip()
                if text.isdigit():
                    years.append(text)

            # Skip first year since it was already scraped above
            if skip_first:
                years = years[1:]

            print(f"Era {era_label}: scraping {len(years)} years: {years}")

            for year in years:
                print(f"  Scraping {year}...")

                # Re-open dropdown
                await page.click(".tournament-year-select")
                await page.wait_for_timeout(1000)

                # Re-click era tab while dropdown is open
                await page.click(era_selector, force=True)
                await page.wait_for_timeout(500)

                # Click the year
                year_lis_fresh = await page.query_selector_all("div.nav.show .year-list li")
                clicked = False
                for li in year_lis_fresh:
                    if (await li.inner_text()).strip() == year:
                        await li.click(force=True)
                        clicked = True
                        break

                if not clicked:
                    print(f"    Could not find {year}, skipping.")
                    continue

                await page.wait_for_selector(".winners-table tbody tr", timeout=10000)
                await page.wait_for_timeout(500)

                # Scrape player names
                player_cells = await page.query_selector_all(
                    ".winners-table tbody tr td:nth-child(2)"
                )
                for cell in player_cells:
                    name = (await cell.inner_text()).strip()
                    if name:
                        all_rows.append({"Name": name, "Year": int(year)})

        await browser.close()

    masters_players_df = pd.DataFrame(all_rows, columns=["Name", "Year"])
    masters_players_df = masters_players_df.drop_duplicates().reset_index(drop=True)

    print(f"\nScraped {len(masters_players_df)} player-year records.")
    print(masters_players_df.head(10))
    return masters_players_df


async def main():
    df = await scrape_masters_players()
    output_path = "C:\\Personal Projects\\masters_players.csv"
    df.to_csv(output_path, index=False)
    print(f"\nSaved to {output_path}")
    return df


if __name__ == "__main__":
    asyncio.run(main())






