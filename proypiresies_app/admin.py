# <your_app_name>/admin.py
from django.contrib import admin
from .models import (
    Eidikotita, Ekpaideftikos, Ypiresia, PYSEEP,
    EidosProypiresias, SxesiErgasias, Aitisi, Proypiresia,
    ProypiresiaPyseepHistory
)
from django.utils import timezone # Για το timestamp

# Inline για τις Προϋπηρεσίες μέσα στη φόρμα της Αίτησης
class ProypiresiaInline(admin.TabularInline): # ή StackedInline για διαφορετική εμφάνιση
    model = Proypiresia
    extra = 1 # Πόσες κενές φόρμες προϋπηρεσίας θα εμφανίζονται αρχικά
    fields = (
        'eidos_proypiresias', #'eidos_proypiresias_allo', (αν είχαμε το πεδίο για ελεύθερη εισαγωγή)
        'arithmos_protokollou_vevaiosis',
        'sxesi_ergasias', #'sxesi_ergasias_allo', (αν είχαμε το πεδίο για ελεύθερη εισαγωγή)
        'xroniko_diastima_apo', 'xroniko_diastima_eos',
        'eti_proypiresias', 'mines_proypiresias', 'meres_proypiresias',
        'paratiriseis', 'esoterikes_simeioseis',
        'elegxthike', 'elegxthike_pote', 'elegxthike_apo', 'paravlepsi'
    )
    readonly_fields = ('elegxthike_pote', 'elegxthike_apo')
    # Για την αυτόματη συμπλήρωση των 'eti_proypiresias', 'mines_proypiresias', 'meres_proypiresias'
    # θα χρειαζόταν JavaScript ή ένα custom formset.

    # Αν θέλατε να επιτρέπεται η εισαγωγή νέου "Είδους Προϋπηρεσίας" απευθείας από εδώ:
    # formfield_overrides = {
    #     models.ForeignKey: {'widget': RelatedFieldWidgetWrapper(
    #                                 admin.site.widgets.ForeignKeyRawIdWidget,
    #                                 EidosProypiresias._meta.get_field('eidos_proypiresias').remote_field,
    #                                 admin.site, can_add_related=True, can_change_related=False, can_delete_related=False
    #                             )
    #                       },
    # }
    # Αυτό είναι πιο περίπλοκο και συνήθως προτιμάται η διαχείριση των "Ειδών Προϋπηρεσίας" από τη δική τους σελίδα στο admin.


# Inline για το Ιστορικό ΠΥΣΕΕΠ μέσα στη φόρμα της Προϋπηρεσίας
class ProypiresiaPyseepHistoryInline(admin.TabularInline):
    model = ProypiresiaPyseepHistory
    extra = 0
    fields = ('pyseep_apofasis', 'imerominia_egkrisis_apo_pyseep')
    readonly_fields = ('imerominia_egkrisis_apo_pyseep',) # Αυτό θα μπορούσε να συμπληρωθεί αυτόματα ή να είναι επεξεργάσιμο
    can_delete = False # Συνήθως δεν θέλουμε να διαγράφεται το ιστορικό εύκολα

