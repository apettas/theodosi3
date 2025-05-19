# proypiresies_app/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, UpdateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required # <--- ΠΡΟΣΘΕΣΤΕ ΑΥΤΗ ΤΗ ΓΡΑΜΜΗ
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction, models # Προσθέστε το models εδώ αν το χρησιμοποιείτε για το Q object
from django.http import HttpResponse, JsonResponse
from django.utils import timezone # Είχαμε προσθέσει το timezone
from .models import Aitisi, Proypiresia, Ekpaideftikos, PYSEEP, ProypiresiaPyseepHistory # Προσθέστε το ProypiresiaPyseepHistory
from .forms import AitisiForm, ProypiresiaFormSet
from django.db import transaction, models # Βεβαιωθείτε ότι το models είναι εδώ
from .models import Aitisi, Proypiresia, Ekpaideftikos, PYSEEP, ProypiresiaPyseepHistory


# -- Παράδειγμα για Αιτήσεις --
class AitisiListView(LoginRequiredMixin, ListView):
    model = Aitisi
    template_name = 'proypiresies_app/aitisi_list.html' # Δημιουργήστε αυτό το template
    context_object_name = 'aitiseis'
    paginate_by = 20

class AitisiDetailView(LoginRequiredMixin, DetailView):
    model = Aitisi
    template_name = 'proypiresies_app/aitisi_detail.html' # Δημιουργήστε αυτό το template
    context_object_name = 'aitisi'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['proypiresies'] = self.object.proypiresies.filter(paravlepsi=False).order_by('xroniko_diastima_apo')
        # Ιστορικό προϋπηρεσιών για αυτή την αίτηση
        proypiresia_ids = self.object.proypiresies.values_list('id', flat=True)
        history = ProypiresiaPyseepHistory.objects.filter(proypiresia_id__in=proypiresia_ids).select_related('pyseep_apofasis').order_by('proypiresia_id', '-imerominia_egkrisis_apo_pyseep')
        context['proypiresia_history'] = {
            proy_id: [h for h in history if h.proypiresia_id == proy_id]
            for proy_id in proypiresia_ids
        }
        return context

class AitisiCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Aitisi
    form_class = AitisiForm
    template_name = 'proypiresies_app/aitisi_form.html'
    success_message = "Η αίτηση δημιουργήθηκε με επιτυχία!"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['proypiresies_formset'] = ProypiresiaFormSet(self.request.POST, self.request.FILES, prefix='proypiresies')
        else:
            # Λογική για φόρτωση προηγούμενων προϋπηρεσιών
            ekpaideftikos_id = self.request.GET.get('ekpaideftikos_id')
            initial_proypiresies = []
            if ekpaideftikos_id:
                try:
                    ekpaideftikos = Ekpaideftikos.objects.get(pk=ekpaideftikos_id)
                    # Βρίσκουμε την τελευταία αίτηση του εκπαιδευτικού (αν υπάρχει)
                    last_aitisi = Aitisi.objects.filter(ekpaideftikos=ekpaideftikos).order_by('-created_at').first()
                    if last_aitisi:
                        for proy in last_aitisi.proypiresies.all():
                            initial_proypiresies.append({
                                'eidos_proypiresias': proy.eidos_proypiresias,
                                'arithmos_protokollou_vevaiosis': proy.arithmos_protokollou_vevaiosis,
                                'sxesi_ergasias': proy.sxesi_ergasias,
                                'xroniko_diastima_apo': proy.xroniko_diastima_apo,
                                'xroniko_diastima_eos': proy.xroniko_diastima_eos,
                                'eti_proypiresias': proy.eti_proypiresias,
                                'mines_proypiresias': proy.mines_proypiresias,
                                'meres_proypiresias': proy.meres_proypiresias,
                                'paratiriseis': proy.paratiriseis,
                                # Δεν φορτώνουμε τις εσωτερικές σημειώσεις ή την κατάσταση ελέγχου σε νέα αίτηση
                            })
                except Ekpaideftikos.DoesNotExist:
                    pass
            data['proypiresies_formset'] = ProypiresiaFormSet(prefix='proypiresies', initial=initial_proypiresies)
        data['form_title'] = "Δημιουργία Νέας Αίτησης"
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        proypiresies_formset = context['proypiresies_formset']
        with transaction.atomic():
            self.object = form.save() # Αποθηκεύουμε την Αίτηση πρώτα
            if proypiresies_formset.is_valid():
                proypiresies_formset.instance = self.object # Συνδέουμε το formset με την Αίτηση
                proypiresies = proypiresies_formset.save(commit=False)
                for proy in proypiresies:
                    # Εδώ θα μπορούσε να μπει λογική για αυτόματο υπολογισμό ετών/μηνών/ημερών
                    # από τις ημερομηνίες ΑΠΟ-ΕΩΣ αν δεν έχουν συμπληρωθεί.
                    proy.save()
            else:
                # Αν το formset δεν είναι valid, ακυρώνουμε την αποθήκευση της αίτησης
                # επιστρέφοντας το form με τα λάθη.
                return self.form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('proypiresies_app:aitisi_detail', kwargs={'pk': self.object.pk})


class AitisiUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Aitisi
    form_class = AitisiForm
    template_name = 'proypiresies_app/aitisi_form.html'
    success_message = "Οι αλλαγές στην αίτηση αποθηκεύτηκαν με επιτυχία!"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['proypiresies_formset'] = ProypiresiaFormSet(self.request.POST, self.request.FILES, instance=self.object, prefix='proypiresies')
        else:
            data['proypiresies_formset'] = ProypiresiaFormSet(instance=self.object, prefix='proypiresies')
        data['form_title'] = f"Επεξεργασία Αίτησης: {self.object}"
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        proypiresies_formset = context['proypiresies_formset']
        with transaction.atomic():
            self.object = form.save()
            if proypiresies_formset.is_valid():
                proypiresies_formset.save() # Το instance έχει ήδη οριστεί
                # Λογική για το 'Ελέγχθηκε' στις προϋπηρεσίες
                for proy_form in proypiresies_formset:
                    if proy_form.cleaned_data.get('elegxthike') and not proy_form.instance.elegxthike_apo:
                        proy_form.instance.elegxthike_apo = self.request.user
                        # το elegxthike_pote θα μπει από το model.save()
                        proy_form.instance.save()
                    elif not proy_form.cleaned_data.get('elegxthike') and proy_form.instance.elegxthike_apo:
                        proy_form.instance.elegxthike_apo = None
                        proy_form.instance.elegxthike_pote = None
                        proy_form.instance.save()

            else:
                return self.form_invalid(form) # Επιστρέφει τη φόρμα με τα λάθη του formset
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('proypiresies_app:aitisi_detail', kwargs={'pk': self.object.pk})

# View για την τελική έγκριση από ΠΥΣΕΕΠ (παράδειγμα)
@login_required # Χρησιμοποιούμε function-based view για απλότητα εδώ
def aitisi_teliki_egkrisi_pyseep(request, pk):
    aitisi = get_object_or_404(Aitisi, pk=pk)
    if request.method == 'POST':
        pyseep_id = request.POST.get('pyseep_teliki_apofasi_id')
        if pyseep_id:
            pyseep_apofasi = get_object_or_404(PYSEEP, pk=pyseep_id)
            if aitisi.pyseep_proothisis and pyseep_apofasi.imerominia_praxis < aitisi.pyseep_proothisis.imerominia_praxis:
                # error message
                pass # Προσθέστε μήνυμα λάθους
            else:
                aitisi.pyseep_teliki_apofasi = pyseep_apofasi
                aitisi.save() # Το save του μοντέλου θα καλέσει και το clean() για έλεγχο.
                             # Και το save_model του admin (αν το είχαμε εδώ) θα έφτιαχνε το history.
                             # Εδώ πρέπει να το κάνουμε χειροκίνητα.
                for proy in aitisi.proypiresies.filter(paravlepsi=False):
                    ProypiresiaPyseepHistory.objects.update_or_create(
                        proypiresia=proy,
                        pyseep_apofasis=pyseep_apofasi,
                        defaults={'imerominia_egkrisis_apo_pyseep': pyseep_apofasi.imerominia_praxis}
                    )
                # success message
                return redirect('proypiresies_app:aitisi_detail', pk=aitisi.pk)
    pass






