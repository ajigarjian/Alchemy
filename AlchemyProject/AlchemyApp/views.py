import json #for api calls
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.http import JsonResponse #for API calls
from django.urls import reverse #for HttpResponseRedirect(reverse)
from django.contrib.auth import authenticate, login, logout #for login/logout/register
from django.views.decorators.csrf import csrf_exempt #for API calls
from django.contrib import messages #for register error message(s)
from django.shortcuts import redirect
from .models import CustomUser, Client, NISTControl, Question, Answer, ControlFamily, InformationCategory, InformationSubCategory, System #for interacting with database
from .forms import OrganizationForm

# Route to render the landing page
def index(request):
    return render(request, "index.html")

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
            return HttpResponseRedirect(reverse("alchemy:overview"))
        else:
            context = {
                'error_message': 'Invalid email or password.',
            }

            return render(request, "login.html", context)

    # if not a POST request, show the login page
    return render(request, "login.html")

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
        login(request, user)
        return redirect('alchemy:index')

    return render(request, 'register.html', {
        "clients": Client.objects.all()
    })

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("alchemy:index"))

def contact(request):
    return render(request, "contact.html")

def overview(request):

    # if the user isn't logged in, they can't access the home page - redirect them to the login page
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("alchemy:login"))

    information_types = InformationCategory.objects.prefetch_related('informationsubcategory_set').all()

    return render(request, "overview.html", {
        "information_types": information_types,
        "organization": request.user.client,
        "org_form": OrganizationForm()
    })

@csrf_exempt
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