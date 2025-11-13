# Script para iniciar el servidor con WebSocket support
Write-Host "🚀 Iniciando servidor con Daphne (WebSocket + HTTP)..." -ForegroundColor Green
Write-Host ""
Write-Host "� Recolectando archivos estáticos..." -ForegroundColor Cyan
uv run python manage.py collectstatic --noinput | Out-Null
Write-Host "✅ Archivos estáticos listos" -ForegroundColor Green
Write-Host ""
Write-Host "�📍 Servidor corriendo en:" -ForegroundColor Cyan
Write-Host "   HTTP/API:    http://127.0.0.1:8000/" -ForegroundColor White
Write-Host "   Admin:       http://127.0.0.1:8000/admin/" -ForegroundColor White
Write-Host "   WebSocket:   ws://127.0.0.1:8000/ws/juez/{id}/" -ForegroundColor White
Write-Host ""
Write-Host "⏹️  Para detener: Ctrl+C" -ForegroundColor Yellow
Write-Host ""

uv run daphne -b 127.0.0.1 -p 8000 server.asgi:application
