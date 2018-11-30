from django.contrib import admin

# Register your models here.
from django.contrib.auth.admin import UserAdmin
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser,Project,Subproject,Report,datesofmonth,Review,Team,Designation,Task

class CustomUserAdmin(UserAdmin):
    model    = CustomUser
    add_form = CustomUserCreationForm
    form     = CustomUserChangeForm
    
admin.site.register(CustomUser, CustomUserAdmin)
admin.register(Team)(admin.ModelAdmin)
admin.register(Project)(admin.ModelAdmin)
admin.register(Subproject)(admin.ModelAdmin)
admin.register(Report)(admin.ModelAdmin)
admin.register(datesofmonth)(admin.ModelAdmin)
admin.register(Review)(admin.ModelAdmin)
admin.register(Designation)(admin.ModelAdmin)
admin.register(Task)(admin.ModelAdmin)