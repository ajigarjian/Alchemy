import json #for api calls
import re
import logging
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
from dotenv import load_dotenv #for access to .env variables, like OPENAI API key
from urllib.parse import unquote #to decode url strings passed through urls as parameters, e.g. client
from django.db.models.functions import Coalesce #for treating base controls with enhancements as null as high values 
from openpyxl.styles import Alignment
from openpyxl import load_workbook
from copy import copy
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
import shutil #for removing temporary directories once they are done being used

from langchain.document_loaders import PyPDFLoader #for taking relevant pdfs and loading them as langchain "document" objects
from langchain.document_loaders import Docx2txtLoader #for taking relevant word documents and loading them as langchain "document" objects
from langchain.text_splitter import CharacterTextSplitter #for taking langchain documents and splitting them into chunks (pre-processing for vector storage)
from langchain.embeddings.openai import OpenAIEmbeddings #for taking document chunks and embedding them as vectors for similarity searching
from langchain.vectorstores import FAISS #for storing the vector representations of document chunks, vectorizing the given query, and retrieving the relevant text via similarity search. Will not be long term solution
from langchain.chains import RetrievalQA #Langchain chain for distilling the retrieved document chunks into an human-like answer using an llm/chat model, like gpt-turbo-3.5
from langchain.chat_models import ChatOpenAI #Importing langchain's abstraction on top of the OpenAI API
from langchain.prompts import PromptTemplate #for creating a prompt template that will provide context to user queries/other inputs to llm

