from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_403_FORBIDDEN,
    HTTP_200_OK,
    HTTP_202_ACCEPTED,
    HTTP_500_INTERNAL_SERVER_ERROR
)
from rest_framework.response import Response
from django.shortcuts import render, redirect

from .utils import Utils, PostDataClass
from .decorators import superuser_only, token_required, video_token_required
from .tables import UserTable, SmartGlassTableChat, VideoUserTable
from .forms import LoginForm, AddNewUserForm, ModifyUserForm, \
    ChangePasswordForm, UserForgotPasswordForm, ResetPasswordForm
from .models import SmartGlass, User, VideoUser, UserWhitToken
from django.contrib.auth.tokens import default_token_generator
from django.db.models import Q
from django.template import loader
from django.core.mail import send_mail
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.urls import reverse
import json


# from video_chat.settings import EMAIL_SENDER


def handler404(request, *args, **kwargs):
    response = render(request, "error/404.html")
    response.status_code = 404
    return response


def handler500(request, *args, **kwargs):
    response = render(request, "error/500.html")
    response.status_code = 500
    return response


def handler403(request, *args, **kwargs):
    response = render(request, "error/403.html")
    response.status_code = 403
    return response


def handler400(request, *args, **kwargs):
    response = render(request, "error/400.html")
    response.status_code = 400
    return response


#
# @csrf_exempt
# @login_required()
# def home(request):
#     if request.user.is_superuser:
#         return redirect(user_list)
#     else:
#         return redirect(video_chat)
#
#
# def login_user(request):
#     button_text = 'LogIn'
#     if not User.objects.all().exists():
#         Utils.first_run()
#     state = ""
#     next = '/home/'
#     if request.method == 'GET':
#         if request.GET:
#             next = request.GET['next']
#
#     if request.POST or request.user.is_authenticated:
#         if not request.user.is_authenticated:
#             form = LoginForm(request.POST)
#             if form.is_valid():
#                 next = request.POST.get('next')
#                 username = form.cleaned_data.get('username')
#                 password = form.cleaned_data.get('password')
#                 user = authenticate(username=username, password=password)
#             else:
#                 state = 'Riprova! Dati errati'
#         else:
#             user = request.user
#         try:
#             user
#         except NameError:
#             user = None
#
#         if user:
#             last_login=user.last_login
#             login(request, user)
#             if  not last_login :
#                 request.session['next']=next
#                 return redirect('change_password')
#             return redirect(next)
#
#
#         else:
#             state = 'Riprova i dati non sono validi'
#     else:
#         form = LoginForm()
#     title= 'Login'
#     return render(request, 'accounts/login.html',
#                   {'next': next, 'state': state, 'form': form, 'button_text': button_text, 'title': title})
#
#
# def logout_user(request):
#     next = 'login'
#     if request.method == 'GET':
#          next = request.GET.get('next','login')
#     if request.user.is_authenticated:
#         request.user.save()
#     request.session.flush()
#     logout(request)
#     return redirect(next)
#
# @superuser_only
# @login_required()
# def new_user(request):
#     message = ''
#     if request.method == "POST":
#         form = AddNewUserForm(request.user, request.POST)
#         user = None
#         if form.is_valid():
#             user = form.save(commit=False)
#             user.set_password(user.password)
#             user.save()
#             if user:
#                 message = 'successo'
#                 return redirect('user', pk=user.pk)
#             else:
#                 message = 'Non hai sufficienti permessi'
#         else:
#             message = 'Non Valido'
#
#
#     else:
#         form = AddNewUserForm(request.user)
#
#     button_text = 'Registra'
#     return render(request, 'accounts/forms.html', {'form': form, 'state': message, 'button_text': button_text})
#
#
#
#
# @login_required()
# @superuser_only
# def user_list(request):
#     table = UserTable(User.objects.all())
#     table.paginate(page=request.GET.get('page', 1), per_page=25)
#     button = PostDataClass
#     button.text = 'Nuovo Utente'
#     button.link = reverse('new_user_registration')
#     button.classToAdd = 'btn-new-user'
#     page = 'user_tab'
#     delete_AJAX = reverse('delete_user_ajax')
#     return render(request, 'accounts/table.html', {'table': table, page: True, 'button': button, 'delete_AJAX':delete_AJAX})
#
#
# @login_required()
# @superuser_only
# def video_user_list(request):
#     table = VideoUserTable(VideoUser.allValid())
#     table.paginate(page=request.GET.get('page', 1), per_page=25)
#     page = 'video_user_tab'
#     return render(request, 'accounts/table.html', {'table': table, page: True})
#
#
#
#
# @login_required()
# def user_modify(request, pk):
#     if(request.user.is_superuser) or (request.user.pk == pk):
#         if request.user.pk == pk:
#             current_user=True
#             user = request.user
#         else:
#             current_user=False
#             user = get_object_or_404(User, pk=pk)
#         message = ''
#         if request.method == "POST":
#             if request.POST.get('modify') == 'True':
#                 form = ModifyUserForm(user=request.user, user_to_modify=user, disabled=False)
#                 button_text = 'Conferma'
#             else:
#                 form = ModifyUserForm(user=request.user, user_to_modify=user, disabled=False, data=request.POST)
#                 button_text = 'Conferma'
#                 if form.is_valid():
#                     user_to_save = form.save(commit=False)
#                     user.first_name=user_to_save.first_name
#                     user.last_name = user_to_save.last_name
#                     user.username = user_to_save.username
#                     user.email = user_to_save.email
#                     if not user.password == '':
#                         user.set_password(user_to_save.password)
#                     user.save()
#                     if current_user:
#                         login(request, user)
#                     message = 'successo'
#                     form = ModifyUserForm(user=request.user, user_to_modify=user, disabled=True)
#                     button_text = 'Modifica'
#                 else:
#                     message = 'Non Valido'
#         else:
#             form = ModifyUserForm(user=request.user, user_to_modify=user, disabled=True)
#             button_text = 'Modifica'
#         return render(request, 'accounts/forms.html', {'form': form, 'state': message, 'button_text': button_text})
#     else:
#         raise PermissionDenied
#
#
# @login_required()
# def change_password(request):
#     if request.method == "POST":
#         form = ChangePasswordForm(user=request.user,data=request.POST)
#         if form.is_valid():
#             password = form.cleaned_data.get('password')
#             request.user.set_password(password)
#             user= request.user.save()
#             login(request, user)
#             next =  request.session.pop('next','/auth/login/')
#             return redirect(next)
#         else:
#             state = 'errore'
#     else:
#         form = ChangePasswordForm(user=request.user)
#         state = ''
#     button_text = 'cambia'
#     return render(request, 'accounts/login.html',
#                   {'next': request.session.get('next',''), 'state': state, 'form': form, 'button_text': button_text})
#
#

