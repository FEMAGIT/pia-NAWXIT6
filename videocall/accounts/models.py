from django.db import models
from datetime import timedelta
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from django import utils
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
import requests


class Group(models.Model):
    name = models.CharField(max_length=100, unique=True, null=False)
    busy = models.BooleanField(null=False, default=False)
    calling = models.BooleanField(null=False, default=False)
    singleUser = models.BooleanField(null=False, default=False)

    def __str__(self):
        return self.name


class User(AbstractUser):

    # Title Name in list
    def __str__(self):
        return self.username

    @property
    def tokenResetPassword(self):
        return default_token_generator.make_token(self)

    @property
    def linkResetPassword(self):
        return settings.BASE_URL + reverse('password_reset_confirm', args=(
        urlsafe_base64_encode(force_bytes(self.pk)).decode('utf-8'), self.tokenResetPassword,))

    @staticmethod
    def getUserByTokenResetPassword(uidb64, token):
        uid = urlsafe_base64_decode(uidb64)
        user = User.objects.filter(pk=uid).first()
        if user and token and default_token_generator.check_token(user, token):
            return user
        else:
            return None


class UserWhitToken(models.Model):
    key = models.CharField(max_length=255)
    date_create = models.DateTimeField(default=timezone.now)
    date_expire = models.DateTimeField(max_length=40, unique=True, null=False)
    is_busy = models.BooleanField(default=False)
    is_online = models.BooleanField(default=False)
    is_calling = models.BooleanField(default=False)
    active = models.BooleanField(default=True)

    @property
    def name(self):
        return str(self.id)

    @staticmethod
    def create_smart_glass(token):
        if token:
            videouser = VideoUser.getVideoUserByToken(token)
            if videouser:
                smartglass = SmartGlass(creator=videouser)
                smartglass.generate_token()
                smartglass.save()
                return smartglass

            # from .utils import Utils
            # token = Utils.decode_data(token, settings.SECRET_KEY)
            # if token and 'iat' in token and 'creator' in token:
            #     videouser = VideoUser.objects.filter(id=token['creator']).first()
            #     if videouser:
            #         smartglass = SmartGlass(creator=videouser)
            #         smartglass.generate_token()
            #         smartglass.save()
            #         return smartglass
        return None

    def deactive(self):
        self.active = False
        self.key = None
        self.date_expire = timezone.now()
        self.save()

    def isTokenValid(self):
        if (self.key == None) or (self.date_expire < utils.timezone.now()) or self.active:
            if self.key != None:
                self.key = None
                self.save
            return False
        else:
            return True

    def generate_token(self, hour=8, force=False):
        from .utils import Utils
        if (not self.date_expire or self.date_expire < timezone.now() + timedelta(minutes=20) or force):
            # self.date_expire = timezone.now() + timedelta(hours=int(hour))
            self.date_expire = timezone.now() + timedelta(hours=99999)
            self.key = Utils.encode_data({'iat': timezone.now(), 'user': self.pk}, settings.SECRET_KEY).decode('utf-8')
        return self.key

    def regenerate_token(self, hour=8, force=False):
        self.generate_token(hour=hour, force=force)
        self.save()
        return self.key

    def token(self):
        if (self.key == None) or (self.date_expire < utils.timezone.now()):
            return self.regenerate_token()
        else:
            return self.key

    def save(self, *args, **kwargs):
        if (self.key == None) or self.date_expire == None or (self.date_expire < utils.timezone.now()):
            self.generate_token()
        super(UserWhitToken, self).save(*args, **kwargs)


class VideoUser(UserWhitToken):
    external_id = models.CharField(max_length=50, unique=False, null=False)
    username = models.CharField(max_length=50, unique=False, null=False)

    @property
    def name(self):
        return self.username

    @property
    def link(self):
        return settings.BASE_URL + reverse('video_chat', args=(self.key,))

    @property
    def is_authenticated(self):
        return True

    @classmethod
    def allValid(cls):
        return cls.objects.filter(date_expire__gt=timezone.now(), active=True).exclude(key=None)

    def generate_smartglss(self, exp=10):
        from .utils import Utils
        return Utils.encode_data({'iat': timezone.now(),
                                  'exp': timezone.now() + timedelta(minutes=exp),
                                  'creator': self.id},
                                 settings.SECRET_KEY).decode('utf-8')

    @classmethod
    def getVideoUserByToken(cls, token=None):
        # if token:
        #     response = requests.post(settings.BASE_URL + '/rest/is_token_valid/', json={'auth_token':token})
        #     if not response.json()['error']:
        #         video_user=cls(external_id=response.json()['data']['id'], username=response.json()['data']['login'])
        #         video_user.generate_token()
        #         video_user.save()
        #         return video_user
        # return None
        if token:
            video_user = cls(external_id=1, username="admin")
            video_user.generate_token()
            video_user.save()
            return video_user
        return None


class SmartGlass(UserWhitToken):
    serial = models.CharField(max_length=50, unique=False, null=True)
    date_join = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    creator = models.ForeignKey(to=VideoUser, on_delete=models.CASCADE, )

    def __str__(self):
        return self.name

    @property
    def name(self):
        return self.serial + '_smartglass'
        #if self.pk == 361:
            # return self.creator.username +'_smartglass'
        #    return 'occhialino 1'
        #elif self.pk == 362:
            # return self.creator.username +'_smartglass'
        #    return 'occhialino 2'
        #elif self.pk == 363:
            # return self.creator.username +'_smartglass'
        #    return 'occhialino 3'
        #else:
        #    return self.creator.username + '_smartglass'

    @classmethod
    def all_valid(cls):
        return cls.objects.filter(is_online=True)

# class Group(models.Model):
#    name = models.CharField(max_length=100, unique=True, null=False)
#    busy = models.BooleanField(null=False, default=False)
#    calling = models.BooleanField(null=False, default=False)
#    singleUser = models.BooleanField(null=False, default=False)

#    def __str__(self):
#        return self.name
