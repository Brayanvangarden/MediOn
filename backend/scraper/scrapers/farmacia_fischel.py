import sys
import asyncio
import urllib.parse
from playwright.async_api import async_playwright, TimeoutError

async def buscar_fischel(query: str, max_resultados: int = 5):
    """
    Busca productos en Farmacia Fishel.
    """
    resultados = []
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            encoded_query = urllib.parse.quote(query)
            url = f"https://www.fischelenlinea.com/busqueda?f={encoded_query}"
            
            await page.goto(url)

            # Esperar a que los resultados de búsqueda carguen
            await page.wait_for_selector('div.card', timeout=20000)

            products = await page.query_selector_all('div[id*="productId"]')

            for product in products[:max_resultados]:
                try:
                    # Selector para el nombre del producto
                    name_el = await product.query_selector('h3.title-card-product')
                    name = await name_el.inner_text() if name_el else "No encontrado"
                    
                    # Selector para el precio
                    price_el = await product.query_selector('span.product-price')
                    price = await price_el.inner_text() if price_el else "No encontrado"

                    # Selector para el URL del producto
                    url_el = await product.query_selector('a[href^="/detalle-producto"]')
                    product_url = "https://www.fischelenlinea.com" + await url_el.get_attribute('href') if url_el else "No encontrado"

                    resultados.append({
                        "descripcion": name.strip(),
                        "precio": price.strip().replace("i.v.a.i", "").strip(),
                        "url": product_url
                    })
                except Exception as e:
                    print(f"Error procesando un producto en Fishel: {e}")
                    continue

            await browser.close()
            mensaje = None if resultados else "No se encontraron productos."
            return {"tienda": "Fischel", "productos": resultados, "mensaje": mensaje}

    except TimeoutError:
        return {"tienda": "Fischel", "productos": [], "mensaje": "Timeout: la página tardó demasiado en cargar. Puede que no haya resultados."}
    except Exception as e:
        return {"tienda": "Fischel", "productos": [], "mensaje": f"Error inesperado: {str(e)}"}

# ---------------- Main para prueba ----------------
async def main():
    producto = input("🔎 Ingresa el producto a buscar en Farmacia Fishel: ")
    max_resultados = input("🔹 Número máximo de resultados (por defecto 5): ")

    try:
        max_resultados = int(max_resultados)
    except ValueError:
        max_resultados = 5

    resultados = await buscar_fischel(producto, max_resultados)

    print("\n===== Resultados =====")
    if resultados["productos"]:
        for idx, prod in enumerate(resultados["productos"], start=1):
            print(f"{idx}. {prod['descripcion']}")
            print(f"  Precio: {prod['precio']}")
    else:
        print(resultados["mensaje"])

if __name__ == "__main__":
    asyncio.run(main())