load_dotenv()
logger = logging.getLogger(__name__)

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

    # Store the OpenAI API Key for future use
    openai_api_key = os.getenv("OPENAI_API_KEY", None)
    
    # Get the relevant info from the user (files, settings)
    uploaded_files = request.FILES.getlist('data_files')
    selected_framework = request.POST['selectedFramework']
    selected_family = request.POST['selectedFamily']
    selected_model = request.POST['selectedModel']

    vectorstore = None

    for index, uploaded_file in enumerate(uploaded_files): # Loop through all uploaded files
        # If the file is too big, reject it
        if uploaded_file.multiple_chunks():
            return JsonResponse({"error": "Uploaded file is too big (%.2f MB)." % (uploaded_file.size/(1000*1000),)}, status=400)

        # Create a temporary file to save the uploaded data
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            for chunk in uploaded_file.chunks():
                temp_file.write(chunk)

        # Load the temporary file using the PyPDFLoader (if a PDF ) or a DocxLoader (if a Word document)
        if uploaded_file.name.endswith('.pdf'):
            loader = PyPDFLoader(temp_file.name)
        elif uploaded_file.name.endswith('.docx'):
            loader = Docx2txtLoader(temp_file.name)
        else:
            return JsonResponse({"error": "Unsupported file type."}, status=400)

        #chunk up the loaded document. Can tweak chunking parameters for optimal performance 
        text_splitter = CharacterTextSplitter(        
            separator = "\n",
            chunk_size = 1000,
            chunk_overlap  = 200,
            length_function = len,
        )

        pages = loader.load_and_split(text_splitter)

        if index == 0:
            # Take the first file's page chunks and store them as vector embeddings within FAISS vector storage.
            vectorstore = FAISS.from_documents(pages, OpenAIEmbeddings(openai_api_key=openai_api_key))
        
        else:
            # Add every subsequent file's page chunks into the initialized vector storage
            vectorstore.add_documents(pages)

    # Instantiate the llm we'll be using to analyze the documents using the user's selected OpenAI model
    llm = ChatOpenAI(model_name=selected_model, temperature=0, openai_api_key=openai_api_key)
    
    #Instantiate the query/answer chain we'll use with the llm and PDF's vector store for answering any questions about the document.
    qa_chain = RetrievalQA.from_chain_type(llm,retriever=vectorstore.as_retriever())

    template = """{organization} has implemented security processes based on the provided documents. Please analyze the documents against the following information security test procedure: {control_description}. For this test procedure, please respond with exactly each of the 4 items, with each prefaced by their "Analysis_Part" + the number of the section, e.g. "Analysis_Part1:" (without any introduction or explanation, just your analysis):

    1. Without any introduction or explanation, the snippets of the relevant sections of text that offer evidence to support that the test requirement is implemented. Include the page number, where possible. (if it is not at all applicable, do not provide anything);
    2. An analysis of how well the document(s) meets the requirements of the given test procedure;
    3. An implementation status based on 1. and 2. of "Pass", "Fail"; and
    4. If the status was deemend "Fail" in 3., then recommendations for control remediation. If it was deemed "Pass", then do not provide anything.
    """

    # """{organization} has implemented security processes based on the provided document. How well does the provided document meet the requirements of the following information security control: '{control_description}'. Please also provide recommendations for remediation if the control is not fully met."""
    prompt_template = PromptTemplate.from_template(template)

    document_org = qa_chain({"query": "What is the name of the organization that the document is for? Reply with the name and nothing else."})['result']

    #Pull the testing workbook
    static_path = settings.STATIC_ROOT if settings.STATIC_ROOT else settings.STATICFILES_DIRS[0]
    template_path = os.path.join(static_path, 'SRC_Innovation_Documents/FedRAMP Assessment Workbook.xlsx')

    # Load workbook and select the specific testing worksheet in the workbook
    workbook = load_workbook(filename=template_path)
    
    worksheet = workbook[selected_family]

    # Create a duplicate of the original workbook for output
    duplicate_workbook = copy(workbook)
    duplicate_worksheet = duplicate_workbook[selected_family]

    # Perform analysis based on the test procedures in the controls workbook, the prompt and QA chain, and update the duplicate workbook with the output
    procedure_results = assess_controls_in_workbook(worksheet, duplicate_worksheet, document_org, prompt_template, qa_chain)

    # -------------------- SECTION TO GET METRICS FROM FILLED OUT WORKBOOK FOR FRONT END ----------------

    # Dictionary to store the intermediate results
    control_intermediate = {}

    # Process each test procedure
    for procedure, data in procedure_results.items():
        
        status = data["result"] #Getting each procedure's pass/fail
        control_name = data["name"] #Getting each procedure's 'name' (really control name)
        control = procedure.rsplit('.', 1)[0] #Getting the control ID from each procedure ID

        # If control isn't in the intermediate dictionary yet, initialize it
        if control not in control_intermediate:
            control_intermediate[control] = {'Pass': 0, 'Fail': 0, 'Name': control_name}

        # Increase the count for the current status (either Pass or Fail) for the current control
        control_intermediate[control][status] += 1

    # Final dictionary for control results
    control_results = {}

    # Determine the final status for each control
    for control, statuses in control_intermediate.items():
        control_name = statuses.pop('Name')

        if statuses['Pass'] > 0 and statuses['Fail'] == 0:
            status = 'Implemented'
        elif statuses['Pass'] > 0 and statuses['Fail'] > 0:
            status = 'Partially Implemented'
        else:
            status = 'Not Implemented'
        
        control_results[control] = {
            'Name': control_name,
            'Status': status
        }
            
    # Metrics
    total_procedures = len(procedure_results)
    passed_procedures_count = sum(1 for data in procedure_results.values() if data["result"] == 'Pass')
    failed_procedures_count = total_procedures - passed_procedures_count

    total_controls = len(control_results)
    implemented_controls_count = sum(1 for data in control_results.values() if data['Status'] == 'Implemented')
    partially_implemented_controls_count = sum(1 for data in control_results.values() if data['Status'] == 'Partially Implemented')
    not_implemented_controls_count = total_controls - implemented_controls_count - partially_implemented_controls_count

    # Pack metrics into a dictionary to send to the frontend

    overview_metrics = {
        'control_results': control_results,
        'total_procedures': total_procedures,
        'passed_procedures_count': passed_procedures_count,
        'failed_procedures_count': failed_procedures_count,
        'total_controls': total_controls,
        'implemented_controls_count': implemented_controls_count,
        'partially_implemented_controls_count': partially_implemented_controls_count,
        'not_implemented_controls_count': not_implemented_controls_count
    }


    # ---------------------------------- SECTION TO TEMPORARILY SAVE OUTPUTS (METRICS & TESTING WORKBOOK) FOR FRONT END ---------------------

     # Create a temporary directory
    temp_dir = tempfile.mkdtemp()

    excel_file_path = os.path.join(temp_dir, "Assessment Workbook with Analysis.xlsx")

    # Save the testing workbook to a temporary file within a temporary directory
    duplicate_workbook.save(excel_file_path)

    # Save the metrics to a JSON file in the temporary directory
    json_file_path = os.path.join(temp_dir, "metrics.json")
    with open(json_file_path, 'w') as json_file:
        json.dump(overview_metrics, json_file)

    # Zip both files together
    zip_filename = "Assessment_and_Metrics.zip"
    zip_file_path = os.path.join(temp_dir, zip_filename)
    with zipfile.ZipFile(zip_file_path, 'w') as zipf:
        zipf.write(excel_file_path, os.path.basename(excel_file_path))
        zipf.write(json_file_path, os.path.basename(json_file_path))
    
    # Send the ZIP file as a response
    with open(zip_file_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type="application/zip")
        response['Content-Disposition'] = f'attachment; filename="{zip_filename}"'
    
    # Clean up the temporary directory
    shutil.rmtree(temp_dir)
    
    return response
    
    # # Read the saved workbook into memory
    # with open(temp_file_name, 'rb') as f:
    #     file_data = f.read()

    # # Remove the temporary file
    # os.remove(temp_file_name)

    # # Create an HTTP response with the file
    # response = HttpResponse(file_data, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    # response['Content-Disposition'] = 'attachment; filename="Assessment Workbook with Analysis.xlsx"'

    # return response

