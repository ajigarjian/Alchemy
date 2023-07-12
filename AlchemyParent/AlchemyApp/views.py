import json #for api calls
import random #for generating system color for client dashboard
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, FileResponse #for API calls
from django.urls import reverse #for HttpResponseRedirect(reverse)
from django.contrib.auth import authenticate, login, logout #for login/logout/register
from django.views.decorators.csrf import csrf_exempt #for API calls
from django.contrib import messages #for register error message(s)
from .models import CustomUser, Client, NISTControl, NISTControlElement, Question, Answer, ControlFamily, InformationCategory, InformationSubCategory, System, ControlImplementation, ControlImplementationStatement, ImplementationStatus, ControlOrigination, ResponsibleRole #for interacting with database
from .forms import OrganizationForm, SystemForm
from django.contrib.auth.backends import ModelBackend
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required #to redirect user to login route if they try to access an app page past login
from django.db.models import Count, Case, When, F, Q, Max, IntegerField, Subquery, Prefetch, OuterRef, Exists
from django.core import serializers
import os, openai
from dotenv import load_dotenv
from urllib.parse import unquote #to decode url strings passed through urls as parameters, e.g. client
from django.db.models.functions import Coalesce #for treating base controls with enhancements as null as high values 
from io import StringIO # For Innovation Hub reading CSV
import pandas as pd # For Innovation Hub reading CSV
from openpyxl.styles import Alignment
from openpyxl import load_workbook
from django.conf import settings
from docx import Document
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.shared import Pt
from pathlib import Path
from collections import defaultdict
from math import ceil
import xml.etree.ElementTree as ET
import zipfile
import tempfile
import datetime
import boto3 #for generating the report
from botocore.config import Config #for generating the report
from botocore.exceptions import NoCredentialsError #for generating the report
import io #for generating the report
import time

load_dotenv()

####################################### Public Application when not logged in ##############################################

# Route to render the landing page
def index(request):

    if not request.user.is_authenticated:

        return render(request, "public/index.html")
    
    else:
        return HttpResponseRedirect(reverse("alchemy:dashboard"))

def login_view(request):
    # if this is a POST, process the login data and redirect the logged in user to the overview page
    if request.method == "POST":
        # process the data in form.cleaned_data as required
        email = request.POST["email"]
        password = request.POST["password"]

        #attempt to sign user in, return User object if so
        user = authenticate(request, email=email, password=password)

        if user:
            login(request, user)
            return HttpResponseRedirect(reverse("alchemy:dashboard"))
        else:
            context = {
                'error_message': 'Invalid email or password.',
            }

            return render(request, "public/login.html", context)

    # if not a POST request, show the login page
    if not request.user.is_authenticated:
        return render(request, "public/login.html")
    else:
        return HttpResponseRedirect(reverse("alchemy:logout"))


def register_view(request):

    if request.method == 'POST':
        email = request.POST['email']
        phone_number = request.POST['phone_number']
        client = Client.objects.get(id=request.POST['client'])
        password = request.POST['password']

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect('alchemy:register')

        user = CustomUser.objects.create(email=email, phone_number=phone_number, client=client)
        user.set_password(password)
        user.save()

        # Log the user in.
        backend = ModelBackend()
        user.backend = f"{backend.__module__}.{backend.__class__.__name__}"
        login(request, user)
        return redirect('alchemy:index')

    else:
        if request.user.is_authenticated:
            logout(request)
        return render(request, 'public/register.html', {
            "clients": Client.objects.all()
        })

def logout_view(request):

    if request.user.is_authenticated:
        logout(request)
    return HttpResponseRedirect(reverse("alchemy:index"))

def contact(request):

    if request.user.is_authenticated:
         return HttpResponseRedirect(reverse("alchemy:dashboard"))
    return render(request, "public/contact.html")

def fedramp(request, control):

    # Get the control and control families from the database
    control_object = get_object_or_404(NISTControl, id=control)
    control_families = ControlFamily.objects.all().order_by('family_abbreviation')

    # For each control family, order its controls
    for family in control_families:
        family.controls = family.family_controls.all().order_by(
            'control_family__family_abbreviation', 
            'control_number', 
            Coalesce('control_enhancement', -1)
        )

    # render fedramp.html given

    return render(request, "public/fedramp.html", {
        "control": control_object,
        "control_families": control_families,
    })

def assess(request):

    # render assess.html

    return render(request, "public/assess.html")