@login_required
def generate_pyseep_report_xlsx(request, pyseep_id):
    pyseep_instance = get_object_or_404(PYSEEP, pk=pyseep_id)
    # Αιτήσεις που έχουν προωθηθεί ή έχουν τελική απόφαση από αυτό το ΠΥΣΕΕΠ
    aitiseis = Aitisi.objects.filter(
        Q(pyseep_proothisis=pyseep_instance) | Q(pyseep_teliki_apofasi=pyseep_instance)
    ).select_related(
        'ekpaideftikos', 'ekpaideftikos__eidikotita', 'ypiresia_trexousas_topothetisis'
    ).prefetch_related(
        'proypiresies', 'proypiresies__eidos_proypiresias', 'proypiresies__sxesi_ergasias'
    ).order_by('ypiresia_trexousas_topothetisis__onomasia', 'ekpaideftikos__eponymo', 'ekpaideftikos__onoma')

    wb = Workbook()
    ws = wb.active
    ws.title = f"ΠΥΣΕΕΠ {pyseep_instance.arithmos_praxis}"

    # Headers
    headers = [
        "Α/Α", "Υπηρεσία Τοποθέτησης", "Επώνυμο", "Όνομα", "Πατρώνυμο", "Ειδικότητα",
        "Σχ. Έτος Αίτησης", "Είδος Προϋπ.", "Αρ. Πρωτ.", "Σχέση Εργ.",
        "Από", "Έως", "Έτη", "Μήνες", "Μέρες", "Παρατηρήσεις Αιτ.", "Ελέγχθηκε", "Παράβλεψη"
    ]
    ws.append(headers)

    row_num_display = 0 # Για τον εμφανιζόμενο Α/Α
    for aitisi in aitiseis:
        # Φιλτράρισμα προϋπηρεσιών που δεν έχουν παραβλεφθεί
        relevant_proypiresies = [p for p in aitisi.proypiresies.all() if not p.paravlepsi]
        if not relevant_proypiresies: # Αν δεν υπάρχουν σχετικές προϋπηρεσίες, πήγαινε στην επόμενη αίτηση
            continue

        for proy in relevant_proypiresies:
            row_num_display += 1
            row_data = [
                row_num_display, # Α/Α
                aitisi.ypiresia_trexousas_topothetisis.onomasia,
                aitisi.ekpaideftikos.eponymo,
                aitisi.ekpaideftikos.onoma,
                aitisi.ekpaideftikos.patronymo,
                aitisi.ekpaideftikos.eidikotita.eidikotita_sintomi,
                aitisi.sxoliko_etos,
                proy.eidos_proypiresias.perigrafi,
                proy.arithmos_protokollou_vevaiosis,
                proy.sxesi_ergasias.perigrafi,
                proy.xroniko_diastima_apo.strftime("%d/%m/%Y") if proy.xroniko_diastima_apo else "",
                proy.xroniko_diastima_eos.strftime("%d/%m/%Y") if proy.xroniko_diastima_eos else "",
                proy.eti_proypiresias,
                proy.mines_proypiresias,
                proy.meres_proypiresias,
                proy.paratiriseis,
                "ΝΑΙ" if proy.elegxthike else "ΟΧΙ",
                "ΝΑΙ" if proy.paravlepsi else "ΟΧΙ"
            ]
            ws.append(row_data)

    response = HttpResponse(
        save_virtual_workbook(wb),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="report_pyseep_{pyseep_instance.arithmos_praxis.replace("/", "-")}.xlsx"'
    return response





@login_required
def generate_pyseep_report_pdf(request, pyseep_id):
    pyseep_instance = get_object_or_404(PYSEEP, pk=pyseep_id)
    aitiseis = Aitisi.objects.filter(
        Q(pyseep_proothisis=pyseep_instance) | Q(pyseep_teliki_apofasi=pyseep_instance)
    ).select_related(
        'ekpaideftikos', 'ekpaideftikos__eidikotita', 'ypiresia_trexousas_topothetisis'
    ).prefetch_related(
        'proypiresies', 'proypiresies__eidos_proypiresias', 'proypiresies__sxesi_ergasias'
    ).order_by('ypiresia_trexousas_topothetisis__onomasia', 'ekpaideftikos__eponymo', 'ekpaideftikos__onoma')

    context = {
        'pyseep_instance': pyseep_instance,
        'aitiseis': aitiseis,
        'current_date': timezone.now().date(), # Χρησιμοποιούμε timezone.now().date()
        'relevant_proypiresies_for_aitisi': {} # Λεξικό για τις σχετικές προϋπηρεσίες
    }

    for aitisi in aitiseis:
        # Φιλτράρισμα προϋπηρεσιών που δεν έχουν παραβλεφθεί για κάθε αίτηση
        relevant_proypiresies = [p for p in aitisi.proypiresies.all() if not p.paravlepsi]
        if relevant_proypiresies: # Μόνο αν υπάρχουν σχετικές προϋπηρεσίες
             context['relevant_proypiresies_for_aitisi'][aitisi.id] = relevant_proypiresies


    html_string = render_to_string('proypiresies_app/report_pyseep_pdf_template.html', context)

    # --- Λογική για WeasyPrint (ΠΡΟΣΟΧΗ: Χρειάζεται εγκατάσταση του WeasyPrint και των εξαρτήσεών του) ---
    # from weasyprint import HTML # Αποσχολιάστε αν έχετε εγκαταστήσει το WeasyPrint
    # response = HttpResponse(content_type='application/pdf')
    # response['Content-Disposition'] = f'attachment; filename="report_pyseep_{pyseep_instance.arithmos_praxis.replace("/", "-")}.pdf"'
    # HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(response)
    # return response
    # ----------------------------------------------------------------------------------------------------

    # Προσωρινός Placeholder αν δεν έχετε το WeasyPrint έτοιμο:
    return HttpResponse(f"PDF generation for PYSEEP {pyseep_id} would happen here. HTML content: <pre>{html_string}</pre>")




from django.shortcuts import render

def home_view(request):
    return render(request, 'proypiresies_app/home.html') # Ή όπως ονομάσετε το template σας



    # Στο template θα έχουμε ένα dropdown για επιλογή ΠΥΣΕΕΠ
    pyseep_options = PYSEEP.objects.all().order_by('-imerominia_praxis')
    return render(request, 'proypiresies_app/aitisi_teliki_egkrisi_form.html', {'aitisi': aitisi, 'pyseep_options': pyseep_options})