# Helper function to /generate_ai_assessment that takes in the worksheet, name of the organization, and the prompt template, and updates the workbook accordingly with the output of the analysis
def assess_controls_in_workbook(worksheet, duplicate_worksheet, organization_name, prompt_template, qa_chain):

    procedure_results = {}

    starting_row = 2

    # Count rows that have data for command line percentage updates
    total_rows = sum(1 for _ in worksheet.iter_rows(values_only=True))-1

    # Loop through each row in the testing workbook and populate the prompt template with the relevant variables
    for row_index, row in enumerate(worksheet.iter_rows(min_row=starting_row, values_only=True), start=starting_row): # Assuming your data starts from the second row (skipping header)
        
        #skip the row if it is empty
        if row_index >= 21:

            # Getting the current control description from this row in the spreadsheet
            control_description = row[4]

            # Querying the llm to perform a similarity search with the templated query against our vector store
            query = prompt_template.format(control_description=control_description, organization=organization_name)
            result = qa_chain({"query": query})

            # Storing the response string into separate variables by section to upload to different columns
            split_output = extract_parts(result['result'])

            #Taking the split output and populating each row's columns G through J with it
            column_index = 8

            for part in split_output:
                # Add the answer to the current column of the current row in the duplicate worksheet
                cell = duplicate_worksheet.cell(row=row_index, column=column_index, value=part)
                # Set wrap_text to True for the cell
                cell.alignment = Alignment(wrap_text=True)

                #If filling in the pass/fail Column I, then center the text in the cell horizontally and vertically
                if column_index == 10:
                    cell.alignment = Alignment(horizontal='center', vertical='center')

                # Move to the next column for the next loop
                column_index += 1

            procedure_id = row[2]
            procedure_name = row[3]
            procedure_result = duplicate_worksheet.cell(row=row_index, column=10).value

            procedure_results[procedure_id] = {
                "name": procedure_name,
                "result": procedure_result
            }

            # progress bar in command line
            print(f"{round(100*((row_index-1)/(total_rows)))}% complete")
    
    return procedure_results