# API


@login_required()
@superuser_only
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def delete_user_ajax(request):
    if request.method == 'POST':
        id_user = request.POST.get('id')
    if id_user != 1:
        try:
            u = User.objects.get(pk=id_user)
            u.delete()
            message = "The user is deleted"
            success = True
            status = HTTP_200_OK
        except User.DoesNotExist:
            message = "l'utente non esiste"
            success = False
            status = HTTP_400_BAD_REQUEST
        except Exception as e:
            message = e.message
            success = False
            status = HTTP_400_BAD_REQUEST
    else:
        message = "non puoi eliminare questo utete"
        success = False
        status = HTTP_400_BAD_REQUEST

    data = {
        'message': message,
        'success': success
    }
    return JsonResponse(data, status=status)


def reset_password(request):
    message = ''
    if request.method == "POST":
        form = UserForgotPasswordForm(request.POST)
        if form.is_valid():
            email_or_username = form.cleaned_data.get('email_or_username')
            users = User.objects.filter(Q(email=email_or_username) | Q(username=email_or_username))
            if users.exists():
                for user in users:
                    c = {
                        'base_url': settings.BASE_URL,
                        'link': user.linkResetPassword,
                        'user': user,
                        'token': default_token_generator.make_token(user),
                    }
                    subject_template_name = 'accounts/password_reset_subject.txt'
                    email_template_name = 'accounts/password_reset_email.html'
                    subject = loader.render_to_string(subject_template_name, c)
                    # Email subject *must not* contain newlines
                    subject = ''.join(subject.splitlines())
                    email = loader.render_to_string(email_template_name, c)
                    try:
                        send_mail(subject, email, EMAIL_SENDER, [user.email], fail_silently=False)
                    except:
                        print('send_mail error')
                        pass
            return redirect('login')
        else:
            message = 'Non Valido'
    else:
        form = UserForgotPasswordForm()
    button_text = 'resetta'
    title = 'Reset Password'
    return render(request, 'accounts/login.html',
                  {'form': form, 'state': message, 'button_text': button_text, 'title': title})


def password_reset_confirm(request, uidb64, token):
    user = User.getUserByTokenResetPassword(uidb64, token)
    if user:
        message = ''
        if request.method == "POST":
            form = ResetPasswordForm(request.POST)
            if form.is_valid():
                password = form.cleaned_data.get('password')
                user.set_password(password)
                user.save()
                login(request, user)
                message = 'success'
                return redirect('login')
            else:
                message = 'Non Valido'
        else:
            form = ResetPasswordForm()
        button_text = 'resetta'
        return render(request, 'accounts/login.html', {'form': form, 'state': message, 'button_text': button_text})
    return redirect('login')


