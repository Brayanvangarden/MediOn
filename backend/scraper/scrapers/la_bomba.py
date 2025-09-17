import sys
import asyncio
import urllib.parse
from playwright.async_api import async_playwright, TimeoutError

async def buscar_la_bomba(query: str, max_resultados: int = 5):
    """
    Busca productos en Farmacia La Bomba.
    """
    resultados = []
    try:
        async with async_playwright() as p:
            # Lanzar el navegador en modo headless para mayor velocidad
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Codificar la búsqueda para usarla en el URL
            encoded_query = urllib.parse.quote(query)
            url = f"https://www.farmacialabomba.com/busqueda?f={encoded_query}"
            
            await page.goto(url)

            # Esperar a que el contenedor principal de los productos cargue
            await page.wait_for_selector('div.product-card-content', timeout=20000)

            # Seleccionar todos los elementos que contienen un producto
            products = await page.query_selector_all('div.card-costum-shadow')

            for product in products[:max_resultados]:
                try:
                    # Selector para el nombre del producto
                    name_el = await product.query_selector('h3.title-card-product')
                    name = await name_el.inner_text() if name_el else "No encontrado"
                    
                    # Selector para el precio
                    price_el = await product.query_selector('span.product-price')
                    # Eliminar la coma y el texto "i.v.a.i" para limpiar el precio
                    price = (await price_el.inner_text()).strip().replace("i.v.a.i", "").strip() if price_el else "No encontrado"
                    
                    # Selector para la URL del producto
                    url_el = await product.query_selector('a[href^="/detalle-producto"]')
                    product_url = "https://www.farmacialabomba.com" + await url_el.get_attribute('href') if url_el else "No encontrado"

                    resultados.append({
                        "descripcion": name,
                        "precio": price,
                        "url": product_url
                    })
                except Exception as e:
                    print(f"Error procesando un producto en La Bomba: {e}")
                    continue

            await browser.close()
            mensaje = None if resultados else "No se encontraron productos."
            return {"tienda": "La Bomba", "productos": resultados, "mensaje": mensaje}

    except TimeoutError:
        return {"tienda": "La Bomba", "productos": [], "mensaje": "Timeout: la página tardó demasiado en cargar. Puede que no haya resultados."}
    except Exception as e:
        return {"tienda": "La Bomba", "productos": [], "mensaje": f"Error inesperado: {str(e)}"}

# ---------------- Main para prueba ----------------
async def main():
    producto = input("🔎 Ingresa el producto a buscar en Farmacia La Bomba: ")
    max_resultados = input("🔹 Número máximo de resultados (por defecto 5): ")

    try:
        max_resultados = int(max_resultados)
    except ValueError:
        max_resultados = 5

    resultados = await buscar_la_bomba(producto, max_resultados)

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