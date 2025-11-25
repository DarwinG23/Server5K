"""
Script para verificar la estructura de equipos y jueces en la BD
"""
import django
import os
import sys

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from app.models import Juez, Equipo, Competencia

def main():
    print("\n" + "="*80)
    print("  📊 VERIFICACIÓN DE EQUIPOS Y JUECES")
    print("="*80 + "\n")
    
    # Verificar competencias
    competencias = Competencia.objects.all()
    print(f"🏁 Competencias encontradas: {competencias.count()}")
    for comp in competencias:
        print(f"   - ID {comp.id}: {comp.nombre} (en_curso: {comp.en_curso})")
    
    # Verificar jueces
    jueces = Juez.objects.all().order_by('id')
    print(f"\n👨‍⚖️ Jueces encontrados: {jueces.count()}")
    for juez in jueces:
        nombre = getattr(juez, 'nombre_completo', juez.username)
        print(f"   - ID {juez.id}: {juez.username} | Competencia: {juez.competencia_id}")
    
    # Verificar equipos
    equipos = Equipo.objects.all().order_by('id')
    print(f"\n🏃 Equipos encontrados: {equipos.count()}")
    
    if equipos.count() == 0:
        print("   ❌ NO HAY EQUIPOS CREADOS")
        print("\n💡 Solución: Ejecutar 'uv run python manage.py populate_data'")
    else:
        for equipo in equipos:
            juez_asignado = equipo.juez_asignado
            print(f"   - Equipo ID {equipo.id}: {equipo.nombre} (Dorsal {equipo.dorsal}) | Juez: {juez_asignado.username if juez_asignado else 'SIN ASIGNAR'}")
    
    # Verificar asignaciones
    sin_asignar = equipos.filter(juez_asignado__isnull=True).count()
    if sin_asignar > 0:
        print(f"\n⚠️  {sin_asignar} equipos SIN juez asignado")
    
    print("\n" + "="*80)
    
    # Generar mapeo para el script de test
    if jueces.count() > 0 and equipos.count() > 0:
        print("\n📋 MAPEO SUGERIDO PARA test_load_16_jueces.py:")
        print("-" * 80)
        
        # Obtener jueces con equipos asignados
        jueces_con_equipos = []
        for juez in jueces:
            equipos_asignados = Equipo.objects.filter(juez_asignado=juez)
            if equipos_asignados.exists():
                primer_equipo = equipos_asignados.first()
                jueces_con_equipos.append({
                    'juez_id': juez.id,
                    'username': juez.username,
                    'equipo_id': primer_equipo.id,
                    'equipo_nombre': primer_equipo.nombre
                })
        
        if len(jueces_con_equipos) > 0:
            print("\n# Usar este mapeo en el script:")
            print("MAPEO_JUEZ_EQUIPO = {")
            for idx, item in enumerate(jueces_con_equipos, 1):
                nombre = item.get('nombre', item['username'])
                print(f"    {idx}: {item['equipo_id']},  # {item['username']} -> {item['equipo_nombre']}")
            print("}")
            
            print("\n# En la función procesar_juez, cambiar:")
            print("# equipo_id = indice + 1")
            print("# POR:")
            print("# equipo_id = MAPEO_JUEZ_EQUIPO.get(indice + 1, indice + 1)")
        else:
            print("\n❌ Ningún juez tiene equipos asignados")
            print("💡 Ejecutar: uv run python manage.py populate_data")
    
    print("\n")

if __name__ == "__main__":
    main()
