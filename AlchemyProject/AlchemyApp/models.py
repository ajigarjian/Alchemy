from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin #added for custom User class and UserManager class
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinLengthValidator, MaxLengthValidator
from .managers import CustomUserManager
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    phone_regex = RegexValidator(
        regex=r"^\+?1?\d{9,15}$",
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.",
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    client = models.ForeignKey('AlchemyApp.Client', on_delete=models.CASCADE)
    
    is_staff = models.BooleanField(default=True) #to be able to log into django admin
    is_superuser = models.BooleanField(default=True) #to be able to log into django admin AND have read/write access

    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="customuser_groups",
        related_query_name="customuser",
    )

    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="customuser_user_permissions",
        related_query_name="customuser",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["phone_number", "client_id"]

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.email} ({self.client.client_name})"

class Client(models.Model):

    # State option list logic
    ALABAMA = 'AL'
    ALASKA = 'AK'
    ARIZONA = 'AZ'
    ARKANSAS = 'AR'
    CALIFORNIA = 'CA'
    COLORADO = 'CO'
    CONNECTICUT = 'CT'
    DELAWARE = 'DE'
    FLORIDA = 'FL'
    GEORGIA = 'GA'
    HAWAII = 'HI'
    IDAHO = 'ID'
    ILLINOIS = 'IL'
    INDIANA = 'IN'
    IOWA = 'IA'
    KANSAS = 'KS'
    KENTUCKY = 'KY'
    LOUISIANA = 'LA'
    MAINE = 'ME'
    MARYLAND = 'MD'
    MASSACHUSETTS = 'MA'
    MICHIGAN = 'MI'
    MINNESOTA = 'MN'
    MISSISSIPPI = 'MS'
    MISSOURI = 'MO'
    MONTANA = 'MT'
    NEBRASKA = 'NE'
    NEVADA = 'NV'
    NEW_HAMPSHIRE = 'NH'
    NEW_JERSEY = 'NJ'
    NEW_MEXICO = 'NM'
    NEW_YORK = 'NY'
    NORTH_CAROLINA = 'NC'
    NORTH_DAKOTA = 'ND'
    OHIO = 'OH'
    OKLAHOMA = 'OK'
    OREGON = 'OR'
    PENNSYLVANIA = 'PA'
    RHODE_ISLAND = 'RI'
    SOUTH_CAROLINA = 'SC'
    SOUTH_DAKOTA = 'SD'
    TENNESSEE = 'TN'
    TEXAS = 'TX'
    UTAH = 'UT'
    VERMONT = 'VT'
    VIRGINIA = 'VA'
    WASHINGTON = 'WA'
    WEST_VIRGINIA = 'WV'
    WISCONSIN = 'WI'
    WYOMING = 'WY'
    DISTRICT_OF_COLUMBIA = 'DC'
    AMERICAN_SAMOA = 'AS'
    GUAM = 'GU'
    NORTHERN_MARIANA_ISLANDS = 'MP'
    PUERTO_RICO = 'PR'
    UNITED_STATES_MINOR_OUTLYING_ISLANDS = 'UM'
    US_VIRGIN_ISLANDS = 'VI'

    STATE_LIST = {
    (ALABAMA, 'Alabama'),
        (ALASKA, 'Alaska'),
        (ARIZONA, 'Arizona'),
        (ARKANSAS, 'Arkansas'),
        (CALIFORNIA, 'California'),
        (COLORADO, 'Colorado'),
        (CONNECTICUT, 'Connecticut'),
        (DELAWARE, 'Delaware'),
        (FLORIDA, 'Florida'),
        (GEORGIA, 'Georgia'),
        (HAWAII, 'Hawaii'),
        (IDAHO, 'Idaho'),
        (ILLINOIS, 'Illinois'),
        (INDIANA, 'Indiana'),
        (IOWA, 'Iowa'),
        (KANSAS, 'Kansas'),
        (KENTUCKY, 'Kentucky'),
        (LOUISIANA, 'Louisiana'),
        (MAINE, 'Maine'),
        (MARYLAND, 'Maryland'),
        (MASSACHUSETTS, 'Massachusetts'),
        (MICHIGAN, 'Michigan'),
        (MINNESOTA, 'Minnesota'),
        (MISSISSIPPI, 'Mississippi'),
        (MISSOURI, 'Missouri'),
        (MONTANA, 'Montana'),
        (NEBRASKA, 'Nebraska'),
        (NEVADA, 'Nevada'),
        (NEW_HAMPSHIRE, 'New Hampshire'),
        (NEW_JERSEY, 'New Jersey'),
        (NEW_MEXICO, 'New Mexico'),
        (NEW_YORK, 'New York'),
        (NORTH_CAROLINA, 'North Carolina'),
        (NORTH_DAKOTA, 'North Dakota'),
        (OHIO, 'Ohio'),
        (OKLAHOMA, 'Oklahoma'),
        (OREGON, 'Oregon'),
        (PENNSYLVANIA, 'Pennsylvania'),
        (RHODE_ISLAND, 'Rhode Island'),
        (SOUTH_CAROLINA, 'South Carolina'),
        (SOUTH_DAKOTA, 'South Dakota'),
        (TENNESSEE, 'Tennessee'),
        (TEXAS, 'Texas'),
        (UTAH, 'Utah'),
        (VERMONT, 'Vermont'),
        (VIRGINIA, 'Virginia'),
        (WASHINGTON, 'Washington'),
        (WEST_VIRGINIA, 'West Virginia'),
        (WISCONSIN, 'Wisconsin'),
        (WYOMING, 'Wyoming'),
        (DISTRICT_OF_COLUMBIA, 'District of Columbia'),
        (AMERICAN_SAMOA, 'American Samoa'),
        (GUAM, 'Guam'),
        (NORTHERN_MARIANA_ISLANDS, 'Northern Mariana Islands'),
        (PUERTO_RICO, 'Puerto Rico'),
        (UNITED_STATES_MINOR_OUTLYING_ISLANDS, 'United States Minor Outlying Islands'),
        (US_VIRGIN_ISLANDS, 'U.S. Virgin Islands')
    }

    zip_code_regex = RegexValidator(
        r'^\d{5}(?:[-\s]\d{4})?$',
        message="Enter a valid U.S. ZIP code."
    )

    city_regex = RegexValidator(
        r'^[a-zA-Z\s]+$',
        message="Enter a valid city name containing only letters and spaces."
    )

    def validate_street_address(value):
        if len(value.split()) < 2:
            raise ValidationError("Enter a valid street address.")

    client_name = models.CharField(max_length=255, validators=[MinLengthValidator(1)], blank=False, null=False, unique=True)
    address1 = models.CharField("Address line 1", max_length=1024, validators=[validate_street_address], blank=True, null=True)
    address2 = models.CharField("Address line 2",max_length=1024, blank=True, null=True)
    city = models.CharField("City", max_length=1024, validators=[city_regex], blank=True, null=True)
    state = models.CharField("State", max_length=2, choices=STATE_LIST, default=None, blank=True, null=True)
    zip_code = models.CharField("ZIP / Postal code", max_length=12, validators=[zip_code_regex], blank=True, null=True)

    def __str__(self):
        return str(self.client_name)

