from django.shortcuts import render
from . import models

def index(request):
    latest_question_list = models.Question.objects.order_by('-pub_date')[:5]
    context = {'latest_question_list': latest_question_list}
    return render(request, 'index.html', context)

def detail(request, question_id):
    question = models.Question.objects.get(pk=question_id)
    return render(request, 'detail.html', {'question': question})

def results(request, question_id):
    question = models.Question.objects.get(pk=question_id)
    return render(request, 'results.html', {'question': question})