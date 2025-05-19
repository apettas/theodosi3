# <your_app_name>/models.py
from django.db import models
from django.contrib.auth.models import User # Για τον χρήστη που κάνει έλεγχο
from django.core.exceptions import ValidationError
from django.utils import timezone

class Eidikotita(models.Model):
    eidikotita_pliris = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Πλήρης Ονομασία Ειδικότητας"
    )
    eidikotita_sintomi = models.CharField(
        max_length=50,
        verbose_name="Σύντομη Ονομασία Ειδικότητας (π.χ. ΔΕ1)"
    )

    def __str__(self):
        return self.eidikotita_pliris

    class Meta:
        verbose_name = "Ειδικότητα"
        verbose_name_plural = "Ειδικότητες"
        ordering = ['eidikotita_sintomi']


class Ekpaideftikos(models.Model):
    onoma = models.CharField(max_length=100, verbose_name="Όνομα")
    eponymo = models.CharField(max_length=100, verbose_name="Επώνυμο")
    patronymo = models.CharField(max_length=100, verbose_name="Πατρώνυμο")
    eidikotita = models.ForeignKey(
        Eidikotita,
        on_delete=models.PROTECT, # Προστασία για να μην διαγραφεί ειδικότητα αν χρησιμοποιείται
        verbose_name="Ειδικότητα"
    )
    tilefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Τηλέφωνο")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")

    def __str__(self):
        return f"{self.eponymo} {self.onoma} ({self.eidikotita.eidikotita_sintomi})"

    class Meta:
        verbose_name = "Εκπαιδευτικός"
        verbose_name_plural = "Εκπαιδευτικοί"
        unique_together = [['onoma', 'eponymo', 'patronymo', 'eidikotita']]
        ordering = ['eponymo', 'onoma']


class Ypiresia(models.Model):
    onomasia = models.CharField(max_length=255, unique=True, verbose_name="Ονομασία Υπηρεσίας")

    def __str__(self):
        return self.onomasia

    class Meta:
        verbose_name = "Υπηρεσία Τοποθέτησης/Υπηρέτησης"
        verbose_name_plural = "Υπηρεσίες Τοποθέτησης/Υπηρέτησης"
        ordering = ['onomasia']


class PYSEEP(models.Model):
    arithmos_praxis = models.CharField(max_length=50, verbose_name="Αριθμός Πράξης ΠΥΣΕΕΠ")
    imerominia_praxis = models.DateField(verbose_name="Ημερομηνία Πράξης ΠΥΣΕΕΠ")

    def __str__(self):
        return f"Πράξη {self.arithmos_praxis}/{self.imerominia_praxis.strftime('%d-%m-%Y')}"

    class Meta:
        verbose_name = "Πράξη ΠΥΣΕΕΠ"
        verbose_name_plural = "Πράξεις ΠΥΣΕΕΠ"
        unique_together = [['arithmos_praxis', 'imerominia_praxis']]
        ordering = ['-imerominia_praxis', 'arithmos_praxis']


class EidosProypiresias(models.Model):
    perigrafi = models.CharField(max_length=255, unique=True, verbose_name="Περιγραφή Είδους Προϋπηρεσίας")

    def __str__(self):
        return self.perigrafi

    class Meta:
        verbose_name = "Είδος Προϋπηρεσίας"
        verbose_name_plural = "Είδη Προϋπηρεσιών"
        ordering = ['perigrafi']


class SxesiErgasias(models.Model):
    perigrafi = models.CharField(max_length=100, unique=True, verbose_name="Περιγραφή Σχέσης Εργασίας")

    def __str__(self):
        return self.perigrafi

    class Meta:
        verbose_name = "Σχέση Εργασίας"
        verbose_name_plural = "Σχέσεις Εργασίας"
        ordering = ['perigrafi']