@csrf_exempt
def generate_ai_assessment(request):

    # Cannot call this API call to OpenAI unless via the file upload POSTing to backend
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)
    
    # Get the file uploaded
    data_file = request.FILES["data_file"]
    
    # If the file is too big, reject it
    if data_file.multiple_chunks():
        return JsonResponse({"error": "Uploaded file is too big (%.2f MB)." % (data_file.size/(1000*1000),)}, status=400)

    # Get the file extension
    file_extension = os.path.splitext(data_file.name)[1]

    # Take in the file data and put it into a dict
    if file_extension == '.csv':
        file_data = data_file.read().decode("utf-8")
        data = pd.read_csv(StringIO(file_data))
    elif file_extension == '.xlsx':
        data = pd.read_excel(data_file)

    descriptions = []

    for index, row in data.iterrows():
        if pd.isna(row['Assessment Findings']):
            continue  # Skip this row if column 4 is empty
        description = f"I am an information security employee working for a company. I am assessing how well they are meeting NIST CSF subcategory requirements. They have advised me of the following for a given CSF subcategory: The NIST CSF Function is {row['Function']}, the NIST CSF Category is {row['Category']}, and the NIST CSF Subcategory is {row['Subcategory']}. The company has described the controls they have in place for this subcategory as follows: {row['Assessment Findings']}. Please return 1) if you think their description is meeting the subcategory with an answer of 'Implemented', 'Partially Implemented', or 'Not Implemented', and 2) the rationale why, and 3) if 'Partially' or 'Not Implemented', suggestions on how the company may improve. Use the company name where applicable."
        descriptions.append(description)

    openai.api_key = os.getenv("OPENAI_API_KEY", None)

    answers = []

    for description in descriptions:
    
        completion = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Let's transition into a discussion about the NIST Cybersecurity Framework v1.1. As an AI with extensive training in various topics, I would like you to draw from your understanding of the NIST CSF for the next series of questions. Please provide information and advice as an expert on CSF core functions, categories, and subcategories. Limit your responses to no more than 8 sentences. Do not repeat the function or subfunction or category - just the answer."},
                        {"role": "user", "content": description}
                    ],
                    temperature=0.2
            )
        
        answers.append(completion.choices[0].message.content)
    
    data['Testing Results & Rationale'] = pd.Series(answers)

    # Write the DataFrame back to a file in the same format as the input
    if file_extension == '.csv':
        data.to_csv('/tmp/output.csv', index=False)
        response = FileResponse(open('/tmp/output.csv', 'rb'), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="output.csv"'
    elif file_extension == '.xlsx':
        # Step 1: Write DataFrame to an Excel file without any formatting
        data.to_excel('/tmp/output.xlsx', index=False)

        # Step 2: Load the Excel file and apply formatting
        book = load_workbook('/tmp/output.xlsx')

        for sheet in book.worksheets:
            for column in sheet.columns:
                max_length = 0
                column = [cell for cell in column]
                for cell in column:
                    cell.alignment = Alignment(wrap_text=True)
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(cell.value)
                    except:
                        pass
                adjusted_width = max_length if max_length < 60 else 60  # set the maximum width to 30
                sheet.column_dimensions[column[0].column_letter].width = adjusted_width

        book.save('/tmp/output.xlsx')

        response = FileResponse(open('/tmp/output.xlsx', 'rb'), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="output.xlsx"'
    return response

####################################### Internal Application once logged in ##############################################

@csrf_exempt
@login_required
def implementation(request, system, control_family, control=None):
    
    client = request.user.client
    system_object = get_object_or_404(System, name=unquote(system), client=client)
    control_family_object = get_object_or_404(ControlFamily, family_name=unquote(control_family))
    # Only fetch a NISTControl object if control is not None
    implementation_object = None
    if control is not None:
        implementation_object = get_object_or_404(ControlImplementation, system=system_object.id, control=control)

    # Define a Prefetch object for the elements that specifies the order
    elements_prefetch = Prefetch('control__elements', queryset=NISTControlElement.objects.all())
    statements_prefetch = Prefetch('control_statement_elements', queryset=ControlImplementationStatement.objects.all())

    # Pass the Prefetch object to the prefetch_related method
    control_implementations = ControlImplementation.objects.filter(system=system_object, control_family=control_family_object).select_related('control', 'control_family', 'responsible_role').prefetch_related('statuses', 'originations', elements_prefetch, statements_prefetch).order_by('control__control_family__family_abbreviation', 'control__control_number', Coalesce('control__control_enhancement', -1))

    # Case where the search has been updated and an AJAX Call has been POSTed. This branch updates the control implementations rendered
    if request.method == 'POST':

        # Load the AJAX call data for each of the search filters
        data = json.loads(request.body)

        filters = Q()

        if role := data.get('role'):
            filters &= Q(responsible_role__responsible_role=role)
        
        if origination_statuses := data.get('origination_statuses'):
            filters &= Q(originations__origination__in=origination_statuses)

        if implementation_statuses := data.get('implementation_statuses'):
            filters &= Q(statuses__status__in=implementation_statuses)
        
        control_implementations = control_implementations.filter(filters)
        
        serialized_data = ImplementationSerializer(control_implementations, many=True).data

        return JsonResponse(serialized_data, safe=False)

    # Case where the page is initially rendered from the dashboard with all controls being rendered for a given system
    else:

        implementation_choices = ImplementationStatus.objects.all()
        origination_choices = ControlOrigination.objects.all()
        roles = ResponsibleRole.objects.all()

        return render(request, "internal/implementation.html", {
            "client": client,
            "system": system_object,
            "implementation": implementation_object,
            "control_implementations": control_implementations,
            "implementation_choices": implementation_choices,
            "origination_choices": origination_choices,
            "roles": roles,
            "control_family": control_family_object,
            "control_families":ControlFamily.objects.all(),
        })

# Handles showing dashboard page (for GET) as well as creating new systems before showing dashboard page again (for POST)
@login_required
def dashboard(request, system=None):

    client = request.user.client
    systems = System.objects.filter(client=client)

    if system is not None:
        system = unquote(system)

    # If the user is attempting to create a system:
    if (request.method == 'POST') & (request.POST.get("system_name") != None):

        colors = ['3E4756', '97ACCF', 'FFE1E9', 'CAAAB2', '6E7788', '5A3F46', '8D6F77', 'A2ACBD', 'CF9EAA', '986A76', '564147', 'CF9EAC', 'F3E7D0', 'BBB099', 'BEA5AB', 'BBB19B', '867D67']

        # process the data for new system. Use the client of the logged in user, and choose a random color
        system_name = request.POST.get("system_name")

        color = random.choice(colors)

        # Try to make a new system, if not possible, it's due to the system already existing
        try:
            system = System.objects.create(name=system_name, client=client, color=color)
            system.save()

        except IntegrityError:
            return render(request, "dashboard.html", {
                "message": "Email already being used."
            })

        return HttpResponseRedirect(reverse("alchemy:dashboard"))
    
    else:

        # Otherwise, if the user is just visiting the dashboard via get request, show the systems (and formulate %s for progress bar)
        if system is None:
            control_implementations_dict = {}

            for sys in systems:

                # Check that there is a statement for every ControlImplementationStatement linked to this control implementation
                empty_statement_exists = ControlImplementationStatement.objects.filter(
                    control_implementation=OuterRef('pk'),
                    statement__exact=''  # Check for empty statements
                )

                # Check that any ControlImplementationStatement is linked to this control implementation
                any_statement_exists = ControlImplementationStatement.objects.filter(
                    control_implementation=OuterRef('pk')
                )

                filtered_control_implementations = ControlImplementation.objects.filter(system=sys).annotate(
                    has_empty_statements=Exists(empty_statement_exists),
                    has_any_statements=Exists(any_statement_exists),
                    originations_count=Count('originations'),
                    statuses_count=Count('statuses'),
                ).filter(
                    responsible_role__isnull=False,  # Check if the responsible role is not null
                    originations_count__gte=1,  # Check if there is at least one ControlOrigination linked
                    statuses_count__gte=1,  # Check if there is at least one ImplementationStatus linked
                ).exclude(
                    has_empty_statements=True,  # Exclude ControlImplementations that have empty ControlImplementationStatements
                ).filter(
                    Q(has_any_statements=True) | (Q(has_any_statements=False) & ~Q(statement__exact=''))  # If ControlImplementation has no ControlImplementationStatements, it must have its statement field filled
                )

                # Count the number of ControlImplementations meeting the above criteria
                control_implementations_count = filtered_control_implementations.count()

                control_implementations_dict[sys.name] = ceil(100*(control_implementations_count/(ControlImplementation.objects.filter(system=sys).count())))

            return render(request, "internal/dashboard.html", {
                "client": client,
                "systems": systems,
                "percentages":control_implementations_dict
            })

        # Otherwise (final scenario) user is fvisiting dashboard for specific control, so render system_dashboard instead
        else:
            selected_system = get_object_or_404(System, name=system, client=client)

            # Get the ControlFamily objects associated with the selected system
            families = ControlFamily.objects.filter(control_implementations__system=selected_system).order_by('family_abbreviation')

            # Perform the annotations
            families = families.annotate(
                family_controls_count=Count('control_implementations'),
                last_updated=Max('control_implementations__last_updated'),
                
                planned_controls_count=Count('control_implementations', filter=Q(control_implementations__statuses__status='Planned')),
                partial_controls_count=Count('control_implementations', filter=Q(control_implementations__statuses__status='Partially Implemented')),
                implemented_controls_count=Count('control_implementations', filter=Q(control_implementations__statuses__status='Implemented')),
                alternative_controls_count=Count('control_implementations', filter=Q(control_implementations__statuses__status='Alternative Implementation')),
            )
            
            # Count the control implementation statuses
            total_planned = selected_system.control_implementations.filter(statuses__status='Planned').count()
            total_partial = selected_system.control_implementations.filter(statuses__status='Partially Implemented').count()
            total_implemented = selected_system.control_implementations.filter(statuses__status='Implemented').count()
            total_alternative = selected_system.control_implementations.filter(statuses__status='Alternative Implementation').count()

            url_dict = []
            for family in families:
                url = reverse('alchemy:implementation_no_control', args=[selected_system.name, family.family_name])
                url_dict.append({
                    'family_abbreviation': family.family_abbreviation,  # Store the family abbreviation for reference
                    'url': url
                })
            
            urls_json = json.dumps(url_dict)

            return render(request, "internal/system_dashboard.html", {
                "client": client,
                "system": selected_system,
                "families": families,
                "total_planned": total_planned,
                "total_partial": total_partial,
                "total_implemented": total_implemented,
                "urls": urls_json
            })
            
@csrf_exempt
@login_required
def generate_ssp(request):

     #################### SECTION TO PREPARE DOCUMENT AND DATABASE INFO ####################

    # Get the system id from the body of the fetch request and use it to get the system from the database that will have the report made for it
    system_data = json.loads(request.body.decode('utf-8'))
    system_id = system_data['system_id']
    system = get_object_or_404(System, id=system_id)

    # Get the current date
    current_date = datetime.date.today()
    # Convert the date to the desired string format
    date_string = current_date.strftime("%m/%d/%Y")

    # Fetch all control implementations from the database for this specific system
    control_implementations = ControlImplementation.objects.filter(system=system).select_related('responsible_role').prefetch_related('statuses', 'originations').all()

     # Fetch all ControlImplementationStatement objects for this system, and group by associated ControlImplementation
    general_statements = ControlImplementation.objects.filter(system=system).select_related('control').all().order_by('id')
    control_statements = ControlImplementationStatement.objects.filter(control_implementation__system=system).select_related('control_implementation', 'control_element').all().order_by('id')
    
    control_to_general = defaultdict(str)
    for general_statement in general_statements:
        control = general_statement.control.str_SSP()
        statement = general_statement.statement

        control_to_general[(control)] = statement

    control_to_statements = defaultdict(str)
    for control_statement in control_statements:
        control = control_statement.control_implementation.control.str_SSP()
        full_identifier = control_statement.get_full_identifier()
        statement = control_statement.statement

        # Change to map the control and full identifier to the statement
        control_to_statements[(control, full_identifier)] = statement
    
    for key, value in control_to_general.items():
        control = key
        statement = value

    # Define the mapping dictionary - manually mapping what is in the database to SSP text (origination labels don't match up)
    ORIGINATION_CHOICES_MAPPING = {
        'Service Provider Corporate': 'Service Provider Corporate',
        'Service Provider System Specific': 'Service Provider System Specific',
        'Service Provider Hybrid': 'Service Provider Hybrid (Corporate and System Specific)',
        'Configured by Customer': 'Configured by Customer (Customer System Specific)',
        'Provided by Customer': 'Provided by Customer (Customer System Specific)',
        'Shared': 'Shared (Service Provider and Customer Responsibility)',
        'Inherited': 'Inherited from pre-existing FedRAMP Authorization for [Click here to enter text], Date of Authorization'
    }

    # Create a dictionary mapping control identifiers to responsible roles, statuses, and originations for faster lookup
    control_to_role_status_origin = {
        ci.control.str_SSP(): (
            (ci.responsible_role.responsible_role if ci.responsible_role is not None else ''),
            [status.status for status in ci.statuses.all()],
            [origination.origination for origination in ci.originations.all()]
        ) 
        for ci in control_implementations
    }

    control_to_role_status_origin = {
        ci.control.str_SSP(): (
            (ci.responsible_role.responsible_role if ci.responsible_role is not None else ''),
            [status.status for status in ci.statuses.all()],
            [ORIGINATION_CHOICES_MAPPING[origination.origination] for origination in ci.originations.all()]
    )
    for ci in control_implementations}

    #################### SECTION TO SCAN AND EDIT DOCUMENT ####################

     # Load the Word document from static files
    static_path = settings.STATIC_ROOT if settings.STATIC_ROOT else settings.STATICFILES_DIRS[0]
    template_path = os.path.join(static_path, 'SSP-Appendix-A-Moderate-FedRAMP-Security-Controls.docx')
    doc = Document(template_path)

    # Updating the header of SSP appendix with CSO name, CSP name, and date
    table = doc.sections[0].header.tables[0]
    header_run = table.rows[0].cells[1].paragraphs[1].runs[0]
    header_run.clear()
    header_run.text = f'{system.client.client_name}  |  {system.name}  |  <Insert Version X.X  |  {date_string}'

    # Loop through each table in the document
    for table in doc.tables:
        # We're assuming the control identifier is in the text of the first cell of the first row
        control_identifier = table.rows[0].cells[0].text.strip().split(' ')[0]  # taking first word as the control identifier

        # Check if this control identifier is in our dictionary
        if control_identifier in control_to_role_status_origin:
            responsible_role, statuses, originations = control_to_role_status_origin[control_identifier]

            # Populate the responsible role cell (the cell to the right of "Responsible Role:")
            # First, find the cell with "Responsible Role:"
            for row in table.rows:
                for cell in row.cells:
                    if "Responsible Role:" in cell.text:
                        # Once we found it, we clear the cell and then set it to "Responsible Role: <the_role>"
                        cell.text = ""
                        paragraph = cell.paragraphs[0]
                        run = paragraph.add_run("Responsible Role: " + responsible_role)
                        run.font.name = 'Times New Roman'  # change this to your preferred font
                        run.font.size = Pt(12)
                    
                    if "Implementation Status (check all that apply):" in cell.text:
                        cell.text = ""
                        paragraph = cell.add_paragraph("Implementation Status (check all that apply):\n")  # add a new paragraph
                        for status_choice in ImplementationStatus.STATUS_CHOICES:
                            # Use special unicode characters that look like a checkbox
                            checkbox = "☑" if status_choice[0] in statuses else "☐"
                            run = paragraph.add_run(f"{checkbox} {status_choice[1]}\n")  # add each checkbox
                            run.font.name = 'Times New Roman'  # change this to your preferred font
                            run.font.size = Pt(12)
                    
                    if "Control Origination (check all that apply):" in cell.text:
                        cell.text = ""
                        paragraph = cell.add_paragraph("Control Origination (check all that apply):\n")  # add a new paragraph
                        for origination_choice in ControlOrigination.ORIGINATION_CHOICES:
                            # Use special unicode characters that look like a checkbox
                            checkbox = "☑" if origination_choice[1] in originations else "☐"
                            run = paragraph.add_run(f"{checkbox} {origination_choice[1]}\n")  # add each checkbox
                            run.font.name = 'Times New Roman'  # change this to your preferred font
                            run.font.size = Pt(12)

         # Check if the table belongs to a control
        if "What is the solution and how is it implemented?" in table.rows[0].cells[0].text:

            control_identifier = table.rows[0].cells[0].text.strip().split(' ')[0]

            if (len(table.rows) > 2):
                # Process from the second row onwards
                for row in table.rows[1:]:
                    # Get the control element identifier
                    control_element_identifier = row.cells[0].text.replace("Part ", "").replace(":", "").strip()

                    # Replace the implementation statement cell if the control element identifier exists in your dictionary
                    for control, full_identifier in control_to_statements.keys():
                        if control == control_identifier and full_identifier == control_element_identifier:
                            statement = control_to_statements[(control, full_identifier)]

                            # Trim trailing whitespace
                            statement = statement.rstrip()

                            # Clear the cell and add the new text
                            cell = row.cells[0]
                            cell.text = ""
                            paragraph = cell.paragraphs[0]
                            run = paragraph.add_run("Part " + control_element_identifier + ": " + statement)
                            run.font.name = 'Times New Roman'  # change this to your preferred font
                            run.font.size = Pt(12)
            else:
                # Replace the implementation statement cell if the control element identifier exists in your dictionary
                for control in control_to_general.keys():
                    
                    if control == control_identifier:
                        statement = control_to_general[control]

                        # Trim trailing whitespace
                        statement = statement.rstrip()

                        # Clear the cell and add the new text
                        cell = row.cells[0]
                        cell.text = ""
                        paragraph = cell.paragraphs[0]
                        run = paragraph.add_run(statement)
                        run.font.name = 'Times New Roman'  # change this to your preferred font
                        run.font.size = Pt(12)

    # Save the populated document in a temporary location
    doc_path = f'/tmp/SSP-Appendix-A-Moderate-FedRAMP-Security-Controls-{system.name}.docx'
    doc.save(doc_path)

    # Open the .docx file as a zip file
    with zipfile.ZipFile(f'/tmp/SSP-Appendix-A-Moderate-FedRAMP-Security-Controls-{system.name}.docx', 'a') as myzip:
        # Extract the XML file to memory
        with myzip.open('word/document.xml') as f:
            tree = ET.parse(f)

        count = 0
        # Make changes to the XML tree
        for elem in tree.iter():
            if elem.text:
                elem.text = elem.text.replace("<Insert CSO Name>", system.client.client_name)
                elem.text = elem.text.replace("<Insert CSP Name>", system.name)

        # Write the changes back to a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_xml:
            tree.write(temp_xml.name)

        # Replace the XML file in the .docx file with our temporary file
        myzip.write(temp_xml.name, 'word/document.xml')

    # Delete the temporary file
    os.unlink(temp_xml.name)

    # Then, create a FileResponse from the file and set the correct content type and disposition.
    f = open(doc_path, 'rb')
    response = FileResponse(f, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition'] = f'attachment; filename="SSP-Appendix-A-Moderate-FedRAMP-Security-Controls-{system.name}.docx"'
    return response

@csrf_exempt
@login_required
def get_control_origination_data(request):
    system_data = json.loads(request.body.decode('utf-8'))
    system_id = system_data['system_id']

    # Filter ControlImplementation objects by system
    data = ControlImplementation.objects.filter(system_id=system_id).values('responsible_role__responsible_role').annotate(count=Count('id'))
    role_names = [item['responsible_role__responsible_role'] if item['responsible_role__responsible_role'] is not None else 'None' for item in data]
    role_counts = [item['count'] for item in data]
    
    return JsonResponse(data={
        'labels': role_names,
        'data': role_counts,
    })

@csrf_exempt
@login_required
def get_status_data(request):
    system_data = json.loads(request.body.decode('utf-8'))
    system_id = system_data['system_id']

    # Filter ControlImplementation objects by system
    data = ControlImplementation.objects.filter(system_id=system_id).values('statuses__status').annotate(count=Count('id'))
    status_names = [item['statuses__status'] if item['statuses__status'] is not None else 'None' for item in data]
    status_counts = [item['count'] for item in data]
    
    return JsonResponse(data={
        'labels': status_names,
        'data': status_counts,
    })

@csrf_exempt
@login_required
def get_implementation_family_data(request):
    data = json.loads(request.body)
    system_id = data.get('system_id', None)
    system = System.objects.get(id=system_id)

    labels = []
    data = []

    families = ControlFamily.objects.all().order_by('family_abbreviation')
    for family in families:
        implementations = ControlImplementation.objects.filter(control__control_family=family, system=system)
        
        status_dict = {}

        for status in ImplementationStatus.STATUS_CHOICES:
            status_count = implementations.filter(statuses__status=status[0]).count()
            status_dict[status[1]] = status_count

        # Add 'None' to the status dictionary with the count of implementations without any status.
        total_status_counts = sum(status_dict.values())
        status_dict['None'] = implementations.count() - total_status_counts
        
        labels.append(family.family_abbreviation)
        data.append(status_dict)

    return JsonResponse({'labels': labels, 'data': data}, safe=False)

@csrf_exempt
@login_required
def get_origination_data(request):
    system_data = json.loads(request.body.decode('utf-8'))
    system_id = system_data['system_id']

    # Filter ControlImplementation objects by system
    data = ControlImplementation.objects.filter(system_id=system_id).values('originations__origination').annotate(count=Count('id'))
    status_names = [item['originations__origination'] if item['originations__origination'] is not None else 'None' for item in data]
    status_counts = [item['count'] for item in data]
    
    return JsonResponse(data={
        'labels': status_names,
        'data': status_counts,
    })

@login_required
def delete_system(request):

    client = request.user.client

    if request.method == 'POST':
        system_name = unquote(request.POST['delete-system-button'])
        system = get_object_or_404(System, name=system_name, client=client)
        system.delete()

    return redirect('alchemy:dashboard')

@login_required
def rename_system(request):

    client = request.user.client
    

    if request.method == 'POST':
        old_system_name = unquote(request.POST['change-name-button'])
        new_system_name = unquote(request.POST['system_name'])

        system = get_object_or_404(System, name=old_system_name, client=client)
        system.name = new_system_name
        system.save(update_fields=["name"])

    return redirect('alchemy:dashboard')

@login_required
def overview(request, system):

    org = request.user.client
    selected_system = get_object_or_404(System, name=unquote(system), client__client_name=org)
    
    information_types = InformationCategory.objects.all()

    return render(request, "internal/overview.html", {
        "organization": org,
        "system": selected_system,
        "information_types": information_types,
        "org_form": OrganizationForm()
    })

@login_required
def overview2(request, system):

    org = request.user.client
    selected_system = get_object_or_404(System, name=system, client__client_name=org)

    information_types = InformationCategory.objects.all()

    return render(request, "internal/overview2.html", {
        "organization": org,
        "system": selected_system,
        "information_types": information_types,
        "org_form": OrganizationForm(),
        "system_form": SystemForm()
    })

@csrf_exempt
@login_required
def create_update_org(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)

    else:
        data = json.loads(request.body)
        client_id = data.get('id', None)

        if client_id:
            client = get_object_or_404(Client, id=client_id)
            form = OrganizationForm(data, instance=client)
        else:
            form = OrganizationForm(data)

        if form.is_valid():
            client = form.save()
            response_data = {'success': True, 'client_id': client.id}
        else:
            response_data = {'success': False, 'errors': form.errors}

        return JsonResponse(response_data)

@csrf_exempt
@login_required
def update_implementation_status(request):
    if request.method == 'POST':
        # Parse the JSON data from the body of the HTTP request
        data = json.loads(request.body.decode('utf-8'))

        # Get the ControlImplementation instance and ImplementationStatus instance
        implementation = ControlImplementation.objects.get(id=data['implementation_id'])
        status = ImplementationStatus.objects.get(id=data['choice_id'])

        if data['is_checked']:
            # Add the status to the implementation
            implementation.statuses.add(status)
        else:
            # Remove the status from the implementation
            implementation.statuses.remove(status)
        
        # Save the implementation
        implementation.save()

        # Get the updated statuses
        updated_statuses_names = [status.status for status in implementation.statuses.all()]
        updated_statuses_ids = [status.id for status in implementation.statuses.all()]

        # Return a successful response with the updated statuses
        return JsonResponse({'status': 'success', 'updated_statuses_ids': updated_statuses_ids, 'updated_statuses_names': updated_statuses_names}, status=200)

    else:
        # Return an error response if the request method is not POST
        return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
@login_required
def update_origination_status(request):
    if request.method == 'POST':
        # Parse the JSON data from the body of the HTTP request
        data = json.loads(request.body.decode('utf-8'))

        # Get the ControlImplementation instance and ImplementationStatus instance
        implementation = ControlImplementation.objects.get(id=data['implementation_id'])
        origination = ControlOrigination.objects.get(id=data['origination_id'])

        if data['is_checked']:
            # Add the status to the implementation
            implementation.originations.add(origination)
        else:
            # Remove the status from the implementation
            implementation.originations.remove(origination)
        
        # Save the implementation
        implementation.save()

        # Get the updated originations
        updated_originations_names = [origination.origination for origination in implementation.originations.all()]
        updated_originations_ids = [origination.id for origination in implementation.originations.all()]

        # Return a successful response
        return JsonResponse({'status': 'success', 'updated_originations_ids': updated_originations_ids, 'updated_originations_names': updated_originations_names}, status=200)

    else:
        # Return an error response if the request method is not POST
        return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
@login_required
def update_responsible_role(request):
    if request.method == 'POST':
        # Parse the JSON data from the body of the HTTP request
        data = json.loads(request.body.decode('utf-8'))

        # Get the ControlImplementation instance and ImplementationStatus instance
        implementation = ControlImplementation.objects.get(id=data['implementation_id'])
        responsible_role = ResponsibleRole.objects.get(id=data['role_id'])

        if data['is_checked']:
            # Add the status to the implementation
            implementation.responsible_role = responsible_role
        
        # Save the implementation
        implementation.save()

        # Get the updated role
        updated_role_name = implementation.responsible_role.responsible_role
        updated_role_id = implementation.responsible_role.id

        # Return a successful response
        return JsonResponse({'status': 'success', 'updated_role_id': updated_role_id, 'updated_role_name': updated_role_name}, status=200)

    else:
        # Return an error response if the request method is not POST
        return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
@login_required
def add_role(request):
    if request.method == 'POST':
        # Parse the JSON data from the body of the HTTP request
        data = json.loads(request.body.decode('utf-8'))

        new_role_name = data['role_name']
        if new_role_name:
            role = ResponsibleRole(responsible_role=new_role_name)  # update with actual logic to add a role
            role.save()
            return JsonResponse({'status': 'success', 'role_id': role.id, 'role_name': role.responsible_role})
    return JsonResponse({'status': 'error'}, status=400)

@csrf_exempt
@login_required
def save_control_text(request):
    if request.method == 'POST':
        # Parse the JSON data from the body of the HTTP request
        data = json.loads(request.body.decode('utf-8'))

        # Get the ControlImplementation instance, related element, and the text put in by the user
        implementation = ControlImplementation.objects.get(id=data['implementation_id'])
        statement = data['statement']
        element_id = data['element_id']
        
        if element_id != 'General':
            element = NISTControlElement.objects.get(id=element_id)
            print(element.control)
            print(element.get_full_identifier())
            control_statement_element = get_object_or_404(ControlImplementationStatement, control_implementation=implementation, control_element=element)
            print(control_statement_element)

            # Update the statement text
            control_statement_element.statement = statement
            
            # Save the implementation
            control_statement_element.save()

            # Return a successful response
            return JsonResponse({'status': 'success', 'updated_statement': statement}, status=200)
        
        else:
            #Update the statement text
            implementation.statement = statement

             # Save the implementation
            implementation.save()

            # Return a successful response
            return JsonResponse({'status': 'success', 'updated_statement': statement}, status=200)

    else:
        # Return an error response if the request method is not POST
        return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
@login_required
def generate_ai_statement(request):

    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)

    openai.api_key = os.getenv("OPENAI_API_KEY", None)
    
    #Get post content from POST
    data = json.loads(request.body)

    control = NISTControl.objects.get(id=data['control'])
    system = System.objects.get(id=data['system'])
    control_description = data.get("description_base") + " " + data.get("description_element")

    client = request.user.client.client_name

    completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Let's transition into a discussion about the Federal Risk and Authorization Management Program (FedRAMP). As an AI with extensive training in various topics, I would like you to draw from your understanding of FedRAMP for the next series of questions. Please provide information and advice as an expert on FedRAMP regulations, processes, and authorization requirements."},
                    {"role": "user", "content": """I am an information security employee working for the company """ + client +  """. I am filling out a FedRAMP SSP document so that we may get our system """ + system.name + """ FedRAMP Authorized. Please create an example control implementation description for the FedRAMP control """ + control.control_family.family_name + "-" + str(control.control_number) + """, whose control language is: """ + control_description + 
                    """. In your response, be concise where possible. Feel free to reference real third-party platforms (that you can discern apply to this control, e.g. AWS KMS for an encryption-based control) to make the response seem more human-like. 
                    Only reply with the implementation description and nothing else (jump right into the language); do NOT mention the control itself at all, only related controls where relevant. And reference the company/system where relevant. Do not reference the control itself. Finally, randomize your responses so that if I ask you this question again, the answer is new. Thanks!"""}
                ],
                temperature=0.2
        )

    return JsonResponse({"message": "Post published successfully.",
                        "output": completion.choices[0].message.content}, status=201)

