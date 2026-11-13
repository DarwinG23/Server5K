from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from app.models import Competencia, Equipo, Juez, RegistroTiempo


class AuthorizationSecurityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.password = 'password-seguro-123'
        self.juez_a = self._create_juez('juez-a')
        self.juez_b = self._create_juez('juez-b')
        competencia = Competencia.objects.create(
            name='Competencia de prueba',
            datetime=timezone.now(),
            is_running=True,
        )
        self.equipo_a = Equipo.objects.create(
            name='Equipo A',
            number=1,
            competition=competencia,
            judge=self.juez_a,
        )
        self.equipo_b = Equipo.objects.create(
            name='Equipo B',
            number=2,
            competition=competencia,
            judge=self.juez_b,
        )
        RegistroTiempo.objects.create(team=self.equipo_b, time=120000)

    def _create_juez(self, username):
        juez = Juez(username=username, email=f'{username}@example.com')
        juez.set_password(self.password)
        juez.save()
        return juez

    def _authenticate(self, juez):
        response = self.client.post(
            reverse('login'),
            {'username': juez.username, 'password': self.password},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {response.data['access']}"
        )

    def test_juez_cannot_retrieve_another_juez_team(self):
        self._authenticate(self.juez_a)

        response = self.client.get(
            reverse('equipo-detail', args=[self.equipo_b.id])
        )

        self.assertEqual(response.status_code, 404)

    def test_juez_cannot_read_another_juez_records_status(self):
        self._authenticate(self.juez_a)

        response = self.client.get(
            reverse('estado_registros', args=[self.equipo_b.id])
        )

        self.assertEqual(response.status_code, 404)

    def test_juez_cannot_submit_records_for_another_juez_team(self):
        self._authenticate(self.juez_a)
        registros = [
            {
                'tiempo': 100000 + index,
                'horas': 0,
                'minutos': 1,
                'segundos': 40,
                'milisegundos': index,
            }
            for index in range(15)
        ]

        response = self.client.post(
            reverse('registrar_tiempos', args=[self.equipo_b.id]),
            {'registros': registros},
            format='json',
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(RegistroTiempo.objects.filter(team=self.equipo_b).count(), 1)

    def test_admin_endpoint_rejects_common_user(self):
        self._authenticate(self.juez_a)

        response = self.client.get(reverse('admin_estado_competencias'))

        self.assertEqual(response.status_code, 403)

    def test_admin_endpoint_accepts_staff_session(self):
        admin_user = get_user_model().objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password=self.password,
        )
        self.client.force_login(admin_user)

        response = self.client.get(reverse('admin_estado_competencias'))

        self.assertEqual(response.status_code, 200)

    def test_tampered_access_token_is_rejected(self):
        self._authenticate(self.juez_a)
        token = self.client._credentials['HTTP_AUTHORIZATION'].split()[1]
        tampered_token = f'{token[:-1]}{"A" if token[-1] != "A" else "B"}'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tampered_token}')

        response = self.client.get(reverse('me'))

        self.assertEqual(response.status_code, 401)

    @override_settings(SIMPLE_JWT={'ACCESS_TOKEN_LIFETIME': timedelta(seconds=1)})
    def test_expired_access_token_is_rejected(self):
        self._authenticate(self.juez_a)
        token = AccessToken(
            self.client._credentials['HTTP_AUTHORIZATION'].split()[1]
        )
        token.set_exp(lifetime=timedelta(seconds=-1))
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        response = self.client.get(reverse('me'))

        self.assertEqual(response.status_code, 401)
