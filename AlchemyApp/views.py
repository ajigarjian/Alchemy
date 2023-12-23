import json #for api calls
import re
import random #for generating system color for client dashboard
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse #for API calls
from django.urls import reverse #for HttpResponseRedirect(reverse)
from django.contrib.auth import authenticate, login, logout #for login/logout/register
from django.views.decorators.csrf import csrf_exempt #for API calls
from django.contrib import messages #for register error message(s)
from .models import CustomUser, Client, ControlFamily, System, ControlImplementationStatement #for interacting with database
from .forms import OrganizationForm
from django.contrib.auth.backends import ModelBackend
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required #to redirect user to login route if they try to access an app page past login
from django.db.models import Count, Q, OuterRef, Exists
import os, openai
# from openai import OpenAI
from dotenv import load_dotenv #for access to .env variables, like OPENAI API key
from urllib.parse import unquote #to decode url strings passed through urls as parameters, e.g. client
from openpyxl.styles import Alignment
from openpyxl import load_workbook
from copy import copy
from django.conf import settings
from math import ceil
import xml.etree.ElementTree as ET
import zipfile
import tempfile
import shutil #for removing temporary directories once they are done being used

from .tasks import process_assessment_task #For celery task where AI assessment is performed
from celery.result import AsyncResult #for celery
from celery_progress.backend import ProgressRecorder #for celery

from langchain.document_loaders import PyPDFLoader #for taking relevant pdfs and loading them as langchain "document" objects
from langchain.document_loaders import Docx2txtLoader #for taking relevant word documents and loading them as langchain "document" objects
from langchain.text_splitter import CharacterTextSplitter #for taking langchain documents and splitting them into chunks (pre-processing for vector storage)
from langchain.embeddings.openai import OpenAIEmbeddings #for taking document chunks and embedding them as vectors for similarity searching
from langchain.vectorstores import FAISS #for storing the vector representations of document chunks, vectorizing the given query, and retrieving the relevant text via similarity search. Will not be long term solution
from langchain.chains import RetrievalQA #Langchain chain for distilling the retrieved document chunks into an human-like answer using an llm/chat model, like gpt-turbo-3.5
from langchain.chains.summarize import load_summarize_chain
from langchain.chains import LLMChain
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI #Importing langchain's abstraction on top of the OpenAI API
from langchain.prompts import PromptTemplate #for creating a prompt template that will provide context to user queries/other inputs to llm

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

def assess(request):

    # render assess.html

    return render(request, "public/assess.html")

@csrf_exempt
def generate_ai_assessment(request):

    #Initializing for celery for progress bar

    # Cannot call this API call to OpenAI unless via the file upload POSTing to backend
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)

    # Store the OpenAI API Key for future use
    openai_api_key = os.getenv("OPENAI_API_KEY", None)
    
    # Get the relevant info from the user (files, settings)
    uploaded_files = request.FILES.getlist('data_files')
    selected_framework = request.POST['selectedFramework']
    # selected_family = request.POST['selectedFamily']
    selected_model = request.POST['selectedModel']

    temp_files = []

    for uploaded_file in uploaded_files:
        if uploaded_file.multiple_chunks():
            return JsonResponse({"error": "Uploaded file is too big (%.2f MB)." % (uploaded_file.size/(1000*1000),)}, status=400)
        
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, uploaded_file.name)
        with open(temp_file_path, 'wb') as temp_file:
            for chunk in uploaded_file.chunks():
                temp_file.write(chunk)
        
        temp_files.append(temp_file_path)

    # ------------ MAIN PROCESSING AREA ------------------

    # Call the Celery task and wait for its result
    task_result = process_assessment_task.delay(temp_files)
    task_id = task_result.id

    print(f"processing task: {task_id}...")

    # Return the task ID to the frontend
    return JsonResponse({'task_id': task_id})

@csrf_exempt
def get_assessment_status(request, task_id):

    task = AsyncResult(task_id)

    # Initialize response_data at the beginning
    response_data = {}

    try:
        #If it's finished, grab the output zip file with the metrics and the updated test workbook, and send to the front end
        if task.successful():

            current_progress = task.result.get('current', 0)
            total = task.result.get('total', 0)

            print(f"\nTask {task_id}: {task.state} with {current_progress} out of {total} procedures assessed\n")

            # Grab the file paths for the excel workbook report and the metrics json from the task result
            workbook_file_path = task.result.get('workbook_file_path', None)
            metrics_file_path = task.result.get('metrics_file_path', None)

            # Generate URLs for the files to let the front end access the files
            workbook_url = settings.STATIC_URL + os.path.basename(workbook_file_path) if workbook_file_path else None
            metrics_url = settings.STATIC_URL + os.path.basename(metrics_file_path) if metrics_file_path else None

            # Construct the response data
            response_data = {
                'state': task.state,
                'workbook_url': workbook_url,
                'metrics_url': metrics_url
            }
        
        elif task.failed():
            # Handle failed task
            response_data = {
                'state': task.state,
                'error': str(task.info),  # Error details
            }

        #If it is still ongoing, send the ongoing status and details to the front end for the progress bar
        else:

            current_progress = task.result.get('current', 0)
            total = task.result.get('total', 0)

            print(f"\nTask {task_id}: {task.state} with {current_progress} out of {total} procedures assessed\n")
            
            response_data = {
                'state': task.state,
                'details': task.info if task.info else {}
            }
        
        return JsonResponse(response_data)

    except Exception as e:
        print(f"Error in get_assessment_status: {e}")
        return JsonResponse({'error': str(e)}, status=500)

####################################### Internal Application once logged in ##############################################

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