@admin.register(Aitisi)
class AitisiAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'ekpaideftikos', 'sxoliko_etos', 'ypiresia_trexousas_topothetisis',
        'typos_ekpaideftikou', 'imerominia_ypovolis', 'se_anamoni',
        'pyseep_proothisis', 'pyseep_teliki_apofasi', 'created_at'
    )
    list_filter = (
        'sxoliko_etos', 'typos_ekpaideftikou', 'se_anamoni',
        'pyseep_proothisis__arithmos_praxis', 'pyseep_teliki_apofasi__arithmos_praxis', # Φιλτράρισμα βάσει αριθμού πράξης
        'ypiresia_trexousas_topothetisis'
    )
    search_fields = (
        'ekpaideftikos__eponymo', 'ekpaideftikos__onoma', 'id'
    )
    autocomplete_fields = ['ekpaideftikos', 'ypiresia_trexousas_topothetisis', 'pyseep_proothisis', 'pyseep_teliki_apofasi']
    inlines = [ProypiresiaInline]
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('ekpaideftikos', 'ypiresia_trexousas_topothetisis', 'sxoliko_etos',
                       'typos_ekpaideftikou', 'imerominia_ypovolis', 'arxeio_aitisis_pdf')
        }),
        ('Κατάσταση Αίτησης', {
            'classes': ('collapse',), # Κλειστό από προεπιλογή
            'fields': ('se_anamoni', 'pyseep_proothisis', 'pyseep_teliki_apofasi'),
        }),
        ('Πληροφορίες Συστήματος', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at'),
        }),
    )

    def save_model(self, request, obj, form, change):
        # Αυτόματη εκκαθάριση του αντίθετου πεδίου κατάστασης
        if 'se_anamoni' in form.changed_data and obj.se_anamoni:
            obj.pyseep_proothisis = None
        if 'pyseep_proothisis' in form.changed_data and obj.pyseep_proothisis:
            obj.se_anamoni = False
        super().save_model(request, obj, form, change)

        # Λογική για δημιουργία/ενημέρωση ProypiresiaPyseepHistory
        # Όταν μια αίτηση παίρνει pyseep_teliki_apofasi ή αλλάζει το pyseep_teliki_apofasi
        if obj.pyseep_teliki_apofasi and ('pyseep_teliki_apofasi' in form.changed_data or not change): # Επίσης κατά τη δημιουργία αν υπάρχει ήδη
            for proypiresia_obj in obj.proypiresies.all():
                if not proypiresia_obj.paravlepsi: # Μόνο για αυτές που δεν παραβλέπονται
                    history_entry, created = ProypiresiaPyseepHistory.objects.update_or_create(
                        proypiresia=proypiresia_obj,
                        pyseep_apofasis=obj.pyseep_teliki_apofasi,
                        defaults={
                            'imerominia_egkrisis_apo_pyseep': obj.pyseep_teliki_apofasi.imerominia_praxis
                            # Εδώ θα μπορούσατε να προσθέσετε και άλλα πεδία αν το μοντέλο ProypiresiaPyseepHistory τα έχει
                        }
                    )
                    if created:
                        print(f"Created history for proypiresia {proypiresia_obj.id} with PYSEEP {obj.pyseep_teliki_apofasi}")
                    else:
                        print(f"Updated history for proypiresia {proypiresia_obj.id} with PYSEEP {obj.pyseep_teliki_apofasi}")


@admin.register(Proypiresia)
class ProypiresiaAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'aitisi_link', 'eidos_proypiresias', 'xroniko_diastima_apo', 'xroniko_diastima_eos',
        'eti_proypiresias', 'mines_proypiresias', 'meres_proypiresias',
        'elegxthike', 'elegxthike_apo_user', 'elegxthike_pote_formatted', 'paravlepsi'
    )
    list_filter = ('elegxthike', 'paravlepsi', 'eidos_proypiresias', 'sxesi_ergasias', 'aitisi__sxoliko_etos')
    search_fields = ('aitisi__ekpaideftikos__eponymo', 'aitisi__ekpaideftikos__onoma', 'arithmos_protokollou_vevaiosis')
    autocomplete_fields = ['aitisi', 'eidos_proypiresias', 'sxesi_ergasias'] #, 'elegxthike_apo'] # Το elegxthike_apo το χειριζόμαστε διαφορετικά
    readonly_fields = ('elegxthike_pote', 'elegxthike_apo') # Αυτά συμπληρώνονται από τη λογική
    inlines = [ProypiresiaPyseepHistoryInline] # Για να βλέπουμε το ιστορικό της συγκεκριμένης προϋπηρεσίας

    fieldsets = (
        (None, {
            'fields': ('aitisi', 'eidos_proypiresias', 'arithmos_protokollou_vevaiosis', 'sxesi_ergasias')
        }),
        ('Χρονικό Διάστημα & Διάρκεια', {
            'fields': (('xroniko_diastima_apo', 'xroniko_diastima_eos'),
                       ('eti_proypiresias', 'mines_proypiresias', 'meres_proypiresias'))
        }),
        ('Σημειώσεις', {
            'fields': ('paratiriseis', 'esoterikes_simeioseis')
        }),
        ('Έλεγχος & Κατάσταση', {
            'fields': ('elegxthike', 'elegxthike_pote', 'elegxthike_apo', 'paravlepsi')
        }),
    )

    def aitisi_link(self, obj):
        from django.utils.html import format_html
        from django.urls import reverse
        link = reverse("admin:your_app_name_aitisi_change", args=[obj.aitisi.id]) # Αντικαταστήστε your_app_name
        return format_html('<a href="{}">{}</a>', link, obj.aitisi)
    aitisi_link.short_description = 'Αίτηση'

    def elegxthike_apo_user(self, obj):
        return obj.elegxthike_apo.username if obj.elegxthike_apo else "-"
    elegxthike_apo_user.short_description = 'Ελέγχθηκε από'

    def elegxthike_pote_formatted(self, obj):
        return obj.elegxthike_pote.strftime("%d/%m/%Y %H:%M") if obj.elegxthike_pote else "-"
    elegxthike_pote_formatted.short_description = 'Ελέγχθηκε στις'


    def save_model(self, request, obj, form, change):
        # Αν το "Ελέγχθηκε" τσεκαρίστηκε τώρα ή ήταν ήδη τσεκαρισμένο και αλλάζει κάτι άλλο
        if obj.elegxthike:
            if not obj.elegxthike_pote: # Αν δεν έχει timestamp, βάλε τώρα
                obj.elegxthike_pote = timezone.now()
            if not obj.elegxthike_apo: # Αν δεν έχει χρήστη, βάλε τον τρέχοντα
                obj.elegxthike_apo = request.user
        elif not obj.elegxthike and ('elegxthike' in form.changed_data or obj.elegxthike_pote or obj.elegxthike_apo):
            # Αν ξε-τσεκαρίστηκε ή ήταν ξετσεκαρισμένο αλλά είχαν μείνει τιμές
            obj.elegxthike_pote = None
            obj.elegxthike_apo = None
        super().save_model(request, obj, form, change)


