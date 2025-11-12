from rest_framework import serializers


class TiempoSerializer(serializers.Serializer):
    timestamp = serializers.DateTimeField()
    tiempo = serializers.IntegerField()  # milliseconds


class EnvioTiemposSerializer(serializers.Serializer):
    equipo_id = serializers.IntegerField()
    registros = TiempoSerializer(many=True)
