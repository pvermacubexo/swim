from django import forms
from Appointment.models import ClassInstructor
from user import models as user_model
from django.forms import modelformset_factory


class ClassCreateForm(forms.ModelForm):
    class Meta:
        model = ClassInstructor
        fields = '__all__'
        # fields = ['title', 'time_slot', 'total_days', 'description', 'price', 'thumbnail_image', 'instructor']


class ProfileImageForm(forms.Form):
    profile_img = forms.ImageField()


monday, tuesday, wednesday, thursday, friday, saturday, sunday = '1', '2', '3', '4', '5', '6', '7'


class BreakTimeForm(forms.ModelForm):
    instructor = forms.ModelChoiceField(
        queryset=user_model.Profile.objects.all(), widget=(forms.Select(attrs={
            'class': 'break_time_profile display_none',
            'type': 'text'
        })))

    class Meta:
        model = user_model.BreakTime
        fields = '__all__'
        week_name = (
            (monday, 'monday'),
            (tuesday, 'tuesday'),
            (wednesday, 'wednesday'),
            (thursday, 'thursday'),
            (friday, 'friday'),
            (saturday, 'saturday'),
            (sunday, 'sunday'),
        )
        widgets = {
            'week_day': forms.Select(choices=week_name, attrs={'class': 'form-control'}),
            'start_time': forms.TextInput(attrs={'class': 'form-control timepicker', 'placeholder': 'Start Time'}),
            'end_time': forms.TextInput(attrs={'class': 'form-control timepicker',  'placeholder': 'End Time'}),
        }


BreakTimeFormSet = modelformset_factory(user_model.BreakTime, form=BreakTimeForm, extra=1)
