import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from django.urls import get_resolver

resolver = get_resolver()

print("=" * 60)
print("URLs DISPONIBLES EN EL API")
print("=" * 60)

def show_urls(urlpatterns, prefix=''):
    for pattern in urlpatterns:
        if hasattr(pattern, 'url_patterns'):
            # Es un include
            new_prefix = prefix + str(pattern.pattern)
            show_urls(pattern.url_patterns, new_prefix)
        else:
            # Es una URL final
            full_url = prefix + str(pattern.pattern)
            name = pattern.name if pattern.name else '(sin nombre)'
            print(f"{full_url:50} -> {name}")

show_urls(resolver.url_patterns)
