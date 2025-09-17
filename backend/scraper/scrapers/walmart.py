import sys
import asyncio
import urllib.parse

from playwright.async_api import async_playwright, TimeoutError

async def buscar_walmart(query: str, max_resultados: int = 5):
    """
    Busca productos en Walmart CR.
    """
    resultados = []
    try:
        async with async_playwright() as p:
            # headless=True para que no abra ventana
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # 💡 Corrección aquí: la URL de búsqueda correcta es /search?query=...
            encoded_query = urllib.parse.quote(query)
            url = f"https://www.walmart.co.cr/search?query={encoded_query}"
            
            await page.goto(url)

            try:
                await page.wait_for_selector('article.vtex-product-summary-2-x-element', timeout=20000)
            except TimeoutError:
                await browser.close()
                return {"tienda": "Walmart", "productos": [], "mensaje": "Timeout: la página tardó demasiado en cargar. Puede que no haya resultados."}

            products = await page.query_selector_all('article.vtex-product-summary-2-x-element')

            for product in products[:max_resultados]:
                try:
                    name_el = await product.query_selector('span.vtex-product-summary-2-x-productBrand')
                    name = await name_el.inner_text() if name_el else "No encontrado"

                    price_el = await product.query_selector('div.vtex-store-components-3-x-sellingPrice span.vtex-store-components-3-x-currencyContainer span')
                    price = await price_el.inner_text() if price_el else "No encontrado"

                    url_el = await product.query_selector('a[href*="/p/"]')
                    product_url = "https://www.walmart.co.cr" + await url_el.get_attribute('href') if url_el else "No encontrado"

                    resultados.append({
                        "descripcion": name.strip(),
                        "precio": price.strip(),
                        "url": product_url
                    })
                except Exception as e:
                    print(f"Error procesando un producto: {e}")
                    continue

            await browser.close()
            mensaje = None if resultados else "No se encontraron productos."
            return {"tienda": "Walmart", "productos": resultados, "mensaje": mensaje}

    except Exception as e:
        return {"tienda": "Walmart", "productos": [], "mensaje": f"Error inesperado: {str(e)}"}

# ---------------- Main para prueba ----------------
async def main():
    producto = input("🔎 Ingresa el producto a buscar en Walmart: ")
    max_resultados = input("🔹 Número máximo de resultados (por defecto 5): ")

    try:
        max_resultados = int(max_resultados)
    except ValueError:
        max_resultados = 5

    resultados = await buscar_walmart(producto, max_resultados)

    print("\n===== Resultados =====")
    if resultados["productos"]:
        for idx, prod in enumerate(resultados["productos"], start=1):
            print(f"{idx}. {prod['descripcion']}")
            print(f"  Precio: {prod['precio']}")
    else:
        print(resultados["mensaje"])


