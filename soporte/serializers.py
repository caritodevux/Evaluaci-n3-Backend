from rest_framework import serializers
from .models import Solicitud


class SolicitudSerializer(serializers.ModelSerializer):

    usuario = serializers.ReadOnlyField(source='usuario.username')

    class Meta:
        model = Solicitud
        fields = [
            'id',
            'titulo',
            'descripcion',
            'categoria',
            'estado',
            'fecha_creacion',
            'usuario',
        ]
        read_only_fields = [
            'id',
            'fecha_creacion',
        ]

    def validate_titulo(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                "El título debe contener al menos 3 caracteres."
            )
        return value

    def validate_descripcion(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError(
                "La descripción debe contener al menos 10 caracteres."
            )
        return value