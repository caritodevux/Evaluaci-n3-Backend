from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from .models import Solicitud
from .serializers import SolicitudSerializer


class SolicitudViewSet(viewsets.ModelViewSet):

    serializer_class = SolicitudSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Administrador: ve todas. Usuario normal: solo las suyas.
        if self.request.user.is_staff:
            return Solicitud.objects.all()
        return Solicitud.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        user = self.request.user
        estado = serializer.validated_data.get('estado', 'Pendiente')
        # Un usuario normal no puede definir el estado
        if not user.is_staff and estado != 'Pendiente':
            raise PermissionDenied('Solo un administrador puede definir el estado.')
        # El propietario lo asigna el servidor, no el cliente
        serializer.save(usuario=user)

    def perform_update(self, serializer):
        nuevo = serializer.validated_data.get('estado')
        if (not self.request.user.is_staff
                and nuevo is not None
                and nuevo != serializer.instance.estado):
            raise PermissionDenied('Solo un administrador puede cambiar el estado.')
        serializer.save()

    def perform_destroy(self, instance):
        if not self.request.user.is_staff:
            raise PermissionDenied('Solo un administrador puede eliminar solicitudes.')
        instance.delete()