@api_view(["POST"])
@permission_classes([AllowAny])
def api_login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    return JsonResponse({'data': {'token': '1234', 'login': 'Dere'}, 'message': '', "error": False}, status=HTTP_200_OK)


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
@video_token_required
def test_token(request):
    return Response({'data': {}, 'message': '', "error": False}, status=HTTP_200_OK)


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
# @video_token_required
def session(request):
    status = HTTP_200_OK
    with open('ice_servers.json') as f:
        ice_servers = json.load(f)
    data = {
        'result': 'SUCCESS',
        'ws_base_url': settings.WS_BASE_URL,
        'ws_system_url': settings.WS_SYSTEM_URL,
        'ice_servers': ice_servers
    }
    print(data)
    return JsonResponse(data, status=status)


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
@video_token_required
def api_user_info(request):
    return Response({"id": request.userWhitToken.id},
                    status=HTTP_200_OK)


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def api_smartglass_login(request):
    """ from random import randint

    count = UserWhitToken.objects.count()
    random = UserWhitToken.objects.all()[randint(0, count - 1)]

    return Response(
        {'data': {"id": random.pk, "token": random.key}, 'message': '', "error": False},
        status=HTTP_200_OK) """

    # token = Utils.get_token(request)
    # smartglass = UserWhitToken.create_smart_glass(token)
    # if smartglass:
    #     return Response(
    #         {'data': {"id": smartglass.pk, "token": smartglass.token()}, 'message': '', "error": False},
    #         status=HTTP_200_OK)
    # else:
    #     return Response({'data': {}, 'message': '', 'error': True}, status=HTTP_200_OK)

    # o1 = UserWhitToken.objects.get(pk=361).is_online
    # o2 = UserWhitToken.objects.get(pk=362).is_online
    # o3 = UserWhitToken.objects.get(pk=363).is_online
    # print(o1)
    # print(o2)
    # print(o3)
    print(request.data)
    try:
        smartglass = SmartGlass.objects.get(serial=request.data['serial'])
        smartglass.generate_token()
        smartglass.save()
        print({'data': {"id": smartglass.pk, "token": smartglass.key, 'message': '', "error": False}})
        return Response({'data': {"id": smartglass.pk, "token": smartglass.key, 'message': '', "error": False}},
                        status=HTTP_200_OK)
    except Exception as e:
        print(e)
        if settings.SMARTGLASS_REGISTRATION_TOKEN and request.data['token'] == settings.SMARTGLASS_REGISTRATION_TOKEN:
            try:
                new_smartglass = SmartGlass()
                new_smartglass.serial = request.data['serial']
                new_smartglass.creator = VideoUser.objects.filter(external_id=1, username='admin').first()
                new_smartglass.save()
                new_smartglass.generate_token()
                new_smartglass.save()
                print({'data': {"id": new_smartglass.pk, "token": new_smartglass.key, 'message': '', "error": False}})
                return Response({'data': {"id": new_smartglass.pk, "token": new_smartglass.key, 'message': '', "error": False}},
                                status=HTTP_200_OK)
            except Exception as e:
                print(e)
    print('no try catch')
    return Response({'data': {"id": '', "token": '', 'message': '', "error": False}}, status=HTTP_200_OK)




@api_view(["GET", "POST"])
@permission_classes([AllowAny])
@token_required
def generate_user_video_token(request):
    return Response(
        {'data': {"id": request.videouser.pk, "token": request.videouser.token(), 'link': request.videouser.link},
         'message': '', "error": False},
        status=HTTP_200_OK)


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def check_token(request):
    return Response({'data': {}, 'message': '', "error": False}, status=HTTP_200_OK)


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
@video_token_required
def generate_smartglass_video_token(request):
    if request.videouser:
        SmartGlass.generate_token(request.videouser)
        return Response({'data': {"token": request.videouser.generate_smartglss()}, 'message': '', "error": False},
                        status=HTTP_200_OK)
    else:
        return Response({}, status=HTTP_403_FORBIDDEN)


@video_token_required
def video_chat(request, token=None):
    if request.videouser:
        table = SmartGlassTableChat(SmartGlass.all_valid())
        base = 'base_external.html'
        token = request.videouser.key
        page = ''
    if table:
        return render(request, 'accounts/video_chat.html',
                      {'token': token, page: True, 'table': table, 'base': base})
    raise PermissionDenied


def home(request):
    import random
    import string

    # get random password pf length 8 with letters, digits, and symbols
    characters = string.ascii_letters + string.digits
    password = ''.join(random.choice(characters) for i in range(40))

    return redirect(settings.BASE_URL + 'video/api/video_chat_ext/?token=' + str(password))


@token_required
def video_chat_ext(request, token=None):
    # if request.session.get("user_role", None) is None:
    #     return redirect('/login/')
    # request.user = User.objects.get(pk=1)
    # # request.videouser = VideoUser.objects.get(pk=)
    #
    # print(request.videouser)
    if request.videouser:
        table = SmartGlassTableChat(SmartGlass.all_valid())
        base = 'base_external.html'
        token = request.videouser.key
        page = ''
    if table:
        return render(request, 'accounts/video_chat.html',
                      {'token': token, page: True, 'table': table, 'base': base})
    raise PermissionDenied


@api_view(["POST"])
@permission_classes([AllowAny])
def upload_file(request):
    if request.method == 'POST':
        file_obj = request.data['audio_data']

        import datetime
        titolo = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M") + '.wav'

        with default_storage.open(titolo, 'wb+') as destination:
            for chunk in file_obj.chunks():
                destination.write(chunk)

        return Response(
            {'data': {'OK'}, 'message': '', "error": False}, status=HTTP_200_OK)
