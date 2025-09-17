import sys
import os
import asyncio
from fastapi import FastAPI, HTTPException
from multiprocessing import Process, Queue
from fastapi.middleware.cors import CORSMiddleware

# Asegúrate de que esta línea esté correcta para tu estructura de carpetas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 💡 Importar la lista de tiendas desde el paquete `scrapers`
from scraper.scrapers import TIENDAS

# Crear la app FastAPI
app = FastAPI(
    title="API Scraper MediOn",
    description="API para buscar y comparar productos de múltiples tiendas en Costa Rica",
    version="1.0.0"
)

# 💡 Configuración de CORS para permitir peticiones desde tu frontend
# Reemplaza el origen si tu frontend no corre en el puerto 5173
origins = [
    "http://localhost",
    "http://localhost:5173", # Puerto por defecto de Vite
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔹 Endpoint de prueba para verificar que la API responde
@app.get("/ping", summary="Probar conexión")
async def ping():
    """
    Endpoint simple para verificar que la API está funcionando.
    """
    return {"status": "ok"}

def run_scraper(scraper_func, query: str, max_resultados: int, queue: Queue):
    """
    Función que ejecuta un scraper específico en un proceso separado.
    """
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    results = asyncio.run(scraper_func(query, max_resultados))
    queue.put(results)

# 🔹 Endpoint principal para buscar productos en todas las tiendas
@app.get("/buscar", summary="Buscar productos en todas las tiendas")
async def buscar_producto(
    query: str, 
    max_resultados: int = 5
):
    """
    Endpoint para buscar productos en todas las tiendas registradas.

    **Parámetros:**
    - `query`: nombre del producto a buscar
    - `max_resultados`: cantidad máxima de resultados por tienda (por defecto 5)
    """
    try:
        all_results = []
        processes = []
        queues = []

        # 💡 Ejecutar cada scraper en un proceso separado
        for tienda in TIENDAS:
            result_queue = Queue()
            queues.append(result_queue)
            
            scraper_process = Process(target=run_scraper, args=(tienda, query, max_resultados, result_queue))
            processes.append(scraper_process)
            scraper_process.start()

        # 💡 Recopilar los resultados de cada proceso
        for i, process in enumerate(processes):
            # Usar un timeout para evitar que un scraper lento bloquee los demás
            try:
                resultados = await asyncio.to_thread(queues[i].get, timeout=60)
                all_results.append(resultados)
            except Exception as e:
                # Manejar el caso de que un scraper falle
                print(f"Error al obtener resultados del scraper {i}: {e}")
                
            process.join()

        return all_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
