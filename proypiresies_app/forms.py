# <your_app_name>/forms.py
from django import forms
from .models import Aitisi, Proypiresia, Ekpaideftikos, EidosProypiresias, SxesiErgasias, Ypiresia
from django.forms.widgets import DateInput

class DatePickerInput(DateInput):
    input_type = 'date' # Χρησιμοποιεί το native date picker του browser

class ProypiresiaForm(forms.ModelForm):
    # Για να επιτρέψετε την εισαγωγή νέου Είδους Προϋπηρεσίας αν δεν υπάρχει:
    # eidos_proypiresias_new = forms.CharField(label="Νέο Είδος Προϋπηρεσίας (αν δεν υπάρχει στη λίστα)", required=False)
    # Για να επιτρέψετε την εισαγωγή νέας Σχέσης Εργασίας αν δεν υπάρχει:
    # sxesi_ergasias_new = forms.CharField(label="Νέα Σχέση Εργασίας (αν δεν υπάρχει στη λίστα)", required=False)

    class Meta:
        model = Proypiresia
        fields = [
            'eidos_proypiresias', #'eidos_proypiresias_new',
            'arithmos_protokollou_vevaiosis',
            'sxesi_ergasias', #'sxesi_ergasias_new',
            'xroniko_diastima_apo', 'xroniko_diastima_eos',
            'eti_proypiresias', 'mines_proypiresias', 'meres_proypiresias',
            'paratiriseis', 'esoterikes_simeioseis',
            'elegxthike', # Το elegxthike_apo και elegxthike_pote θα χειριστούν στις views/models
            'paravlepsi'
        ]
        widgets = {
            'xroniko_diastima_apo': DatePickerInput(),
            'xroniko_diastima_eos': DatePickerInput(),
            'paratiriseis': forms.Textarea(attrs={'rows': 3}),
            'esoterikes_simeioseis': forms.Textarea(attrs={'rows': 3}),
        }
        # Μπορείτε να προσαρμόσετε τα labels εδώ αν χρειάζεται
        labels = {
            'eidos_proypiresias': 'Είδος Προϋπηρεσίας',
            # ... άλλα labels
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['eidos_proypiresias'].queryset = EidosProypiresias.objects.all().order_by('perigrafi')
        self.fields['sxesi_ergasias'].queryset = SxesiErgasias.objects.all().order_by('perigrafi')
        # Αν είχατε τα _new πεδία:
        # self.fields['eidos_proypiresias'].required = False
        # self.fields['sxesi_ergasias'].required = False


    # def clean(self):
    #     cleaned_data = super().clean()
    #     eidos = cleaned_data.get('eidos_proypiresias')
    #     eidos_new = cleaned_data.get('eidos_proypiresias_new')
    #     # Παρόμοια λογική για sxesi_ergasias
    #
    #     if not eidos and not eidos_new:
    #         self.add_error('eidos_proypiresias', 'Πρέπει να επιλέξετε ή να εισάγετε νέο είδος προϋπηρεσίας.')
    #     elif eidos_new:
    #         # Εδώ θα μπορούσατε να δημιουργήσετε το νέο EidosProypiresias αν δεν υπάρχει ήδη
    #         # και να το αντιστοιχίσετε στο cleaned_data['eidos_proypiresias']
    #         pass
    #     return cleaned_data


# Formset για τις προϋπηρεσίες
ProypiresiaFormSet = forms.inlineformset_factory(
    Aitisi, Proypiresia, form=ProypiresiaForm,
    fields=[
        'eidos_proypiresias', 'arithmos_protokollou_vevaiosis', 'sxesi_ergasias',
        'xroniko_diastima_apo', 'xroniko_diastima_eos',
        'eti_proypiresias', 'mines_proypiresias', 'meres_proypiresias',
        'paratiriseis', 'esoterikes_simeioseis', 'paravlepsi', 'elegxthike'
    ],
    extra=1, # Αριθμός κενών φορμών
    can_delete=True # Να επιτρέπεται η διαγραφή
)


class AitisiForm(forms.ModelForm):
    class Meta:
        model = Aitisi
        fields = [
            'ekpaideftikos', 'ypiresia_trexousas_topothetisis', 'sxoliko_etos',
            'typos_ekpaideftikou', 'imerominia_ypovolis', 'arxeio_aitisis_pdf',
            'se_anamoni', 'pyseep_proothisis' # Το pyseep_teliki_apofasi συνήθως ορίζεται σε ξεχωριστό βήμα
        ]
        widgets = {
            'imerominia_ypovolis': DatePickerInput(),
        }
        labels = {
            'se_anamoni': 'Αίτηση σε αναμονή δικαιολογητικών',
            'pyseep_proothisis': 'Έτοιμη για ΠΥΣΕΕΠ (Προώθηση)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ekpaideftikos'].queryset = Ekpaideftikos.objects.all().order_by('eponymo', 'onoma')
        self.fields['ekpaideftikos'].label_from_instance = lambda obj: f"{obj.eponymo} {obj.onoma} ({obj.patronymo})"
        self.fields['ypiresia_trexousas_topothetisis'].queryset = Ypiresia.objects.all().order_by('onomasia')
        if self.instance and self.instance.pk: # Αν επεξεργαζόμαστε υπάρχουσα αίτηση
             # Αποτρέπουμε την αλλαγή του εκπαιδευτικού μετά τη δημιουργία της αίτησης
            self.fields['ekpaideftikos'].disabled = True


    def clean(self):
        cleaned_data = super().clean()
        se_anamoni = cleaned_data.get("se_anamoni")
        pyseep_proothisis = cleaned_data.get("pyseep_proothisis")

        if se_anamoni and pyseep_proothisis:
            raise forms.ValidationError(
                "Μια αίτηση δεν μπορεί να είναι ταυτόχρονα 'Σε Αναμονή' και 'Έτοιμη για ΠΥΣΕΕΠ'.",
                code='invalid_status_combination'
            )
        return cleaned_data