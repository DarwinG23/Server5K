#!/usr/bin/env python3
"""
============================================================================
Script de Prueba de Carga - Server5K
============================================================================
Simula 16 jueces conectándose simultáneamente y enviando 15 registros cada uno
- Utiliza Redis como transport layer (channels_redis)
- Prueba conexiones WebSocket concurrentes
- Valida el sistema completo end-to-end

Uso: uv run python test_load_16_jueces.py
============================================================================
"""

import asyncio
import json
import random
import time
from datetime import datetime
from typing import List, Dict
import aiohttp
import websockets
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout

# Configuración
BASE_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000"
NUM_REGISTROS = 15

MAPEO_JUEZ_EQUIPO = {
    1: 26,   # juez1 -> Los Veloces
    2: 27,   # juez2 -> Corredores Unidos
    3: 28,   # juez3 -> Team Thunder
    4: 29,   # juez4 -> Atletas Elite
    5: 30,   # juez5 -> Racing Crew
    6: 31,   # juez6 -> Speed Masters
    7: 32,   # juez7 -> Los Invencibles
    8: 33,   # juez8 -> Running Stars
    9: 34,   # juez9 -> Team Phoenix
    10: 35,  # juez10 -> Campeones 5K
    11: 36,  # juez11 -> Relámpagos FC
    12: 37,  # juez12 -> Halcones Rápidos
    13: 38,  # juez13 -> Águilas Corredoras
    14: 39,  # juez14 -> Titanes del Asfalto
    15: 40,  # juez15 -> Fénix Runners
    16: 41,  # juez16 -> Centauros Veloces
}

console = Console()

# Credenciales de los 16 jueces
JUECES = [
    {"username": "juez1", "password": "juez1123", "nombre": "Joan Figuerola"},
    {"username": "juez2", "password": "juez2123", "nombre": "Salud Garriga"},
    {"username": "juez3", "password": "juez3123", "nombre": "Salomé Piña"},
    {"username": "juez4", "password": "juez4123", "nombre": "Dominga Martin"},
    {"username": "juez5", "password": "juez5123", "nombre": "Hector Lladó"},
    {"username": "juez6", "password": "juez6123", "nombre": "Encarnacion Cuenca"},
    {"username": "juez7", "password": "juez7123", "nombre": "Cecilio Machado"},
    {"username": "juez8", "password": "juez8123", "nombre": "Natanael Pinilla"},
    {"username": "juez9", "password": "juez9123", "nombre": "Toño Cerezo"},
    {"username": "juez10", "password": "juez10123", "nombre": "Hernán Girona"},
    {"username": "juez11", "password": "juez11123", "nombre": "Maura Figueras"},
    {"username": "juez12", "password": "juez12123", "nombre": "Rodrigo Falcón"},
    {"username": "juez13", "password": "juez13123", "nombre": "Pedro Arjona"},
    {"username": "juez14", "password": "juez14123", "nombre": "Julieta Reig"},
    {"username": "juez15", "password": "juez15123", "nombre": "Luis Miguel Donaire"},
    {"username": "juez16", "password": "juez16123", "nombre": "Edelmiro Riera"},
]


class ResultadosJuez:
    """Almacena los resultados de cada juez"""
    def __init__(self, username: str, nombre: str):
        self.username = username
        self.nombre = nombre
        self.login_exitoso = False
        self.token = None
        self.juez_id = None
        self.ws_conectado = False
        self.registros_enviados = 0
        self.registros_confirmados = 0
        self.tiempo_login = 0
        self.tiempo_ws = 0
        self.tiempo_envio = 0
        self.errores = []
        
    def agregar_error(self, error: str):
        self.errores.append(f"[{datetime.now().strftime('%H:%M:%S')}] {error}")


