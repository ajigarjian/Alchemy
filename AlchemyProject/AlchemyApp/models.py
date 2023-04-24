from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin #added for custom User class and UserManager class
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

# Create your models here.

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password, phone_number, client, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, phone_number=phone_number, client=client, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, phone_number, client, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, phone_number, client, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    phone_regex = RegexValidator(
        regex=r"^\+?1?\d{9,15}$",
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.",
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    client = models.ForeignKey('AlchemyApp.Client', on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["phone_number", "client"]

    groups = models.ManyToManyField(
        "auth.Group",
        verbose_name=_("groups"),
        blank=True,
        related_name="customuser_set",
        related_query_name="customuser",
        help_text=_(
            "The groups this user belongs to. A user will get all permissions "
            "granted to each of their groups."
        ),
    )

    user_permissions = models.ManyToManyField(
        "auth.Permission",
        verbose_name=_("user permissions"),
        blank=True,
        related_name="customuser_set",
        related_query_name="customuser",
        help_text=_("Specific permissions for this user."),
    )

    def __str__(self):
        return f"{self.email} ({self.client.client_name})"

class Client(models.Model):
    client_name = models.CharField(max_length=255) #Client Name

    def __str__(self):
        return str(self.client_name)

class NISTControl(models.Model):
    control_name = models.CharField(max_length=255) #Control Name
    control_family = models.ForeignKey('AlchemyApp.ControlFamily', on_delete=models.CASCADE) #Control Family  
    control_number = models.IntegerField() #Control Number
    control_enhancement = models.IntegerField(blank=True, null=True) #Control Enhancement (can be blank)
    control_description = models.TextField() #Control description
    supplemental_guidance = models.TextField() #Supplemental guidance

    def __str__(self):
        enhancement_text = ""
        if self.control_enhancement:
            enhancement_text = " (" + str(self.control_enhancement) + ")"

        return str((self.control_family.family_abbreviation) + '-' + str(self.control_number) + enhancement_text)

    class Meta:
        verbose_name = "NIST Control"
        verbose_name_plural = "NIST Controls"

class ControlFamily(models.Model):

    # Logic and eventual tuple list for choices in family_name field
    ACCESS_CONTROL='''Access Control''' 
    AWARENESS_AND_TRAINING='''Awareness and Training'''
    AUDIT_AND_ACCOUNTABILITY='''Audit and Accountability'''
    CONFIGURATION_MANAGEMENT='''Configuration Management'''
    CONTINGENCY_PLANNING='''Contingency Planning'''
    IDENTIFICATION_AND_AUTHENTICATION='''Identification and Authentication'''
    INCIDENT_RESPONSE='''Incident Response'''
    MAINTENANCE='''Maintenance'''
    MEDIA_PROTECTION='''Media Protection'''
    PHYSICAL_AND_ENVIRONMENTAL_PROTECTION='''Physical and Environmental Protection'''
    PLANNING='''Planning'''
    PERSONNEL_SECURITY='''Personnel Security'''
    RISK_ASSESSMENT='''Risk Assessment'''
    SECURITY_ASSESSMENT_AND_AUTHORIZATION='''Security Assessment and Authorization'''
    SYSTEM_AND_COMMUNICATIONS_PROTECTION='''System and Communications Protection'''
    SYSTEM_AND_INFORMATION_INTEGRITY='''System and Information Integrity'''
    SYSTEM_AND_SERVICES_ACQUISITION='''System and Services Acquisition'''

    FAMILY_LIST = [
        (ACCESS_CONTROL, 'Access Control'),
        (AWARENESS_AND_TRAINING, 'Awareness and Training'),
        (AUDIT_AND_ACCOUNTABILITY, 'Audit and Accountability'),
        (CONFIGURATION_MANAGEMENT, 'Configuration Management'),
        (CONTINGENCY_PLANNING, 'Contingency Planning'),
        (IDENTIFICATION_AND_AUTHENTICATION, 'Identification and Authentication'),
        (INCIDENT_RESPONSE, 'Incident Response'),
        (MAINTENANCE, 'Maintenance'),
        (MEDIA_PROTECTION, 'Media Protection'),
        (PHYSICAL_AND_ENVIRONMENTAL_PROTECTION, 'Physical and Environmental Protection'),
        (PLANNING, 'Planning'),
        (PERSONNEL_SECURITY, 'Personnel Security'),
        (RISK_ASSESSMENT, 'Risk Assessment'),
        (SECURITY_ASSESSMENT_AND_AUTHORIZATION, 'Security Assessment and Authorization'),
        (SYSTEM_AND_COMMUNICATIONS_PROTECTION, 'System and Communications Protection'),
        (SYSTEM_AND_INFORMATION_INTEGRITY, 'System and Information Integrity'),
        (SYSTEM_AND_SERVICES_ACQUISITION, 'System and Services Acquisition')
    ]

    family_name = models.CharField(max_length=40, choices=FAMILY_LIST, default=None) #Control Family Name

    ACCESS_CONTROL='''AC''' 
    AWARENESS_AND_TRAINING='''AT'''
    AUDIT_AND_ACCOUNTABILITY='''AU'''
    CONFIGURATION_MANAGEMENT='''CM'''
    CONTINGENCY_PLANNING='''CP'''
    IDENTIFICATION_AND_AUTHENTICATION='''IA'''
    INCIDENT_RESPONSE='''IR'''
    MAINTENANCE='''MA'''
    MEDIA_PROTECTION='''MP'''
    PHYSICAL_AND_ENVIRONMENTAL_PROTECTION='''PE'''
    PLANNING='''PL'''
    PERSONNEL_SECURITY='''PS'''
    RISK_ASSESSMENT='''RA'''
    SECURITY_ASSESSMENT_AND_AUTHORIZATION='''CA'''
    SYSTEM_AND_COMMUNICATIONS_PROTECTION='''SC'''
    SYSTEM_AND_INFORMATION_INTEGRITY='''SI'''
    SYSTEM_AND_SERVICES_ACQUISITION='''SA'''

    ABBV_LIST = [
        (ACCESS_CONTROL, 'AC'),
        (AWARENESS_AND_TRAINING, 'AT'),
        (AUDIT_AND_ACCOUNTABILITY, 'AU'),
        (CONFIGURATION_MANAGEMENT, 'CM'),
        (CONTINGENCY_PLANNING, 'CP'),
        (IDENTIFICATION_AND_AUTHENTICATION, 'IA'),
        (INCIDENT_RESPONSE, 'IR'),
        (MAINTENANCE, 'MA'),
        (MEDIA_PROTECTION, 'MP'),
        (PHYSICAL_AND_ENVIRONMENTAL_PROTECTION, 'PE'),
        (PLANNING, 'PL'),
        (PERSONNEL_SECURITY, 'PS'),
        (RISK_ASSESSMENT, 'RA'),
        (SECURITY_ASSESSMENT_AND_AUTHORIZATION, 'CA'),
        (SYSTEM_AND_COMMUNICATIONS_PROTECTION, 'SC'),
        (SYSTEM_AND_INFORMATION_INTEGRITY, 'SI'),
        (SYSTEM_AND_SERVICES_ACQUISITION, 'SA')
    ]

    family_abbreviation = models.CharField(max_length=2, choices=ABBV_LIST, default=None)
    family_description = models.CharField(max_length=255, blank="True", null="True")

    class Meta:
        verbose_name = "Control Family"
        verbose_name_plural = "Control Families"

    def __str__(self):
        return f"{self.family_name}"

class Question(models.Model):
    controls = models.ManyToManyField(NISTControl) #Many-to-Many relationship with applicable NISTControls
    question_text = models.TextField() #Question Language

    def __str__(self):
        related_controls = ', '.join(
            [
                control.control_family.family_abbreviation + '-'
                + str(control.control_number)
                + (f" ({control.control_enhancement})" if control.control_enhancement else '')
                for control in self.controls.all()
            ]
        )
        return f"Q{self.id}: Related Controls: {related_controls}"

class Answer(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE) #Client answering
    question = models.ForeignKey(Question, on_delete=models.CASCADE) #Question answered
    answer_text = models.TextField() #What the answer was

    class Meta:
        unique_together = ('client', 'question')

    def __str__(self):
        answer_preview = self.answer_text[:50] + "..." if len(self.answer_text) > 50 else self.answer_text
        return f"{self.client.client_name}: Q{self.question.id}: {answer_preview}"

class InformationCategory(models.Model):
    info_category = models.CharField(max_length=255) #Information category
    category_description = models.TextField()

    class Meta:
        verbose_name = "Information Category"
        verbose_name_plural = "Information Categories"

    def __str__(self):
        return str(self.info_category)

class InformationSubCategory(models.Model):
    info_subcategory = models.CharField(max_length=255) #Information subcategory
    parent_category = models.ForeignKey(InformationCategory, on_delete=models.CASCADE)
    subcategory_description = models.TextField()

    class Meta:
        verbose_name = "Information Subcategory"
        verbose_name_plural = "Information SubCategories"
    
    def __str__(self):
        return str(self.info_subcategory)