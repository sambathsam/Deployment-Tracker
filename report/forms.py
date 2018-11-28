from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from .models import CustomUser,Report,Review


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email','primary_project','Empid','EmpName','date_join',
                  'primary_process','is_superuser', 'Designation','Team','Empimage')
        
class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model  = CustomUser
        fields = UserChangeForm.Meta.fields

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields=('Name', 'EmpID','Attitude','TaskInterpretation','TaskUnderstanding','Approach','Communication','Execution','Commitment','Fulfillment','Performance','Comments') 
        
CHOICES = [('Present', 'Present'), ('Leave', 'leave'),('Half day leave', 'Half day leave'),('Permission', 'Permission'),
           ('WO', 'Week Off'),('OT','Over Time'),('GH','Govt Holiday'),('WFH','WFH'),]
class ReportForm(forms.ModelForm):
    Attendence  = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect(),initial='Present')
    class Meta:
        model = Report
        fields = ('Empid','Name','Primarytask','Team','Report_date','Attendence','Project_name', 'Subproject_name','Task','No_hours','start_time','End_time','Comments','status')
        
class ReportFormup(forms.ModelForm):
    Attendence  = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect(),initial='Present')
    class Meta:
        model = Report
        fields = ('Report_date','Attendence','Project_name', 'Subproject_name','Task','No_hours','start_time','End_time','Comments')