async def hacer_login(session: aiohttp.ClientSession, juez: Dict, resultado: ResultadosJuez) -> bool:
    """Realiza login de un juez y obtiene el token"""
    try:
        inicio = time.time()
        
        # Login
        async with session.post(
            f"{BASE_URL}/api/login/",
            json={"username": juez["username"], "password": juez["password"]},
            timeout=aiohttp.ClientTimeout(total=10)
        ) as response:
            if response.status != 200:
                error_data = await response.json()
                resultado.agregar_error(f"Login falló: {error_data.get('error', 'Error desconocido')}")
                return False
            
            data = await response.json()
            resultado.token = data.get("access")
            
        # Obtener info del juez
        async with session.get(
            f"{BASE_URL}/api/me/",
            headers={"Authorization": f"Bearer {resultado.token}"},
            timeout=aiohttp.ClientTimeout(total=10)
        ) as response:
            if response.status != 200:
                resultado.agregar_error("No se pudo obtener info del juez")
                return False
            
            data = await response.json()
            resultado.juez_id = data.get("id")
            
        resultado.tiempo_login = time.time() - inicio
        resultado.login_exitoso = True
        return True
        
    except Exception as e:
        resultado.agregar_error(f"Error en login: {str(e)}")
        return False


async def conectar_websocket(resultado: ResultadosJuez, equipo_id: int) -> None:
    """Conecta al WebSocket y envía 15 registros"""
    try:
        inicio_ws = time.time()
        
        uri = f"{WS_URL}/ws/juez/{resultado.juez_id}/?token={resultado.token}"
        
        async with websockets.connect(uri, ping_interval=20, ping_timeout=10) as websocket:
            resultado.ws_conectado = True
            resultado.tiempo_ws = time.time() - inicio_ws
            
            # Esperar mensaje de conexión establecida
            msg = await websocket.recv()
            data = json.loads(msg)
            
            if data.get("tipo") != "conexion_establecida":
                resultado.agregar_error(f"Mensaje inesperado: {data.get('tipo')}")
                return
            
            # Verificar que la competencia esté en curso
            competencia = data.get("competencia", {})
            if not competencia.get("en_curso"):
                resultado.agregar_error("La competencia no está en curso")
                return
            
            # Generar 15 registros de tiempo
            registros = []
            for i in range(NUM_REGISTROS):
                # Tiempo aleatorio entre 15-45 minutos (900000-2700000 ms)
                tiempo = random.randint(900000, 2700000)
                horas = tiempo // 3600000
                minutos = (tiempo % 3600000) // 60000
                segundos = (tiempo % 60000) // 1000
                milisegundos = tiempo % 1000
                
                registros.append({
                    "tiempo": tiempo,
                    "horas": horas,
                    "minutos": minutos,
                    "segundos": segundos,
                    "milisegundos": milisegundos
                })
            
            # Enviar batch de registros
            inicio_envio = time.time()
            mensaje = {
                "tipo": "registrar_tiempos",
                "equipo_id": equipo_id,
                "registros": registros
            }
            
            await websocket.send(json.dumps(mensaje))
            resultado.registros_enviados = NUM_REGISTROS
            
            # Esperar confirmación con timeout
            try:
                respuesta = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data_respuesta = json.loads(respuesta)
                
                resultado.tiempo_envio = time.time() - inicio_envio
                
                # Log de debug: mostrar qué respuesta recibimos
                print(f"[DEBUG {resultado.nombre}] Respuesta recibida: {data_respuesta.get('tipo')}")
                
                if data_respuesta.get("tipo") == "tiempos_registrados_batch":
                    resultado.registros_confirmados = data_respuesta.get("total_guardados", 0)
                    
                    if data_respuesta.get("total_fallidos", 0) > 0:
                        resultado.agregar_error(
                            f"{data_respuesta['total_fallidos']} registros fallaron"
                        )
                        # Mostrar detalles de errores
                        if data_respuesta.get("registros_fallidos"):
                            for fallo in data_respuesta["registros_fallidos"][:3]:  # Primeros 3
                                print(f"  ❌ {resultado.nombre}: {fallo.get('error', 'Error desconocido')}")
                elif data_respuesta.get("tipo") == "error":
                    resultado.agregar_error(f"Error del servidor: {data_respuesta.get('mensaje', 'Error desconocido')}")
                else:
                    resultado.agregar_error(f"Respuesta inesperada: {data_respuesta.get('tipo')} - {data_respuesta}")
            except asyncio.TimeoutError:
                resultado.agregar_error("Timeout esperando confirmación del servidor (5s)")
            except json.JSONDecodeError as e:
                resultado.agregar_error(f"Respuesta no es JSON válido: {str(e)}")
            
    except websockets.exceptions.WebSocketException as e:
        resultado.agregar_error(f"Error WebSocket: {str(e)}")
    except Exception as e:
        resultado.agregar_error(f"Error al enviar registros: {str(e)}")


