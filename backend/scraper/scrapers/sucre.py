import sys
import asyncio
import urllib.parse
from playwright.async_api import async_playwright, TimeoutError

async def buscar_sucre(query: str, max_resultados: int = 5):
    """
    Busca productos en Farmacia Sucre.
    """
    resultados = []
    try:
        async with async_playwright() as p:
            # Lanzar el navegador en modo headless para mayor velocidad
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Codificar la búsqueda para usarla en el URL
            encoded_query = urllib.parse.quote(query)
            url = f"https://sucreenlinea.com/catalogsearch/result/?q={encoded_query}"
            
            await page.goto(url)

            # Esperar a que los resultados de búsqueda carguen
            await page.wait_for_selector('div.product-item-details', timeout=20000)

            # Seleccionar todos los elementos que contienen un producto
            products = await page.query_selector_all('div.product.details.product-item-details')

            for product in products[:max_resultados]:
                try:
                    # Selector para el nombre y el URL del producto
                    link_el = await product.query_selector('a.product-item-link')
                    name = await link_el.inner_text() if link_el else "No encontrado"
                    product_url = await link_el.get_attribute('href') if link_el else "No encontrado"
                    
                    # Selector para el precio
                    price_el = await product.query_selector('span.price')
                    # Eliminar la coma y el texto para limpiar el precio
                    price = (await price_el.inner_text()).strip() if price_el else "No encontrado"
                    
                    resultados.append({
                        "descripcion": name.strip(),
                        "precio": price.strip(),
                        "url": product_url
                    })
                except Exception as e:
                    print(f"Error procesando un producto en Sucre: {e}")
                    continue

            await browser.close()
            mensaje = None if resultados else "No se encontraron productos."
            return {"tienda": "Sucre", "productos": resultados, "mensaje": mensaje}

    except TimeoutError:
        return {"tienda": "Sucre", "productos": [], "mensaje": "Timeout: la página tardó demasiado en cargar. Puede que no haya resultados."}
    except Exception as e:
        return {"tienda": "Sucre", "productos": [], "mensaje": f"Error inesperado: {str(e)}"}

# ---------------- Main para prueba ----------------
async def main():
    producto = input("🔎 Ingresa el producto a buscar en Farmacia Sucre: ")
    max_resultados = input("🔹 Número máximo de resultados (por defecto 5): ")

    try:
        max_resultados = int(max_resultados)
    except ValueError:
        max_resultados = 5

    resultados = await buscar_sucre(producto, max_resultados)

    print("\n===== Resultados =====")
    if resultados["productos"]:
        for idx, prod in enumerate(resultados["productos"], start=1):
            print(f"{idx}. {prod['descripcion']}")
            print(f"   Precio: {prod['precio']}")
            print(f"   URL: {prod['url']}")
    else:
        print(resultados["mensaje"])

if __name__ == "__main__":
    # La política del evento es necesaria para Windows
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(main())