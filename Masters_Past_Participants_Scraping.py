# -*- coding: utf-8 -*-
"""
Masters Tournament Past Winners Scraper
"""

import asyncio
import pandas as pd
from playwright.async_api import async_playwright

BASE_URL = "https://www.masters.com/en_US/tournament/past_winners.html"

async def scrape_table(page):
    """Scrape all columns from the winners table on the current page."""
    rows = []
    trs = await page.query_selector_all(".winners-table tbody tr")
    for tr in trs:
        tds = await tr.query_selector_all("td")
        if len(tds) < 2:
            continue
        pos         = (await tds[0].inner_text()).strip()
        name        = (await tds[1].inner_text()).strip()
        r1          = (await tds[2].inner_text()).strip() if len(tds) > 2 else ""
        r2          = (await tds[3].inner_text()).strip() if len(tds) > 3 else ""
        r3          = (await tds[4].inner_text()).strip() if len(tds) > 4 else ""
        r4          = (await tds[5].inner_text()).strip() if len(tds) > 5 else ""
        total_score = (await tds[6].inner_text()).strip() if len(tds) > 6 else ""
        total_par   = (await tds[7].inner_text()).strip() if len(tds) > 7 else ""
        if name:
            rows.append({
                "Pos": pos,
                "Name": name,
                "R1": r1,
                "R2": r2,
                "R3": r3,
                "R4": r4,
                "Total Score": total_score,
                "Total Par": total_par,
            })
    return rows


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

        # Dismiss cookie banner
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

        # ── Era loop ──────────────────────────────────────────────────────────
        # For each era: open the dropdown, click the era tab to get its year
        # list, close without loading anything, then iterate every year —
        # clicking it fresh each time so the table is always up to date.

        eras = [
            (".yearNav > li:nth-child(1)", "2025-1996"),
            (".yearNav > li:nth-child(2)", "1995-1966"),
            (".yearNav > li:nth-child(3)", "1965-1934"),
        ]

        for era_selector, era_label in eras:
            print(f"\nEra {era_label}: collecting year list...")

            # Open dropdown and click era just to read its year list
            await page.click(".tournament-year-select")
            await page.wait_for_timeout(1000)
            await page.click(era_selector, force=True)
            await page.wait_for_timeout(500)

            year_lis = await page.query_selector_all("div.nav.show .year-list li")
            years = []
            for li in year_lis:
                text = (await li.inner_text()).strip()
                if text.isdigit():
                    years.append(text)

            # Close dropdown without triggering a table load
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(300)

            print(f"Era {era_label}: scraping {len(years)} years: {years}")

            for year in years:
                print(f"  Scraping {year}...")

                # Re-open dropdown, click era, then click the specific year
                await page.click(".tournament-year-select")
                await page.wait_for_timeout(1000)
                await page.click(era_selector, force=True)
                await page.wait_for_timeout(500)

                year_lis_fresh = await page.query_selector_all("div.nav.show .year-list li")
                clicked = False
                for li in year_lis_fresh:
                    if (await li.inner_text()).strip() == year:
                        await li.evaluate("el => el.click()")
                        clicked = True
                        break

                if not clicked:
                    print(f"    Could not find {year}, skipping.")
                    continue

                await page.wait_for_selector(".winners-table tbody tr", timeout=10000)
                await page.wait_for_timeout(500)

                for row in await scrape_table(page):
                    row["Year"] = int(year)
                    all_rows.append(row)

        await browser.close()

    masters_players_df = pd.DataFrame(all_rows, columns=[
        "Year", "Pos", "Name", "R1", "R2", "R3", "R4", "Total Score", "Total Par"
    ])
    masters_players_df = masters_players_df.drop_duplicates().reset_index(drop=True)

    print(f"\nScraped {len(masters_players_df)} player-year records.")
    print(masters_players_df.head(10))
    return masters_players_df


async def main():
    df = await scrape_masters_players()

    output_path = "C:\\Personal Projects\\masters_players.csv"
    try:
        existing = pd.read_csv(output_path)
        df = pd.concat([existing, df]).drop_duplicates().reset_index(drop=True)
        print(f"Merged with existing CSV — {len(df)} total records after dedup.")
    except FileNotFoundError:
        pass

    df.to_csv(output_path, index=False)
    print(f"\nSaved to {output_path}")
    return df


if __name__ == "__main__":
    asyncio.run(main())



CSV_PATH = "C:\\Personal Projects\\masters_players.csv"

df = pd.read_csv(CSV_PATH)
print(f"Rows before cleanup: {len(df)}")

# Get the set of player+score combinations that belong to 2025
players_2025 = df[df['Year'] == 2025][['Name', 'R1', 'R2', 'R3', 'R4']].drop_duplicates()

# For 1995 and 1965, flag any row whose Name+R1-R4 matches a 2025 row
contaminated_years = [1995, 1965]
mask_bad = (
    df['Year'].isin(contaminated_years) &
    df[['Name', 'R1', 'R2', 'R3', 'R4']].apply(tuple, axis=1).isin(
        players_2025.apply(tuple, axis=1)
    )
)

print(f"Removing {mask_bad.sum()} contaminated rows "
      f"({mask_bad[df['Year']==1995].sum()} from 1995, "
      f"{mask_bad[df['Year']==1965].sum()} from 1965)")

df_clean = df[~mask_bad].reset_index(drop=True)
print(f"Rows after cleanup: {len(df_clean)}")
print()
print("Year counts after cleanup:")
print(df_clean[df_clean['Year'].isin([2025, 1995, 1965])].groupby('Year').size())

df_clean.to_csv(CSV_PATH, index=False)
print(f"\nSaved cleaned CSV to {CSV_PATH}")