import asyncio


def capture(url, fmt="png", viewport=(1280, 800), full_page=False, device=""):
    return asyncio.run(_capture_async(url, fmt, viewport, full_page, device))


async def _capture_async(url, fmt, viewport, full_page, device):
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context(viewport={"width": viewport[0], "height": viewport[1]})
        if device:
            ctx = await browser.new_context(**p.devices.get(device, {}))
        page = await ctx.new_page()
        await page.goto(url, wait_until="networkidle", timeout=30000)
        return await page.screenshot(type=fmt, full_page=full_page)