# Helper function to /generate_ai_assessment that takes the output from the query to OpenAI from the similarity search, and splits it so that we can put the info into the right columns
def extract_parts(input_str):
    # Define the markers that we will use to split the text
    markers = ["Analysis_Part1:", "Analysis_Part2:", "Analysis_Part3:", "Analysis_Part4:"]
    
    # Initialize an empty list to hold the parts
    parts = []
    
    # Iterate through the markers to split the text
    for i in range(len(markers)):
        start_marker = markers[i]
        try:
            end_marker = markers[i + 1]
        except IndexError:
            end_marker = None
            
        if end_marker:
            # Find the indices of the start and end markers
            start_idx = input_str.index(start_marker) + len(start_marker)
            end_idx = input_str.index(end_marker)
            
            # Extract the part in between the markers and strip whitespace
            part = input_str[start_idx:end_idx].strip()
        else:
            # We are at the last marker; extract everything after it
            start_idx = input_str.index(start_marker) + len(start_marker)
            part = input_str[start_idx:].strip()
        
        # Append the part to the list
        parts.append(part)
        
    if len(parts) != 4:
        raise ValueError("Invalid input: Expected exactly 4 parts.")
        
    return tuple(parts)

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
def generate_cis(request):

    # Getting the current system for the CIS worksheet
    system_data = json.loads(request.body.decode('utf-8'))
    system_id = system_data['system_id']
    system = get_object_or_404(System, id=system_id)

    # Get the systems' control implementations
    control_implementations = ControlImplementation.objects.filter(system=system).select_related('control', 'control__control_family').order_by('control__control_family__family_abbreviation', 'control__control_number')

    #Pull the CIS template
    static_path = settings.STATIC_ROOT if settings.STATIC_ROOT else settings.STATICFILES_DIRS[0]
    template_path = os.path.join(static_path, 'SSP-Appendix-J-_CSO_-CIS-and-CRM-Workbook.xlsx')

    # Load workbook and select the specific worksheet in the workbook
    workbook = load_workbook(filename=template_path)
    worksheet = workbook['Moderate CIS Worksheet'] 

    # Define the mapping between column index and status
    status_col_map = {
        'Implemented': 2,  # 'B' column
        'Partially Implemented': 3,  # 'C' column
        'Planned': 4,  # 'D' column
        'Alternative Implementation': 5,  # 'E' column
        'Not Applicable': 6  # 'F' column
    }

    origination_col_map = {
        'Service Provider Corporate': 7,  # 'G' column
        'Service Provider System Specific': 8,  # 'H' column
        'Service Provider Hybrid': 9,  # 'I' column
        'Configured by Customer': 10,  # 'J' column
        'Provided by Customer': 11,  # 'K' column
        'Shared': 12,  # 'L' column
        'Inherited': 13  # 'M' column
    }
    
    center_aligned_style = Alignment(horizontal='center')

    # Iterate over control implementations in your database
    for control_imp in control_implementations:
        control_str = control_imp.control.str_SSP()  # Get the control string

        # Loop through the rows in the worksheet
        for row in worksheet.iter_rows(min_row=4, min_col=1, max_col=1):
            cell = row[0]
            if not cell.value: #If we've run through all of the controls, stop the loop
                break  # Stop the loop
            cell_value = re.sub(r'\([a-z]\)$', '', cell.value)  # Remove (a-z) from cell value
            if cell_value == control_str:
                # Loop over the implementation statuses
                for status in control_imp.statuses.all():
                    target_cell = worksheet.cell(row=cell.row, column=status_col_map[status.status])
                    # Mark the status column with 'x'
                    target_cell.value = 'x'
                    target_cell.alignment = center_aligned_style

                # Loop over the originations
                for origination in control_imp.originations.all():
                    target_cell = worksheet.cell(row=cell.row, column=origination_col_map[origination.origination])
                    # Mark the origination column with 'x'
                    target_cell.value = 'x'
                    target_cell.alignment = center_aligned_style

    # Save the populated workbook to a byte stream
    byte_stream = io.BytesIO()
    workbook.save(byte_stream)
    byte_stream.seek(0)

    # Upload the document to S3 and get the URL
    url = upload_doc_to_s3(byte_stream, system.name, 'cis')

    # Make sure to close the workbook after you are done with it.
    workbook.close()

    return JsonResponse({'url': url})

@csrf_exempt
@login_required
def generate_ssp(request):
    logger.info('Start generate_ssp')

    system_data = json.loads(request.body.decode('utf-8'))
    system_id = system_data['system_id']

    logger.info('Parsed system_id: %s', system_id)

    # Get system and control data
    system, control_to_role_status_origin, control_to_general, control_to_statements = get_system_and_control_data(system_id)

    logger.info('Got system and control data')

    # Create and edit the document
    byte_stream = create_and_edit_doc(system, control_to_role_status_origin, control_to_general, control_to_statements)

    logger.info('Converted new document to byte stream')

    # Upload the document to S3 and get the URL
    url = upload_doc_to_s3(byte_stream, system.name, 'ssp')

    logger.info('Uploaded document to s3')

    logger.info('End generate_ssp')

    return JsonResponse({'url': url})

