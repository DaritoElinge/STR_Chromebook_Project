from django import forms
from .models import Usuario

class UsuarioAdminForm(forms.ModelForm):
    """Formulario personalizado para crear/editar usuarios en el admin"""
    
    # Campo de contraseña visible (no encriptado) para el admin
    password_input = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'placeholder': 'Ingrese la contraseña'}),
        required=False,
        help_text='Deje en blanco si no desea cambiar la contraseña (solo al editar).'
    )
    
    password_confirm = forms.CharField(
        label='Confirmar Contraseña',
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirme la contraseña'}),
        required=False,
        help_text='Ingrese la misma contraseña para verificación.'
    )
    
    class Meta:
        model = Usuario
        fields = ['username', 'nom_completo', 'cedula', 'telefono', 'email', 
                  'id_tipo_usuario', 'id_titulo']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si es un nuevo usuario, hacer la contraseña obligatoria
        if not self.instance.pk:
            self.fields['password_input'].required = True
            self.fields['password_confirm'].required = True
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password_input')
        password_confirm = cleaned_data.get('password_confirm')
        
        # Validar que las contraseñas coincidan
        if password or password_confirm:
            if password != password_confirm:
                raise forms.ValidationError('Las contraseñas no coinciden.')
            
            # Validar longitud mínima
            if len(password) < 4:
                raise forms.ValidationError('La contraseña debe tener al menos 4 caracteres.')
        
        return cleaned_data
    
    def save(self, commit=True):
        usuario = super().save(commit=False)
        
        # Si se ingresó una contraseña, encriptarla
        password = self.cleaned_data.get('password_input')
        if password:
            usuario.set_password(password)
        
        if commit:
            usuario.save()
        
        return usuario