class System(models.Model):

    ENVIRONMENT_CHOICES = [
        ('On-Premises', 'On-Premises'),
        ('Cloud-Based', 'Cloud-Based'),
        ('Hybrid', 'Hybrid'),
    ]

    OPERATIONAL_STATUS_CHOICES = [
        ('Under Development', 'Under Development'),
        ('Operational', 'Operational'),
        ('Decommissioned', 'Decommissioned'),
    ]

    FEDRAMP_COMPLIANCE_STATUS_CHOICES = [
        ('Not Started', 'Not Started'),
        ('In Progress', 'In Progress'),
        ('Authorized', 'Authorized'),
    ]

    phone_regex = RegexValidator(
        regex=r"^\+?1?\d{9,15}$",
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.",
    )

    name = models.CharField(max_length=255, blank=True, null=True)  # In-scope system name
    abbreviation = models.CharField(max_length=20, blank=True, null=True) #Short abbreviation
    environment = models.CharField(max_length=20, choices=ENVIRONMENT_CHOICES, blank=True, null=True) #Type of hosting environment (on-prem, cloud, hybrid)

    description = models.TextField(blank=True, null=True)  # System purpose description
    authorization_boundary = models.TextField(blank=True, null=True) #  A brief description of the boundary that separates the system from other systems and networks.

    operational_status = models.CharField(max_length=20, choices=OPERATIONAL_STATUS_CHOICES, blank=True, null=True) #If system is in dev, operational, or decommed
    last_authorization_date = models.DateField(blank=True, null=True) #The date when the system was last granted an Authorization to Operate (ATO) or Provisional Authorization to Operate (P-ATO) by a federal agency or the Joint Authorization Board (JAB).
    fedramp_compliance_status = models.CharField(max_length=20, choices=FEDRAMP_COMPLIANCE_STATUS_CHOICES, blank=True, null=True, default='not_started') #Current status in the FedRAMP authorization process (e.g., not started, in progress, or authorized). 
    
    owner_name = models.CharField(max_length=255, blank=True, null=True)
    owner_title = models.CharField(max_length=255, blank=True, null=True)
    owner_email = models.EmailField(unique=True, blank=True, null=True)
    owner_phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True, null=True)

    client = models.ForeignKey(Client, on_delete=models.CASCADE)  # Client to which the system belongs
    color = color = models.CharField(max_length=20)
    information_subcategories = models.ManyToManyField(
        'AlchemyApp.InformationSubCategory',
        verbose_name=_('information subcategories'),
        blank=True,
        help_text=_('The information subcategories that flow through the system.'),
        related_name="system_information_subcategories",
        related_query_name="system",
    )

    #Making combination of client and name unique so that a given client cannot have two systems with the same name
    class Meta:
        unique_together = ('name', 'client') 

    def __str__(self):
        return f"{self.name} ({self.client.client_name})"

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

