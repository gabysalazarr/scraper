import asyncio 
from playwright.async_api import async_playwright
from feedgen.feed import FeedGenerator
from xml.dom import minidom

# scrape data using playwright
# strcture data into RSS feed
# save it as clean XML file

async def scrape_with_dates():
    # create rss feed structure 
    fg = FeedGenerator()
    fg.title('Bastrop TX Meetings (with Dates)')
    fg.link(href='https://bastrop-tx.municodemeetings.com/?field_microsite_tid_selective=27', rel='alternate')
    fg.description('Comprehensive meeting data including dates.')
    async with async_playwright() as p:
        # launch browser with playwright
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        print("opening website") # DEBUG
        # ensure full load
        await page.goto("https://bastrop-tx.municodemeetings.com/?field_microsite_tid_selective=27", wait_until="networkidle")
        # load all meeting pages
        while True:
            load_more = await page.query_selector("li.pager__item a:has-text('View Additional Meetings')")
            if load_more and await load_more.is_visible():
                print("next page") # DEBUG
                await load_more.click() 
                await asyncio.sleep(3) # wait for complete load
            else:
                break
        # extract data
        rows = await page.query_selector_all("tbody tr") # <tbody> -> <tr>; 
        print(f"extracting data from {len(rows)} rows") # DEBUG
        for row in rows:
            cells = await row.query_selector_all("td")
            if len(cells) >= 2:
                # get date from col 0 and name from col 1
                raw_date = await cells[0].inner_text()
                raw_name = await cells[1].inner_text()
                # clean text (xtra spaces/newlines)
                clean_date = raw_date.strip()
                clean_name = raw_name.strip()
                # create a combined title for the RSS feed
                combined_title = f"{clean_date}: {clean_name}"
                # meeting link
                link_el = await row.query_selector("a")
                if link_el:
                    raw_url = await link_el.get_attribute("href")
                    # fix url
                    full_url = raw_url if raw_url.startswith('http') else f"https://bastrop-tx.municodemeetings.com{raw_url}"
                else:
                    full_url = "https://bastrop-tx.municodemeetings.com/"
                # add entry to rss feed
                if clean_name:
                    fe = fg.add_entry()
                    fe.title(combined_title)
                    fe.link(href=full_url)
                    fe.id(full_url)
                    fe.description(f"Meeting Date: {clean_date}")

        print("formatting and saving") # DEBUG
        # creare raw
        raw_xml_str = fg.rss_str(pretty=True).decode('utf-8')
        # format
        collapsed_xml = "".join([line.strip() for line in raw_xml_str.splitlines()])
        reparsed = minidom.parseString(collapsed_xml)
        pretty_xml = reparsed.toprettyxml(indent="    ")
        final_lines = [line for line in pretty_xml.splitlines() if line.strip()]
        # save file
        with open("bastrop_meetings_with_dates.xml", "w", encoding="utf-8") as f:
            f.write("\n".join(final_lines))
        print(f"\nSUCCESS: Saved {len(fg.entry())} items to 'meeting_agenda.xml'")
        await browser.close()
if __name__ == "__main__":
    asyncio.run(scrape_with_dates())



