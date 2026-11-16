import sys, asyncio
from playwright.async_api import async_playwright
async def main(src, out, landscape):
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page()
        await pg.goto(f"file:///home/claude/meet/{src}"); await pg.wait_for_timeout(300)
        await pg.pdf(path=out, prefer_css_page_size=True, print_background=True)
        await b.close()
asyncio.run(main(sys.argv[1], sys.argv[2], True))