class NISTControlPart(models.Model):
    control = models.ForeignKey('NISTControl', related_name='parts', on_delete=models.CASCADE)
    part_letter = models.CharField(max_length=1)
    part_description = models.TextField()

    class Meta:
        verbose_name = "NIST Control Part"
        verbose_name_plural = "NIST Control Parts"

    def __str__(self):
        return f'{self.control}: {self.part_letter}'

class NISTControl(models.Model):
    control_name = models.CharField(max_length=255) #Control Name
    control_family = models.ForeignKey('AlchemyApp.ControlFamily', on_delete=models.CASCADE) #Control Family  
    control_number = models.IntegerField() #Control Number
    control_enhancement = models.IntegerField(blank=True, null=True) #Control Enhancement (can be blank)
    control_description = models.TextField() #Control description
    supplemental_guidance = models.TextField(blank=True, null=True) #Supplemental guidance

    def __str__(self):
        enhancement_text = ""
        if self.control_enhancement:
            enhancement_text = " (" + str(self.control_enhancement) + ")"

        return str((self.control_family.family_abbreviation) + '-' + str(self.control_number) + enhancement_text)

    class Meta:
        verbose_name = "NIST Control"
        verbose_name_plural = "NIST Controls"

class ControlImplementationStatement(models.Model):
    control_implementation = models.ForeignKey('AlchemyApp.ControlImplementation', related_name='control_statement_parts', on_delete=models.CASCADE)
    control_part = models.ForeignKey('NISTControlPart', on_delete=models.CASCADE)
    statement = models.TextField(blank=True, null=True)  # Control Part Implementation description
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('control_implementation', 'control_part')

    def __str__(self):
        return f'{self.control_implementation.system}: {self.control_part.control}.{self.control_part.part_letter} - {self.statement}'

class ImplementationStatus(models.Model):
    STATUS_CHOICES = [
        ('Implemented', 'Implemented'),
        ('Partially Implemented', 'Partially Implemented'),
        ('Planned', 'Planned'),
        ('Alternative Implementation', 'Alternative Implementation'),
        ('Not Applicable', 'Not Applicable')
    ]
    status = models.CharField(max_length=30, choices=STATUS_CHOICES)

    def __str__(self):
        return self.status

    class Meta:
        verbose_name = "Implementation Status"
        verbose_name_plural = "Implementation Statuses"

