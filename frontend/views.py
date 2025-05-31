from django.shortcuts import render

# Create your views here.
def operator_panel(request):
    return render(request, "operator.html")