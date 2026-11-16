import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page()
        await pg.goto("file:///home/claude/meet/guide.html"); await pg.wait_for_timeout(300)
        await pg.pdf(path="Research_Project_Personal_Study_Guide.pdf", prefer_css_page_size=True, print_background=True,
            display_header_footer=True, header_template="<span></span>",
            footer_template='<div style="font-family:Inter,sans-serif;font-size:8px;color:#6b7280;width:100%;padding:0 16mm;display:flex;justify-content:space-between"><span>SQL Judge project · personal study guide · 16 Nov 2026</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>')
        await b.close()
asyncio.run(main())
