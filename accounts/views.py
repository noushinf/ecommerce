from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .models import *
from core.models import Customer
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

# Create your views here.


def user_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        #email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')
        messages.info(request,"login faild ,please try again")

    return render(request, 'accounts/login.html')


def user_register(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        conform_password = request.POST.get('conform_password')
        email = request.POST.get('email')
        phone = request.POST.get('phone_field')
        print(username, phone)
        if password == conform_password:
            if User.objects.filter(username=username).exists():
                messages.info(request, "user already exist")
                return redirect('user_register')

            else:
                if User.objects.filter(email=email).exists():
                    messages.info(request, "email already exist")
                    return redirect('user_register')

                else:
                    user = User.objects.create_user(username=username, password=password, email=email)
                    print(user, phone)
                    user.save()
                    data = Customer(user=user, phone_field=phone)
                    data.save()
                    print(data)
                    # core for login
                    our_user = authenticate(username=username, password=password)
                    print(our_user)
                    if our_user is not None:
                        login(request, user)
                        return redirect('/')

        else:
            messages.info(request, "password and confirm password missmatch")
            print('error register')
            return redirect('user_register')

    return render(request, 'accounts/register.html')


def user_logout(request):
    logout(request)
    return redirect('/')
