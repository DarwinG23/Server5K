from django.core.management.base import BaseCommand
from mensajeria.mqtt_client import start_mqtt

class Command(BaseCommand):
    help = "Inicia el cliente MQTT para recibir y procesar mensajes de los jueces."

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Iniciando cliente MQTT..."))
        start_mqtt()