async def procesar_juez(session: aiohttp.ClientSession, juez: Dict, indice: int) -> ResultadosJuez:
    """Procesa un juez completo: login + WebSocket + envío"""
    resultado = ResultadosJuez(juez["username"], juez["nombre"])
    
    # Paso 1: Login
    login_ok = await hacer_login(session, juez, resultado)
    if not login_ok:
        return resultado
    
    # Paso 2: WebSocket y envío de registros
    # Usar el mapeo correcto: los equipos tienen IDs 26-41, no 1-16
    equipo_id = MAPEO_JUEZ_EQUIPO.get(indice + 1, indice + 1)
    await conectar_websocket(resultado, equipo_id)
    
    return resultado


async def main():
    """Función principal que ejecuta la prueba de carga"""
    
    console.clear()
    console.print("\n")
    console.print("=" * 80, style="cyan")
    console.print("  🧪 PRUEBA DE CARGA - SERVER5K", style="bold green", justify="center")
    console.print("  16 Jueces Simultáneos × 15 Registros = 240 Registros Totales", style="yellow", justify="center")
    console.print("=" * 80, style="cyan")
    console.print("\n")
    
    # Crear tabla de progreso
    tabla = Table(show_header=True, header_style="bold magenta")
    tabla.add_column("#", style="dim", width=3)
    tabla.add_column("Juez", width=20)
    tabla.add_column("Estado", width=50)
    
    for i, juez in enumerate(JUECES, 1):
        tabla.add_row(str(i), juez["nombre"], "⏳ Esperando...")
    
    console.print(tabla)
    console.print("\n")
    
    inicio_total = time.time()
    
    # Crear sesión HTTP compartida
    async with aiohttp.ClientSession() as session:
        # Ejecutar todos los jueces en paralelo
        with console.status("[bold green]Procesando 16 jueces simultáneamente...") as status:
            tareas = [
                procesar_juez(session, juez, i) 
                for i, juez in enumerate(JUECES)
            ]
            resultados = await asyncio.gather(*tareas)
    
    tiempo_total = time.time() - inicio_total
    
    # Mostrar resultados
    console.print("\n")
    console.print("=" * 80, style="cyan")
    console.print("  📊 RESULTADOS DE LA PRUEBA", style="bold green", justify="center")
    console.print("=" * 80, style="cyan")
    console.print("\n")
    
    # Tabla de resultados detallados
    tabla_resultados = Table(show_header=True, header_style="bold cyan")
    tabla_resultados.add_column("#", justify="center", width=3)
    tabla_resultados.add_column("Juez", width=20)
    tabla_resultados.add_column("Login", justify="center", width=8)
    tabla_resultados.add_column("WS", justify="center", width=8)
    tabla_resultados.add_column("Enviados", justify="center", width=9)
    tabla_resultados.add_column("Confirmados", justify="center", width=11)
    tabla_resultados.add_column("Tiempo", justify="right", width=10)
    
    login_exitosos = 0
    ws_exitosos = 0
    total_enviados = 0
    total_confirmados = 0
    jueces_con_errores = []
    
    for i, resultado in enumerate(resultados, 1):
        # Contadores
        if resultado.login_exitoso:
            login_exitosos += 1
        if resultado.ws_conectado:
            ws_exitosos += 1
        total_enviados += resultado.registros_enviados
        total_confirmados += resultado.registros_confirmados
        
        if resultado.errores:
            jueces_con_errores.append((i, resultado))
        
        # Símbolos de estado
        login_icon = "✅" if resultado.login_exitoso else "❌"
        ws_icon = "✅" if resultado.ws_conectado else "❌"
        
        # Colores según éxito
        enviados_color = "green" if resultado.registros_enviados == NUM_REGISTROS else "red"
        confirmados_color = "green" if resultado.registros_confirmados == NUM_REGISTROS else "yellow"
        
        tiempo_total_juez = resultado.tiempo_login + resultado.tiempo_ws + resultado.tiempo_envio
        
        tabla_resultados.add_row(
            str(i),
            resultado.nombre[:18],
            login_icon,
            ws_icon,
            f"[{enviados_color}]{resultado.registros_enviados}[/{enviados_color}]",
            f"[{confirmados_color}]{resultado.registros_confirmados}[/{confirmados_color}]",
            f"{tiempo_total_juez:.2f}s"
        )
    
    console.print(tabla_resultados)
    console.print("\n")
    
    # Resumen estadístico
    tabla_resumen = Table(show_header=False, box=None, padding=(0, 2))
    tabla_resumen.add_column(style="bold cyan", justify="right")
    tabla_resumen.add_column(style="bold white")
    
    tabla_resumen.add_row("⏱️  Tiempo Total:", f"{tiempo_total:.2f} segundos")
    tabla_resumen.add_row("👥 Jueces Procesados:", f"{len(JUECES)}")
    tabla_resumen.add_row("✅ Logins Exitosos:", f"{login_exitosos}/{len(JUECES)}")
    tabla_resumen.add_row("🔌 WebSockets Conectados:", f"{ws_exitosos}/{len(JUECES)}")
    tabla_resumen.add_row("📤 Registros Enviados:", f"{total_enviados} (esperados: {len(JUECES) * NUM_REGISTROS})")
    tabla_resumen.add_row("✅ Registros Confirmados:", f"{total_confirmados}/{total_enviados}")
    tabla_resumen.add_row("📊 Tasa de Éxito:", f"{(total_confirmados/total_enviados*100):.1f}%" if total_enviados > 0 else "N/A")
    tabla_resumen.add_row("⚡ Throughput:", f"{total_confirmados/tiempo_total:.1f} registros/segundo")
    
    panel_resumen = Panel(
        tabla_resumen,
        title="[bold green]📈 Estadísticas Generales",
        border_style="green"
    )
    console.print(panel_resumen)
    console.print("\n")
    
    # Mostrar errores si los hay
    if jueces_con_errores:
        console.print("[bold red]⚠️  JUECES CON ERRORES:[/bold red]\n")
        for idx, resultado in jueces_con_errores:
            console.print(f"[yellow]Juez #{idx} - {resultado.nombre}:[/yellow]")
            for error in resultado.errores:
                console.print(f"  • {error}", style="red")
            console.print()
    
    # Resultado final
    console.print("=" * 80, style="cyan")
    if total_confirmados == len(JUECES) * NUM_REGISTROS:
        console.print("  ✅ PRUEBA EXITOSA - Todos los registros fueron confirmados", 
                     style="bold green", justify="center")
    elif total_confirmados > 0:
        console.print("  ⚠️  PRUEBA PARCIAL - Algunos registros fallaron", 
                     style="bold yellow", justify="center")
    else:
        console.print("  ❌ PRUEBA FALLIDA - No se confirmaron registros", 
                     style="bold red", justify="center")
    console.print("=" * 80, style="cyan")
    console.print("\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]⏹️  Prueba interrumpida por el usuario[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ Error fatal: {e}[/red]")