class ControlOrigination(models.Model):
    ORIGINATION_CHOICES = [
        ('Service Provider Corporate', 'Service Provider Corporate'),
        ('Service Provider System Specific', 'Service Provider System Specific'),
        ('Service Provider Hybrid', 'Service Provider Hybrid'),
        ('Configured by Customer', 'Configured by Customer'),
        ('Provided by Customer', 'Provided by Customer'),
        ('Shared', 'Shared'),
        ('Inherited', 'Inherited')
    ]
    
    origination = models.CharField(max_length=50, choices=ORIGINATION_CHOICES)

    def __str__(self):
        return self.origination

    class Meta:
        verbose_name = "Control Origination"
        verbose_name_plural = "Control Originations"

class ResponsibleRole(models.Model):
    
    responsible_role = models.CharField(max_length=255)

    def __str__(self):
        return self.responsible_role

    class Meta:
        verbose_name = "Responsible Role"
        verbose_name_plural = "Responsible Roles"

class ControlImplementation(models.Model):

    PROGRESS_CHOICES = [
        ('Not Started', 'Not Started'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed')
    ]

    system = models.ForeignKey('System', on_delete=models.CASCADE)
    control = models.ForeignKey('NISTControl', on_delete=models.CASCADE) #Linked control
    control_family = models.ForeignKey('ControlFamily', on_delete=models.CASCADE)
    responsible_role = models.ForeignKey('ResponsibleRole', blank=True, null=True, on_delete=models.RESTRICT)
    statuses = models.ManyToManyField(ImplementationStatus)
    originations = models.ManyToManyField(ControlOrigination)
    statement = models.TextField(blank=True, null=True)
    progress = models.CharField(max_length=30, choices=PROGRESS_CHOICES, blank=True, null=True, default='Not Started')
    last_updated = models.DateTimeField(auto_now=True)

    # Making combination of client and name unique so that a given system cannot have two control implementations with the same control
    class Meta:
        unique_together = ('control', 'system')
    
    @property
    def origination_ids(self):
        return [o.id for o in self.originations.all()]

    @property
    def status_ids(self):
        return [s.id for s in self.statuses.all()]
    
    def __str__(self):
        return str(str(self.system) + ": " + str(self.control))

    def save(self, *args, **kwargs):
        # if this is a new instance, the ID field will not be set
        is_new = self.id is None

        super().save(*args, **kwargs)  # Call the "real" save() method.

        if is_new:  # if this is a new instance
            for part in self.control.parts.all():
                ControlImplementationStatement.objects.create(control_implementation=self, control_part=part)

class Question(models.Model):

    CONTROL_QUESTION='''Control Question'''
    OVERVIEW_QUESTION='''Overview Question'''
    DATA_TYPE_QUESTION='''Data Type Question'''
    IMPACT_QUESTION='''Impact Question'''

    QUESTION_TYPE_LIST = [
        (CONTROL_QUESTION, '''Control Question'''),
        (OVERVIEW_QUESTION, '''Overview Question'''),
        (DATA_TYPE_QUESTION, '''Data Type Question'''),
        (IMPACT_QUESTION, '''Impact Question'''),
    ]

    controls = models.ManyToManyField(NISTControl, blank=True) #Many-to-Many relationship with applicable NISTControls
    question_type = models.CharField(max_length=40, choices=QUESTION_TYPE_LIST, blank=True) #Type of question that was asked
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
    system = models.ForeignKey(System, on_delete=models.SET_NULL, null=True)  # System answering
    question = models.ForeignKey(Question, on_delete=models.CASCADE)  # Question answered
    answer_text = models.TextField()  # What the answer was

    def __str__(self):
        answer_preview = self.answer_text[:50] + "..." if len(self.answer_text) > 50 else self.answer_text
        return f"{self.system.client.client_name}: {self.system.name}: Q{self.question.id}: {answer_preview}"

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