from PIL import Image
import io
def crop_png_bytes(png_bytes: bytes, crop_box: tuple[int,int,int,int]) -> bytes:
# crop_box: (left, top, right, bottom)
img = Image.open(io.BytesIO(png_bytes))
cropped = img.crop(crop_box)
out = io.BytesIO()
cropped.save(out, format="PNG")
return out.getvalue()
async def screenshot_element(page, selector: str) -> bytes:
el = await page.query_selector(selector)
if not el:
return await page.screenshot(full_page=True)
return await el.screenshot()
# NOTE: exact selectors for image viewer will be site-specific.
# The worker should try:
# 1) open image -> new tab/open original (if any)
# 2) else fullscreen + zoom -> screenshot_element(image_container) -> crop_png_bytes
