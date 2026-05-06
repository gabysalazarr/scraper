import asyncio
from playwright.async_api import async_playwright
from feedgen.feed import FeedGenerator
from xml.dom import minidom

async def scrape_calendar_with_time():
    fg = FeedGenerator()
    fg.title('Bastrop Monthly Calendar')
    fg.link(href='https://bastrop-tx.municodemeetings.com/calendar/month', rel='alternate')
    fg.description('Meetings with Date/Time.')
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://bastrop-tx.municodemeetings.com/calendar/month", wait_until="networkidle")
        print("waiting for items")
        await page.wait_for_selector(".view-item-calendar", timeout=10000)
        items = await page.query_selector_all(".view-item-calendar")

        for item in items:
            # 1. get title
            title_el = await item.query_selector(".views-field-title")
            title_text = await title_el.inner_text() if title_el else "Unknown Meeting"
            
            # 2. get time
            time_el = await item.query_selector(".views-field-field-calendar-date")
            full_time_text = await time_el.inner_text() if time_el else "Unknown Time"

            # 3. get date
            cell = await item.evaluate_handle("el => el.closest('td')")
            raw_date = await cell.get_attribute("data-date") if cell else ""

            # 4. handle link
            link_el = await item.query_selector("a")
            url = await link_el.get_attribute("href") if link_el else page.url
            full_url = url if url.startswith('http') else f"https://bastrop-tx.municodemeetings.com{url}"

            # 5. format that it to be added to xml
            combined_info = f"{raw_date} | {full_time_text.strip()}: {title_text.strip()}"
            fe = fg.add_entry()
            fe.title(combined_info)
            fe.link(href=full_url)
            fe.id(full_url)
            fe.description(f"Full Schedule: {full_time_text.strip()}")

        # 6. format and save to file
        raw_xml_str = fg.rss_str(pretty=True).decode('utf-8')
        collapsed_xml = "".join([line.strip() for line in raw_xml_str.splitlines()])
        reparsed = minidom.parseString(collapsed_xml)
        pretty_xml = reparsed.toprettyxml(indent="    ")
        final_lines = [line for line in pretty_xml.splitlines() if line.strip()]
        with open("monthly_calendar.xml", "w", encoding="utf-8") as f:
            f.write("\n".join(final_lines))
        print(f"SUCCESS: Captured {len(fg.entry())} meetings.")
        await browser.close()
if __name__ == "__main__":
    asyncio.run(scrape_calendar_with_time())