@admin.register(Ekpaideftikos)
class EkpaideftikosAdmin(admin.ModelAdmin):
    list_display = ('eponymo', 'onoma', 'patronymo', 'eidikotita_sintomi', 'email', 'tilefono')
    search_fields = ('eponymo', 'onoma', 'patronymo', 'email', 'eidikotita__eidikotita_sintomi', 'eidikotita__eidikotita_pliris')
    list_filter = ('eidikotita',)
    autocomplete_fields = ['eidikotita']

    def eidikotita_sintomi(self, obj):
        return obj.eidikotita.eidikotita_sintomi
    eidikotita_sintomi.short_description = 'Ειδικότητα (Σύντμηση)'
    eidikotita_sintomi.admin_order_field = 'eidikotita__eidikotita_sintomi'


@admin.register(Eidikotita)
class EidikotitaAdmin(admin.ModelAdmin):
    list_display = ('eidikotita_sintomi', 'eidikotita_pliris')
    search_fields = ('eidikotita_sintomi', 'eidikotita_pliris')
    ordering = ('eidikotita_sintomi',)

@admin.register(PYSEEP)
class PYSEEPAdmin(admin.ModelAdmin):
    list_display = ('arithmos_praxis', 'imerominia_praxis_formatted')
    search_fields = ('arithmos_praxis',)
    date_hierarchy = 'imerominia_praxis'
    ordering = ('-imerominia_praxis', 'arithmos_praxis')

    def imerominia_praxis_formatted(self, obj):
        return obj.imerominia_praxis.strftime("%d/%m/%Y")
    imerominia_praxis_formatted.short_description = 'Ημερομηνία Πράξης'
    imerominia_praxis_formatted.admin_order_field = 'imerominia_praxis'

@admin.register(Ypiresia)
class YpiresiaAdmin(admin.ModelAdmin):
    search_fields = ('onomasia',)
    ordering = ('onomasia',)

@admin.register(EidosProypiresias)
class EidosProypiresiasAdmin(admin.ModelAdmin):
    search_fields = ('perigrafi',)
    ordering = ('perigrafi',)

@admin.register(SxesiErgasias)
class SxesiErgasiasAdmin(admin.ModelAdmin):
    search_fields = ('perigrafi',)
    ordering = ('perigrafi',)

@admin.register(ProypiresiaPyseepHistory)
class ProypiresiaPyseepHistoryAdmin(admin.ModelAdmin):
    list_display = ('proypiresia', 'pyseep_apofasis', 'imerominia_egkrisis_apo_pyseep_formatted')
    autocomplete_fields = ['proypiresia', 'pyseep_apofasis']
    readonly_fields = ('imerominia_egkrisis_apo_pyseep',) # Δεδομένου ότι συμπληρώνεται αυτόματα

    def imerominia_egkrisis_apo_pyseep_formatted(self, obj):
        return obj.imerominia_egkrisis_apo_pyseep.strftime("%d/%m/%Y")
    imerominia_egkrisis_apo_pyseep_formatted.short_description = 'Ημ/νία Έγκρισης'
    imerominia_egkrisis_apo_pyseep_formatted.admin_order_field = 'imerominia_egkrisis_apo_pyseep'