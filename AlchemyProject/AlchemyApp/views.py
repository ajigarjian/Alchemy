import json #for api calls
import random #for generating system color for client dashboard
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.http import JsonResponse #for API calls
from django.urls import reverse #for HttpResponseRedirect(reverse)
from django.contrib.auth import authenticate, login, logout #for login/logout/register
from django.views.decorators.csrf import csrf_exempt #for API calls
from django.contrib import messages #for register error message(s)
from .models import CustomUser, Client, NISTControl, NISTControlPart, Question, Answer, ControlFamily, InformationCategory, InformationSubCategory, System, ControlImplementation, ControlImplementationStatement, ImplementationStatus, ControlOrigination, ResponsibleRole #for interacting with database
from .forms import OrganizationForm, SystemForm
from django.contrib.auth.backends import ModelBackend
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required #to redirect user to login route if they try to access an app page past login
from django.db.models import Count, Q, Max
from django.db.models import Subquery
from django.core import serializers

import os, openai
from dotenv import load_dotenv

load_dotenv()

####################################### Public Application when not logged in ##############################################

# Route to render the landing page
def index(request):

    if not request.user.is_authenticated:

        return render(request, "public/index.html")
    
    else:
        return HttpResponseRedirect(reverse("alchemy:dashboard", args=[request.user.client]))

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
            return HttpResponseRedirect(reverse("alchemy:dashboard", args=[request.user.client]))
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
         return HttpResponseRedirect(reverse("alchemy:dashboard", args=[request.user.client]))
    return render(request, "public/contact.html")

####################################### Internal Application once logged in ##############################################

@csrf_exempt
@login_required
def implementation(request, system):

    client = request.user.client
    system_object = get_object_or_404(System, name=system, client=client)
    control_implementations = ControlImplementation.objects.filter(system=system_object).order_by('control')

    # Case where the search has been updated and an AJAX Call has been POSTed. This branch updates the control implementations rendered
    if request.method == 'POST':

        # Load the AJAX call data for each of the search filters
        data = json.loads(request.body)
        
        role = data.get('role')
        origination_statuses = data.get('origination_statuses')
        implementation_statuses = data.get('implementation_statuses')
        control_family_name = data.get('family')

        # For each search filter, check if data exists. If it does, filter the control implementations accordingly.
        if role:
            role_object = get_object_or_404(ResponsibleRole, responsible_role=role)
            control_implementations = control_implementations.filter(responsible_role=role_object)

        if origination_statuses:
            control_implementations = control_implementations.filter(originations__origination__in=originations_statuses)

        if implementation_statuses:
            control_implementations = control_implementations.filter(statuses__status__in=implementation_statuses)

        if family:
            control_family = get_object_or_404(ControlFamily, name=control_family_name)
            control_implementations = control_implementations.filter(control_family=control_family)
        
        serialized_data = ImplementationSerializer(implementations, many=True).data

        return JsonResponse(serialized_data, safe=False)

    # Case where the page is initially rendered from the dashboard with all controls being rendered for a given system
    else:

        implementation_choices = ImplementationStatus.objects.all()
        origination_choices = ControlOrigination.objects.all()
        implementation_statements = ControlImplementationStatement.objects.all()
        roles = ResponsibleRole.objects.all().distinct()

    # Get all the questions for the given family, otherwise, just get all the questions

        # Get all control families for the sidebar
        control_families = ControlFamily.objects.all().order_by('family_abbreviation')

        return render(request, "internal/implementation.html", {
            "system": system_object,
            "control_implementations": control_implementations,
            "implementation_choices": implementation_choices,
            "origination_choices": origination_choices,
            "control_families": control_families,
            "roles": roles,
            "implementation_statements": implementation_statements,
        })
    


