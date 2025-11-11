from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializers import EnvioTiemposSerializer
from .models import Equipo, RegistroTiempo


class EnviarTiemposView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = EnvioTiemposSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        equipo_id = serializer.validated_data['equipo_id']
        registros = serializer.validated_data['registros'][:15]

        # validar juez
        try:
            juez = request.user.juez_profile
        except Exception:
            return Response({'detail': 'Usuario no es juez.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            equipo = Equipo.objects.get(pk=equipo_id)
        except Equipo.DoesNotExist:
            return Response({'detail': 'Equipo no existe.'}, status=status.HTTP_400_BAD_REQUEST)

        if equipo.juez_asignado_id != juez.id:
            return Response({'detail': 'No autorizado para enviar registros para este equipo.'}, status=status.HTTP_403_FORBIDDEN)

        created = []
        for reg in registros:
            rt = RegistroTiempo.objects.create(
                equipo=equipo,
                tiempo=reg['tiempo'],
                timestamp=reg['timestamp']
            )
            created.append(str(rt.id_registro))
        return Response({'created': created}, status=status.HTTP_201_CREATED)
from django.shortcuts import render

# Create your views here.