# Responsible for fetching and organizing the system and control data as part of the overall SSP creation process
def get_system_and_control_data(system_id):
    system = get_object_or_404(System, id=system_id)

    control_implementations = ControlImplementation.objects.filter(system=system)\
        .select_related('responsible_role')\
        .prefetch_related('statuses', 'originations')\
        .defer('progress', 'last_updated')

    general_statements = ControlImplementation.objects.filter(system=system).select_related('control').all().order_by('id')
    control_statements = ControlImplementationStatement.objects.filter(control_implementation__system=system).select_related('control_implementation', 'control_element').all().order_by('id')

    control_to_general, control_to_statements = process_statements(general_statements, control_statements)
    control_to_role_status_origin = process_control_implementations(control_implementations)

    return system, control_to_role_status_origin, control_to_general, control_to_statements

# Responsible for processing the fetched data into the appropriate structure as part of overall SSP creation process
def process_statements(general_statements, control_statements):
    control_to_general = {}
    for general_statement in general_statements:
        control_to_general[general_statement.control.str_SSP()] = general_statement

    control_to_statements = defaultdict(list)
    for control_statement in control_statements:
        control_to_statements[control_statement.control_implementation.control.str_SSP()].append(control_statement)

    return control_to_general, control_to_statements

# Responsible for processing the fetched data into the appropriate structure as part of overall SSP creation process
def process_control_implementations(control_implementations):
    control_to_role_status_origin = {}
    for control_implementation in control_implementations:
        control_full_id = control_implementation.control.str_SSP()
        control_to_role_status_origin[control_full_id] = {
            'role': control_implementation.responsible_role.responsible_role if control_implementation.responsible_role else None,
            'status': {status.status for status in control_implementation.statuses.all()},
            'origin': {origination.origination for origination in control_implementation.originations.all()}
        }

    return control_to_role_status_origin

# Responsible for loading, editing, and saving the Word document as part of overall SSP creation process
def create_and_edit_doc(system, control_to_role_status_origin, control_to_general, control_to_statements):
    
     # Load the Word document from static files
    static_path = settings.STATIC_ROOT if settings.STATIC_ROOT else settings.STATICFILES_DIRS[0]
    template_path = os.path.join(static_path, 'SSP-Appendix-A-Moderate-FedRAMP-Security-Controls.docx')
    doc = Document(template_path)

     # Get the current date
    current_date = datetime.date.today()
    # Convert the date to the desired string format
    date_string = current_date.strftime("%m/%d/%Y")

    # Updating the header of SSP appendix with CSO name, CSP name, and date
    table = doc.sections[0].header.tables[0]
    header_run = table.rows[0].cells[1].paragraphs[1].runs[0]
    header_run.clear()
    header_run.text = f'{system.client.client_name}  |  {system.name}  |  <Insert Version X.X>  |  {date_string}'

    # Loop through each table in the document
    for table in doc.tables:
        # We're assuming the control identifier is in the text of the first cell of the first row
        control_identifier = table.rows[0].cells[0].text.strip().split(' ')[0]  # taking first word as the control identifier

        # Check if this control identifier is in our dictionary
        if control_identifier in control_to_role_status_origin:
            
            record = control_to_role_status_origin[control_identifier]

            responsible_role = record['role']
            statuses = record['status']
            originations = record['origin']

            # Populate the responsible role cell (the cell to the right of "Responsible Role:")
            # First, find the cell with "Responsible Role:"
            for row in table.rows:
                for cell in row.cells:
                    if "Responsible Role:" in cell.text:
                        # Once we found it, we clear the cell and then set it to "Responsible Role: <the_role>"
                        cell.text = ""
                        paragraph = cell.paragraphs[0]
                        if responsible_role == None:
                            run = paragraph.add_run("Responsible Role:")
                        else:
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
                    for control_full_id in control_to_statements.keys():
                        control_statements = control_to_statements[control_full_id]

                        for control_statement in control_statements:
                            element_identifier = control_statement.control_element.get_full_identifier()

                            if control_full_id == control_identifier and element_identifier == control_element_identifier:

                                # Trim trailing whitespace
                                statement = control_statement.statement.rstrip()

                                # print(control_full_id, " matches ", control_identifier, " and ", element_identifier, " matches ", control_element_identifier, ": ", statement)

                                # Clear the cell and add the new text
                                cell = row.cells[0]
                                cell.text = ""
                                paragraph = cell.paragraphs[0]
                                run = paragraph.add_run("Part " + control_element_identifier + ": " + statement)
                                run.font.name = 'Times New Roman'  # change this to your preferred font
                                run.font.size = Pt(12)

            else:
                # Replace the implementation statement cell if the control element identifier exists in your dictionary
                for control_full_id in control_to_general.keys():
                    
                    if control_full_id == control_identifier:
                        statement = control_to_general[control_full_id].statement

                        # Trim trailing whitespace
                        statement = statement.rstrip()

                        # Clear the cell and add the new text
                        cell = row.cells[0]
                        cell.text = ""
                        paragraph = cell.paragraphs[0]
                        run = paragraph.add_run(statement)
                        run.font.name = 'Times New Roman'  # change this to your preferred font
                        run.font.size = Pt(12)

    # Save the populated document to a byte stream
    byte_stream = io.BytesIO()
    doc.save(byte_stream)
    byte_stream.seek(0)

    # Create a zipfile from the byte stream
    with zipfile.ZipFile(byte_stream, 'a') as myzip:
        # Extract the XML file to memory
        with myzip.open('word/document.xml') as f:
            tree = ET.parse(f)

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

    # Reset the position of byte_stream to the start
    byte_stream.seek(0)

    return byte_stream