class Aitisi(models.Model):
    TYPOI_EKPAIDEFTIKOU_CHOICES = [
        ('MONIMOS', 'Μόνιμος'),
        ('ANAPLIROTIS', 'Αναπληρωτής'),
    ]

    ekpaideftikos = models.ForeignKey(
        Ekpaideftikos,
        on_delete=models.CASCADE, # Αν διαγραφεί ο εκπαιδευτικός, διαγράφονται και οι αιτήσεις του
        verbose_name="Εκπαιδευτικός"
    )
    ypiresia_trexousas_topothetisis = models.ForeignKey(
        Ypiresia,
        on_delete=models.PROTECT,
        verbose_name="Υπηρεσία Τρέχουσας Τοποθέτησης"
    )
    sxoliko_etos = models.CharField(max_length=9, verbose_name="Σχολικό Έτος (π.χ. 2024-25)") # π.χ. 2023-24
    typos_ekpaideftikou = models.CharField(
        max_length=20,
        choices=TYPOI_EKPAIDEFTIKOU_CHOICES,
        verbose_name="Τύπος Εκπαιδευτικού"
    )
    imerominia_ypovolis = models.DateField(
        blank=True,
        null=True,
        verbose_name="Ημερομηνία Υποβολής Αίτησης"
    )
    arxeio_aitisis_pdf = models.FileField(
        upload_to='aitiseis_pdf/%Y/%m/', # Θα δημιουργήσει υποφακέλους ανά έτος/μήνα
        blank=True,
        null=True,
        verbose_name="Αρχείο Αίτησης (PDF)"
    )
    se_anamoni = models.BooleanField(
        default=False,
        verbose_name="Σε Αναμονή Δικαιολογητικών"
    )
    pyseep_proothisis = models.ForeignKey(
        PYSEEP,
        on_delete=models.SET_NULL, # Αν διαγραφεί το ΠΥΣΕΕΠ, το πεδίο γίνεται null
        blank=True,
        null=True,
        related_name='aitiseis_proothisis',
        verbose_name="Έτοιμη για ΠΥΣΕΕΠ (Προώθηση)"
    )
    pyseep_teliki_apofasi = models.ForeignKey(
        PYSEEP,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='aitiseis_telikes_apofaseis',
        verbose_name="Τελική Απόφαση από ΠΥΣΕΕΠ"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ημερομηνία Δημιουργίας")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ημερομηνία Ενημέρωσης")

    def __str__(self):
        return f"Αίτηση {self.id} του {self.ekpaideftikos} για το {self.sxoliko_etos}"

    def clean(self):
        # Business Logic: Μια αίτηση είτε θα είναι σε αναμονή είτε σε ΠΥΣΕΕΠ. Δεν γίνεται και τα δύο μαζί.
        # Επίσης, δεν μπορεί να έχει pyseep_teliki_apofasi αν δεν έχει pyseep_proothisis
        if self.se_anamoni and self.pyseep_proothisis:
            raise ValidationError(
                "Μια αίτηση δεν μπορεί να είναι ταυτόχρονα 'Σε Αναμονή' και 'Έτοιμη για ΠΥΣΕΕΠ'."
            )
        if self.pyseep_teliki_apofasi and not self.pyseep_proothisis:
             raise ValidationError(
                "Μια αίτηση δεν μπορεί να έχει 'Τελική Απόφαση ΠΥΣΕΕΠ' χωρίς να έχει προηγηθεί 'Προώθηση σε ΠΥΣΕΕΠ'."
            )
        if self.pyseep_teliki_apofasi and self.pyseep_teliki_apofasi.imerominia_praxis < self.pyseep_proothisis.imerominia_praxis:
            raise ValidationError(
                "Η ημερομηνία της τελικής απόφασης ΠΥΣΕΕΠ δεν μπορεί να είναι προγενέστερη της ημερομηνίας προώθησης."
            )

    class Meta:
        verbose_name = "Αίτηση Αναγνώρισης Προϋπηρεσίας"
        verbose_name_plural = "Αιτήσεις Αναγνώρισης Προϋπηρεσιών"
        ordering = ['-created_at']