# Handles showing dashboard page (for GET) as well as creating new systems before showing dashboard page again (for POST)
@login_required
def dashboard(request, client, system=None):
    
    systems = System.objects.filter(client__client_name=client)

    if (request.method == 'POST') & (request.POST.get("system_name") != None):

        colors = ['3E4756', '97ACCF', 'FFE1E9', 'CAAAB2', '6E7788', '5A3F46', '8D6F77', 'A2ACBD', 'CF9EAA', '986A76', '564147', 'CF9EAC', 'F3E7D0', 'BBB099', 'BEA5AB', 'BBB19B', '867D67']

        # process the data for new system. Use the client of the logged in user, and choose a random color
        system_name = request.POST.get("system_name")
        client_object = Client.objects.get(client_name=client)
        color = random.choice(colors)

        # Try to make a new system, if not possible, it's due to the system already existing
        try:
            system = System.objects.create(name=system_name, client=client_object, color=color)
            system.save()

        except IntegrityError:
            return render(request, "dashboard.html", {
                "message": "Email already being used."
            })

        return HttpResponseRedirect(reverse("alchemy:dashboard", args=[client]))
    
    else:
        if system is None:
            return render(request, "internal/dashboard.html", {
                "client": client,
                "systems": systems
            })
        else:
            selected_system = get_object_or_404(System, name=system, client__client_name=client)

            families = ControlFamily.objects.all().order_by('family_abbreviation').annotate(
                completed_controls_count=Count('controlimplementation', filter=Q(controlimplementation__progress='Completed')),
                family_controls_count=Count('controlimplementation'),
                last_updated=Max('controlimplementation__last_updated'),
            )
            
            # Using __ to make a lookup that spans relationship
            total_not = ControlImplementation.objects.filter(system=selected_system, statuses__status='Not Implemented').count()
            total_partial = ControlImplementation.objects.filter(system=selected_system, statuses__status='Partially Implemented').count()
            total_implemented = ControlImplementation.objects.filter(system=selected_system, statuses__status='Implemented').count()

            # For counting all the controls we count the implementations where status is one of the status choices
            total_controls = ControlImplementation.objects.filter(
                system=selected_system, 
                statuses__status__in=ImplementationStatus.STATUS_CHOICES
            ).count()

            total_completed_implementations = ControlImplementation.objects.filter(system=selected_system, progress='Completed').count()

            return render(request, "internal/system_dashboard.html", {
                "client": client,
                "system": selected_system,
                "families": families,
                "total_controls": total_controls,
                "total_completed_implementations": total_completed_implementations,
                "total_not": total_not,
                "total_partial": total_partial,
                "total_implemented": total_implemented
            })

@login_required
def delete_system(request):

    client = request.user.client

    if request.method == 'POST':
        system_name = request.POST['delete-system-button']
        system = get_object_or_404(System, name=system_name, client=client)
        system.delete()

    return redirect('alchemy:dashboard', client=client)

@login_required
def rename_system(request):

    client = request.user.client

    if request.method == 'POST':
        old_system_name = request.POST['change-name-button']
        new_system_name = request.POST['system_name']

        system = get_object_or_404(System, name=old_system_name, client=client)
        system.name = new_system_name
        system.save(update_fields=["name"])

    return redirect('alchemy:dashboard', client=client)

@login_required
def overview(request, system):

    org = request.user.client
    selected_system = get_object_or_404(System, name=system, client__client_name=org)

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

        # Get the ControlImplementation instance, related part, and the text put in by the user
        implementation = ControlImplementation.objects.get(id=data['implementation_id'])
        statement = data['statement']
        data_part = data['part_id']
        
        if data_part != 'General':
            part = NISTControlPart.objects.get(id=data['part_id'])
            control_statement_part = get_object_or_404(ControlImplementationStatement, control_implementation=implementation, control_part=part)

            # Update the statement text
            control_statement_part.statement = statement
            
            # Save the implementation
            control_statement_part.save()

            print(statement)

            # Return a successful response
            return JsonResponse({'status': 'success', 'updated_statement': statement}, status=200)
        
        else:
            #Update the statement text
            implementation.statement = statement

             # Save the implementation
            implementation.save()

            print(statement)

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
    control_description = data.get("description_base") + " " + data.get("description_part")

    client = request.user.client.client_name

    completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Let's transition into a discussion about the Federal Risk and Authorization Management Program (FedRAMP). As an AI with extensive training in various topics, I would like you to draw from your understanding of FedRAMP for the next series of questions. Please provide information and advice as an expert on FedRAMP regulations, processes, and authorization requirements."},
                    {"role": "user", "content": """I am an information security employee working for the company """ + client +  """. I am filling out a FedRAMP SSP document so that we may get our system """ + system.name + """ FedRAMP Authorized. Please create an example control implementation description for the FedRAMP control """ + control.control_family.family_name + "-" + str(control.control_number) + """, whose control language is: """ + control_description + 
                    """. In your response, be concise where possible. Feel free to reference real third-party platforms (that you can discern apply to this control, e.g. AWS KMS for an encryption-based control) to make the response seem more human-like. 
                    Only reply with the implementation description and nothing else (jump right into the language) - and reference the company/system where relevant. Do not reference the control itself. Finally, randomize your responses so that if I ask you this question again, the answer is new. Thanks!"""}
                ],
                temperature=0.2
        )

    return JsonResponse({"message": "Post published successfully.",
                        "output": completion.choices[0].message.content}, status=201)

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