#Responsible for uploading the generated document to S3.
def upload_doc_to_s3(byte_stream, system_name, doc_type):
    if doc_type == 'ssp':
        extension = 'docx'
    elif doc_type == 'cis':
        extension = 'xlsx'
    else:
        raise ValueError(f"Invalid doc_type {doc_type}")

    # Using AWS Boto3 API to store and retrieve file in S3 bucket

    # Generating random session key
    current_time=int(time.time())
    session_name = f'ari@alchemyssp.com-{current_time}'

    #Creating session for an AWS role via boto3user
    sts_client = boto3.client('sts', 
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", None),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", None))

    assumed_role_object=sts_client.assume_role(
        RoleArn="arn:aws:iam::814564129989:role/s3-generate-ssp-role",
        RoleSessionName=session_name
    )
    creds = assumed_role_object['Credentials']

    # Upload the document to S3 and generate a presigned URL using the temporary session credentials
    try:
        s3 = boto3.client('s3', 
            aws_access_key_id=creds['AccessKeyId'],
            aws_secret_access_key=creds['SecretAccessKey'],
            aws_session_token=creds['SessionToken'],
            config=Config(signature_version='v4', region_name=os.getenv("AWS_DEFAULT_REGION", None)))

        filename = f'{system_name}_{doc_type}.{extension}'
        s3.upload_fileobj(
            byte_stream, 
            'alchemyssp-moderate-ssp-reports',
            filename)

        # Generate the URL to get 'key-name' from 'bucket-name'
        url = s3.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': 'alchemyssp-moderate-ssp-reports',
                'Key': filename
            },
            ExpiresIn=120,  # 2 minutes
        )

        return url
    except Exception as e:
        print(e)
        return None

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

# View that takes in a string (a user's query) and returns a response from the OpenAI gpt-3.5-turbo, prompted as a FedRAMP expert
@csrf_exempt
@login_required
def generate_chat_response(request):

    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)

    openai.api_key = os.getenv("OPENAI_API_KEY", None)
    
    #Get post content from POST
    data = json.loads(request.body)

    user_prompt = data.get('user_prompt')

    completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": """Let's transition into a discussion about the Federal Risk and Authorization Management Program (FedRAMP). As an AI with extensive training in various topics, I would like you to draw from your understanding of FedRAMP for the next series of questions. Please provide information and advice as an expert on FedRAMP regulations, processes, and authorization requirements. Only give responses for exactly the question answered - no more."""},
                    {"role": "user", "content": """I am an information security employee. I am filling out a FedRAMP SSP document so that we may get our system FedRAMP Authorized. Not knowing FedRAMP too well, here is a question I have: """ + user_prompt + """."""}
                ],
                temperature=0.2
        )

    return JsonResponse({"message": "Post published successfully.",
                        "output": completion.choices[0].message.content}, status=201)

# View that takes in info about a company, its system, the control it wants a statement for, and returns a response from the OpenAI gpt-3.5-turbo model, prompted as a FedRMAP expert
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