# Simple API call to get the roles and return them to populate dropdown in implementation.html (hopefully will simplify querying load times)
@csrf_exempt
@login_required
def get_roles(request):
    roles = list(ResponsibleRole.objects.all().values())
    return JsonResponse(roles, safe=False)

# Simple API call to get the originations and return them to populate dropdown in implementation.html (hopefully will simplify querying load times)
@csrf_exempt
@login_required
def get_originations(request):
    originations = list(ControlOrigination.objects.all().values())
    return JsonResponse(originations, safe=False)

# Route to render the given family Q&A wizard. Pull the relevant questions
def questions(request, control_family_name=None):

    # Get all the questions for the given family, otherwise, just get all the questions
    if control_family_name:
        control_family = ControlFamily.objects.get(family_name=control_family_name)
        questions = Question.objects.filter(controls__control_family=control_family).distinct()
    else:
        questions = Question.objects.all()

    # Get all answers from the logged in client. Currently hardcoded to be just the first client in database ("Lotsa")
    answers = Answer.objects.filter(client="1")

    # Create a dictionary to store question_id and answer_text pairs
    client_answers = {answer.question.id: answer.answer_text for answer in answers}

    # Get all control families for the sidebar
    control_families = ControlFamily.objects.all()

    return render(request, "questions.html", {
        "questions": questions,
        "client_answers": client_answers,
        "control_families": control_families,
        "current_family_name": control_family_name
    })

# API Call to post answer content to database either as a new answer or new content to an existing answer
@csrf_exempt
def answer(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)
    
    #Get answer from POST
    data = json.loads(request.body)
    client = Client.objects.get(id="1")
    answer = data.get("answer")
    question_id = data.get("question")
    question_instance = Question.objects.get(id=question_id)

    # Try to get the existing answer or create a new one
    answer_instance, created = Answer.objects.get_or_create(client=client, question=question_instance)

    # Update the answer_text
    answer_instance.answer_text = answer
    answer_instance.save()
    
    # Once saved to database, return success message
    return JsonResponse({"message": "Answer saved successfully."}, status=201)

# API Call to get an answer from the database given a question id
@csrf_exempt
def get_answer(request):
    question_id = request.GET.get('question_id', None)
    if question_id is not None:

        try:
            answer = Answer.objects.get(question_id=question_id)
            return JsonResponse({'status': 'success', 'answer': answer.answer_text})
        except Answer.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Answer not found for the given question_id'})

    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request, question_id is required'})