from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.db.models import F
from django.contrib.auth.decorators import login_required
from . import models
from .models import Question, Choice

def index(request):
    latest_question_list = models.Question.objects.order_by('-pub_date')[:5]
    context = {'latest_question_list': latest_question_list}
    return render(request, 'index.html', context)

@login_required
def detail(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    user_choice = question.choice_set.filter(users=request.user).first()

    if request.method == 'POST':
        choice_id = request.POST.get('choice')
        if choice_id:
            choice = get_object_or_404(Choice, pk=choice_id)
            if not user_choice:
                choice.votes += 1
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