class Proypiresia(models.Model):
    aitisi = models.ForeignKey(
        Aitisi,
        on_delete=models.CASCADE, # Αν διαγραφεί η αίτηση, διαγράφονται και οι προϋπηρεσίες της
        related_name='proypiresies',
        verbose_name="Αίτηση"
    )
    eidos_proypiresias = models.ForeignKey(
        EidosProypiresias,
        on_delete=models.PROTECT, # Να μην μπορεί να διαγραφεί αν χρησιμοποιείται
        verbose_name="Είδος Προϋπηρεσίας (από λίστα)"
    )
    # Αν θέλουμε να μπορεί να γράψει και ελεύθερο κείμενο αν δεν υπάρχει στη λίστα:
    # eidos_proypiresias_allo = models.CharField(
    #     max_length=255,
    #     blank=True,
    #     null=True,
    #     verbose_name="Είδος Προϋπηρεσίας (άλλη - ελεύθερο κείμενο)"
    # )
    arithmos_protokollou_vevaiosis = models.CharField(
        max_length=100,
        default="ΟΠΣΥΔ",
        verbose_name="Αρ. Πρωτοκόλλου/Βεβ. Προϋπηρεσίας"
    )
    sxesi_ergasias = models.ForeignKey(
        SxesiErgasias,
        on_delete=models.PROTECT, # Να μην μπορεί να διαγραφεί αν χρησιμοποιείται
        verbose_name="Σχέση Εργασίας (από λίστα)"
    )
    # sxesi_ergasias_allo = models.CharField(
    #     max_length=100,
    #     blank=True,
    #     null=True,
    #     verbose_name="Σχέση Εργασίας (άλλη - ελεύθερο κείμενο)"
    # )
    xroniko_diastima_apo = models.DateField(verbose_name="Χρονικό Διάστημα ΑΠΟ")
    xroniko_diastima_eos = models.DateField(verbose_name="Χρονικό Διάστημα ΕΩΣ")
    eti_proypiresias = models.PositiveIntegerField(default=0, verbose_name="Έτη")
    mines_proypiresias = models.PositiveIntegerField(default=0, verbose_name="Μήνες")
    meres_proypiresias = models.PositiveIntegerField(default=0, verbose_name="Μέρες")
    paratiriseis = models.TextField(blank=True, null=True, verbose_name="Παρατηρήσεις")
    esoterikes_simeioseis = models.TextField(blank=True, null=True, verbose_name="Εσωτερικές Σημειώσεις")

    # Ενέργειες για κάθε record προϋπηρεσίας
    elegxthike = models.BooleanField(default=False, verbose_name="Ελέγχθηκε")
    elegxthike_pote = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Ελέγχθηκε στις"
    )
    elegxthike_apo = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='elegxmenes_proypiresies',
        verbose_name="Ελέγχθηκε από"
    )
    paravlepsi = models.BooleanField(default=False, verbose_name="Παράβλεψη (δεν υπολογίζεται)")

    # Αυτόματη συμπλήρωση του elegxthike_pote και elegxthike_apo θα γίνει στο save() ή στο form
    def save(self, *args, **kwargs):
        if self.elegxthike and not self.elegxthike_pote:
            self.elegxthike_pote = timezone.now()
        elif not self.elegxthike: # Αν απο-τσεκαριστεί, καθαρίζουμε τα πεδία
            self.elegxthike_pote = None
            self.elegxthike_apo = None
        super().save(*args, **kwargs)


    def __str__(self):
        return f"Προϋπηρεσία {self.id} για την αίτηση {self.aitisi.id}"

    class Meta:
        verbose_name = "Καταχωρημένη Προϋπηρεσία"
        verbose_name_plural = "Καταχωρημένες Προϋπηρεσίες"
        ordering = ['aitisi', 'xroniko_diastima_apo']


class ProypiresiaPyseepHistory(models.Model):
    """
    Ιστορικό έγκρισης μιας προϋπηρεσίας από παλαιότερα ΠΥΣΕΕΠ.
    Κάθε φορά που μια προϋπηρεσία περνάει από ΠΥΣΕΕΠ (στο πλαίσιο μιας αίτησης)
    και σημειώνεται ως 'Τελική Απόφαση', δημιουργείται μια εγγραφή εδώ.
    """
    proypiresia = models.ForeignKey(
        Proypiresia,
        on_delete=models.CASCADE,
        related_name='pyseep_history_entries',
        verbose_name="Προϋπηρεσία"
    )
    pyseep_apofasis = models.ForeignKey(
        PYSEEP,
        on_delete=models.PROTECT, # Δεν θέλουμε να χαθεί το ιστορικό αν διαγραφεί η πράξη
        verbose_name="ΠΥΣΕΕΠ Απόφασης"
    )
    imerominia_egkrisis_apo_pyseep = models.DateField(verbose_name="Ημερομηνία Έγκρισης από ΠΥΣΕΕΠ")
    # Μπορεί να θέλουμε να κρατάμε και την κατάσταση (π.χ. ΕΓΚΡΙΘΗΚΕ, ΑΠΟΡΡΙΦΘΗΚΕ, ΤΡΟΠΟΠΟΙΗΘΗΚΕ)
    # status = models.CharField(max_length=50, choices=[...], default='ΕΓΚΡΙΘΗΚΕ')

    def __str__(self):
        return f"Ιστορικό ΠΥΣΕΕΠ {self.pyseep_apofasis} για προϋπηρεσία {self.proypiresia.id}"

    class Meta:
        verbose_name = "Ιστορικό Έγκρισης Προϋπηρεσίας από ΠΥΣΕΕΠ"
        verbose_name_plural = "Ιστορικά Εγκρίσεων Προϋπηρεσιών από ΠΥΣΕΕΠ"
        unique_together = [['proypiresia', 'pyseep_apofasis']] # Μια προϋπηρεσία, μια φορά ανά ΠΥΣΕΕΠ
        ordering = ['proypiresia', '-imerominia_egkrisis_apo_pyseep']