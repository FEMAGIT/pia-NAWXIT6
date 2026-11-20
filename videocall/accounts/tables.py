import django_tables2 as tables
from .models import User, SmartGlass,VideoUser
from django.utils.safestring import mark_safe




class DeleteButton(tables.Column):
    empty_values = list()

    def render(self, value, record):
        self.accessor = "pk"
        self.orderable=False
        #return self.render(self, value, record)
        return mark_safe(
            '<button type="submit" class=" delete btn btn-sm btn-responsive btn-delete"> Cancella</button>')

class SendMailButton(tables.Column):
    empty_values = list()

    def render(self, value, record):
        self.accessor = "pk"
        self.orderable = False
        # return self.render(self, value, record)
        if record.email:
            return mark_safe(
                '<button type="submit" class=" send_mail btn btn-sm btn-responsive btn-send-mail"> Invia Link Via Mail</button>')
        else:
            return ''


class CustomButtonChat(tables.Column):
    empty_values = list()

    def __init__(self, classForJS="",button_text="",classToAdd="", *args, **kwargs):
        super(CustomButtonChat, self).__init__(*args, **kwargs)
        self.classForJS = classForJS
        self.button_text = button_text
        self.classToAdd = classToAdd

    def render(self, value, record):
        self.orderable=False
        #return self.render(self, value, record)
        return mark_safe(
            '<button type="submit" class="btn btn-sm btn-responsive ' + self.classForJS +' '+self.classToAdd+'" >'+self.button_text+'</button>')



class CustomButton(tables.Column):
    empty_values = list()

    def __init__(self, base_link="",button_text="",classToAdd="", *args, **kwargs):
        super(CustomButton, self).__init__(*args, **kwargs)
        self.base_link = base_link
        self.button_text = button_text
        self.classToAdd = classToAdd

    def render(self, value, record):
        link = str(record.pk)
        #return mark_safe('<input type="submit" class="edit btn btn-primary btn-lg" value="'+self.button_text+'" onclick="location.href= \'' + self.base_link + link +'\';">')
        return mark_safe(
            '<button type="submit" class="btn btn-sm btn-responsive '+self.classToAdd+'"  onclick="location.href= \'' + self.base_link + link +'\';" >'+self.button_text+'</button>')



class CustomButtonDisable(tables.Column):
    empty_values = list()

    def __init__(self, base_link="",button_text="",classToAdd="", *args, **kwargs):
        super(CustomButtonDisable, self).__init__(*args, **kwargs)
        self.base_link = base_link
        self.button_text = button_text
        self.classToAdd = classToAdd

    def render(self, value, record):
        link = str(record.pk)
        if record.registered:
            disabled='disabled'
        else:
            disabled =''
        return mark_safe(
            '<button type="submit" class="btn btn-sm btn-responsive '+self.classToAdd+'" '+ disabled +' onclick="location.href= \'' + self.base_link + link +'\';" >'+self.button_text+'</button>')



class ButtonsList(tables.Column):
    empty_values = list()
    attrs = {'td': {'valign': 'top'}}

    def __init__(self, button=None, *args, **kwargs):
        super(ButtonsList, self).__init__(*args, **kwargs)
        self.buttonsList = []
        if button:
            self.buttonsList.append(button)

    def append(self, button=None):
        if button:
            self.buttonsList.append(button)


    def render(self, value, record):
        self.accessor = "pk"
        self.orderable=False
        #return self.render(self, value, record)
        html=''
        for x in self.buttonsList:
            html = html + x.render(value, record)
        return mark_safe(html)




class UserTable(tables.Table):
    is_active = tables.BooleanColumn(attrs={'td': {'align': 'center'}})
    is_superuser = tables.BooleanColumn(attrs={'td': {'align': 'center'}})
    Operazioni = ButtonsList(CustomButton(base_link='/auth/users/', button_text="Modifica",classToAdd=' btn-edit'))
    Operazioni.append(CustomButton(base_link='/auth/users/', button_text="Visualizza",classToAdd=' btn-show'))
    Operazioni.append(DeleteButton())

    class Meta:
        model = User
        attrs = {'class': 'table mt-4'}
        row_attrs = {'data-id': lambda record: record.pk}
        fields = ('username', 'email', 'is_active', 'is_superuser', 'last_login')
        template_name = 'django_tables2/bootstrap4.html'




class ImageBoolean(tables.Column):
    empty_values = list()

    def __init__(self, link_image="", *args, **kwargs):
        super(ImageBoolean, self).__init__(*args, **kwargs)
        self.link_image = link_image

    def render(self, value, record):
        self.accessor = "pk"
        self.orderable = False
        return mark_safe(
            '<img class="hidden inner_table '+ self.attrs.get('td').get('class') +'" src="'+self.link_image+'">')


class SmartGlassTableChat(tables.Table):
    userwhittoken_ptr_id = tables.Column(verbose_name= 'pk',attrs={'td': {'class': 'pk','style': 'display:none;'}, 'th': {'scope': 'col','style': 'display:none;'}})
    name = tables.Column(verbose_name='Nome', attrs={'td': {'class': 'name'}, 'th': {'scope': 'col'}})


    online = ImageBoolean( link_image="/video/static/images/icons/online.png", verbose_name='OnLine', attrs={'td': {'class': 'online'}, 'th': {'scope': 'col'}})
    busy = ImageBoolean( link_image="/video/static/images/icons/busy.png", verbose_name='Occupato', attrs={'td': {'class': 'busy'}, 'th': {'scope': 'col'}})
    calling = ImageBoolean( link_image="/video/static/images/icons/calling.png", verbose_name='Sta Chiamando', attrs={'td': {'class': 'calling'}, 'th': {'scope': 'col'}})
    called = ImageBoolean( link_image="/video/static/images/icons/called.png", verbose_name='Lo Stai Chiamando', attrs={'td': {'class': 'called'}, 'th': {'scope': 'col'}})


    Azioni = ButtonsList(CustomButtonChat(classForJS='start_call_btn', button_text="Chiama", classToAdd='hidden btn-call btn-green'))
    Azioni.append(CustomButtonChat(classForJS='close_call_btn', button_text="Chiudi", classToAdd='hidden btn-close-call btn-red'))
    Azioni.append(CustomButtonChat(classForJS='accept_call_btn', button_text="Rispondi", classToAdd='hidden btn-accept btn-green'))
    Azioni.append(CustomButtonChat(classForJS='ignore_call_btn', button_text="Ignora", classToAdd='hidden btn-ignore btn-red'))
    class Meta:
        model = SmartGlass
        row_attrs = {'data-id': lambda record: record.pk}
        attrs = {'class': 'table mt-4','id':'smartglass'}
        fields = ('userwhittoken_ptr_id', 'name')
        template_name = 'django_tables2/bootstrap4.html'




class Link(tables.Column):
    empty_values = list()

    def render(self, value, record):
        self.accessor = "pk"
        self.orderable=False
        #return self.render(self, value, record)
        return mark_safe(
            '<a hidden id="link_'+str(record.id)+'" href="'+record.link+'"> Link</a> <button class=" copyLink btn btn-sm btn-responsive btn-copy">Copia il Link</button>')


class VideoUserTable(tables.Table):
    Operazioni = ButtonsList( Link())
    Operazioni.append(DeleteButton())



    class Meta:
        model = VideoUser
        row_attrs = {'data-id': lambda record: record.pk}
        attrs = {'class': 'table mt-4'}
        fields = ('name', 'smartGlass','date_expire')
        template_name = 'django_tables2/bootstrap4.html'

