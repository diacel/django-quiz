from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.db.models import F
from django.contrib.auth.decorators import login_required
from . import models
from .models import Question, Choice
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.forms import modelformset_factory
from .models import Quiz
from .forms import CustomUserCreationForm
from django.forms import formset_factory
from django import forms
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404

def index(request):
    latest_quiz_list = Quiz.objects.order_by('-created_at')[:5]
    context = {'latest_quiz_list': latest_quiz_list}
    return render(request, 'index.html', context)

class ChoiceForm(forms.Form):
    choice_text = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

@login_required
def detail(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    user_choice = question.choice_set.filter(users=request.user).first()

    if request.method == 'POST' and not user_choice:
        choice_id = request.POST.get('choice')
        if choice_id:
            choice = get_object_or_404(Choice, pk=choice_id)
            choice.votes = F('votes') + 1
            choice.users.add(request.user)
            choice.save()
            return redirect('detail', question_id=question_id)

    context = {
        'question': question,
        'user_choice': user_choice,
    }
    return render(request, 'detail.html', context)

def vote(request, question_id):
    question = get_object_or_404(models.Question, pk=question_id)
    
    # Проверяем, голосовал ли уже пользователь
    if f'voted_for_question_{question_id}' in request.session:
        return render(request, 'detail.html', {
            'question': question,
            'error_message': "You have already voted for this question.",
        })
    
    try:
        selected_choice = question.choice_set.get(pk=request.POST['choice'])
    except (KeyError, models.Choice.DoesNotExist):
        # Повторно отображаем форму голосования
        return render(request, 'detail.html', {
            'question': question,
            'error_message': "You didn't select a choice.",
        })
    else:
        # Используем F() для атомарного обновления
        selected_choice.votes = F('votes') + 1
        selected_choice.save()
        
        # Помечаем в сессии, что пользователь проголосовал
        request.session[f'voted_for_question_{question_id}'] = True
        
        # Важно: после использования F() нужно обновить объект из базы данных
        selected_choice.refresh_from_db()
        
        return redirect('results', question_id=question.id)

def results(request, question_id):
    question = get_object_or_404(models.Question, pk=question_id)
    return render(request, 'results.html', {'question': question})

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome, {username}! You have been logged in.")
                return redirect('index')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, "login.html", {"form": form})

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')  # или куда вы хотите перенаправить после регистрации
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

def user_logout(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('index')

@login_required
def create_quiz(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        quiz = Quiz.objects.create(title=title, creator=request.user)
        return redirect('add_question', quiz_id=quiz.id)
    return render(request, 'create_quiz.html')

@login_required
def add_question(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, creator=request.user)
    
    if request.method == 'POST':
        question_text = request.POST.get('question_text')
        num_choices = int(request.POST.get('num_choices', 2))
        
        ChoiceFormSet = formset_factory(ChoiceForm, extra=num_choices)
        formset = ChoiceFormSet(request.POST)
        
        if formset.is_valid():
            question = Question.objects.create(quiz=quiz, question_text=question_text)
            for form in formset:
                if form.cleaned_data.get('choice_text'):
                    Choice.objects.create(
                        question=question,
                        choice_text=form.cleaned_data['choice_text']
                    )
            
            if 'add_more' in request.POST:
                return redirect('add_question', quiz_id=quiz.id)
            else:
                return redirect('quiz_detail', quiz_id=quiz.id)
    else:
        ChoiceFormSet = formset_factory(ChoiceForm, extra=2)
        formset = ChoiceFormSet()
    
    return render(request, 'add_question.html', {
        'quiz': quiz,
        'formset': formset
    })

@login_required
def quiz_detail(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    questions = quiz.questions.all()  # This will work now
    return render(request, 'quiz_detail.html', {'quiz': quiz, 'questions': questions})

def quiz_detail_public(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    message = "Пожалуйста, зарегистрируйтесь, чтобы увидеть детали квиза."
    return render(request, 'quiz_detail_public.html', {'quiz': quiz, 'message': message})