from django import forms
from .models import Reserva
from core.models import Asignatura, Carrera, Aula, Bloque
from datetime import time

class ReservaForm(forms.ModelForm):
    """Formulario para crear una nueva reserva de Chromebooks"""
    
    # Override de campos para personalizar
    fecha_uso = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'input',
            'required': True
        }),
        label='Fecha de Uso'
    )
    
    hora_inicio = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'input',
            'required': True
        }),
        label='Hora de Inicio'
    )
    
    hora_fin = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'input',
            'required': True
        }),
        label='Hora de Fin'
    )
    
    id_carrera = forms.ModelChoiceField(
        queryset=Carrera.objects.all(),
        widget=forms.Select(attrs={'class': 'select', 'id': 'id_carrera'}),
        label='Carrera',
        empty_label='Seleccione una carrera'
    )
    
    id_asignatura = forms.ModelChoiceField(
        queryset=Asignatura.objects.all(),
        widget=forms.Select(attrs={'class': 'select', 'id': 'id_asignatura'}),
        label='Asignatura',
        empty_label='Seleccione primero una carrera',
        required=True
    )
    
    bloque = forms.ModelChoiceField(
        queryset=Bloque.objects.all(),
        widget=forms.Select(attrs={'class': 'select'}),
        label='Bloque',
        empty_label='Seleccione un bloque'
    )
    
    id_aula = forms.ModelChoiceField(
        queryset=Aula.objects.all(),
        widget=forms.Select(attrs={'class': 'select'}),
        label='Aula',
        empty_label='Seleccione un aula'
    )
    
    cant_solicitada = forms.IntegerField(
    min_value=1,
    max_value=100,  # ajusta según la capacidad máxima disponible
    widget=forms.NumberInput(attrs={
        'class': 'input',
        'type': 'number',
        'placeholder': 'Ingrese cantidad',
        'required': True
    }),
    label='Número de Chromebooks'
    )

    
    responsable_entrega = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'input',
            'placeholder': 'Ingrese el nombre del responsable',
            'autocomplete': 'off',
            'id': 'id_responsable_entrega'
        }),
        label='Responsable de la Entrega'
    )
    
    telefono_contacto = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'input',
            'placeholder': '0999999999',
            'pattern': '[0-9]{10}',
            'maxlength': '10'
        }),
        label='Teléfono de Contacto'
    )
    
    class Meta:
        model = Reserva
        fields = ['fecha_uso', 'hora_inicio', 'hora_fin', 'id_asignatura', 
                  'id_carrera', 'id_aula', 'cant_solicitada', 
                  'responsable_entrega', 'telefono_contacto']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Agregar campo bloque (no está en el modelo pero lo usaremos para filtrar aulas)
        self.fields['bloque'] = forms.ModelChoiceField(
            queryset=Bloque.objects.all(),
            widget=forms.Select(attrs={'class': 'select', 'id': 'id_bloque'}),
            label='Bloque',
            empty_label='Seleccione un bloque',
            required=True
        )
    
    def clean_hora_fin(self):
        """Validar que la hora de fin no sea posterior a las 17:00"""
        hora_fin = self.cleaned_data.get('hora_fin')
        hora_limite = time(17, 0)  # 17:00
        
        if hora_fin and hora_fin > hora_limite:
            raise forms.ValidationError('La hora de fin no puede ser posterior a las 17:00.')
        
        return hora_fin
    
    def clean(self):
        cleaned_data = super().clean()
        hora_inicio = cleaned_data.get('hora_inicio')
        hora_fin = cleaned_data.get('hora_fin')
        
        if hora_inicio and hora_fin:
            if hora_fin <= hora_inicio:
                raise forms.ValidationError('La hora de fin debe ser posterior a la hora de inicio.')
        
        return cleaned_data