from django.db import models
from django.contrib.auth.models import User


class Solicitud(models.Model):

    CATEGORIAS = [
        ('Hardware', 'Hardware'),
        ('Software', 'Software'),
        ('Redes', 'Redes'),
    ]

    ESTADOS = [
        ('Pendiente', 'Pendiente'),
        ('En proceso', 'En proceso'),
        ('Resuelta', 'Resuelta'),
    ]

    titulo = models.CharField(max_length=100)
    descripcion = models.TextField()
    categoria = models.CharField(max_length=20, choices=CATEGORIAS)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='Pendiente')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='solicitudes'
    )

    class Meta:
        ordering = ['-fecha_creacion']

    def __str__(self):
        return self.titulo