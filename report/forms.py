from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from .models import CustomUser,Report,Review,Team,Project,Subproject,Designation


class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields=('id','Teamname')
         
class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields=('Team_name','Projectname')
        
class SubproForm(forms.ModelForm):
    class Meta:
        model = Subproject
        fields=('team','Project_name','Subproject_name')

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email','primary_project','Empid','EmpName','date_join',
                  'primary_process','is_superuser', 'Designation','Team','Empimage')
        
class CustomUserChangeForm(UserChangeForm):
#     def __init__(self, *args, **kwargs):
#         self.user = kwargs.pop('user', None)
#         super().__init__(*args, **kwargs)
#         self.fields['Team'].initial = self.user.Team
#         if self.user != None:
#             print(self.user.Team)
#             print((Team.objects.filter(Teamname=self.user.Team).values('Teamname'))[0]['Teamname'])
#             if self.user.is_staff:
#                 self.fieslds['Team']    = forms.ModelChoiceField(queryset=Team.objects.all().order_by('Teamname'),required=True,widget=forms.Select(attrs={'class': 'form-control'}),initial=str(self.user.Team))
#             else:
#                 self.fields['Team']    = forms.ModelChoiceField(queryset=(Team.objects.filter(Teamname=self.user.Team).values('Teamname'))[0],required=True,widget=forms.Select(attrs={'class': 'form-control'}))
        
    class Meta:
        model  = CustomUser
#         fields = UserChangeForm.Meta.fields
        fields = ('username', 'email','primary_project','Empid','EmpName','date_join',
                  'primary_process','is_superuser', 'Designation','Team','Empimage','password')#UserChangeForm.Meta.fields

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
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
#         super(ReportFormup, self).__init__(*args, **kwargs)
        super().__init__(*args, **kwargs)
        self.fields['Subproject_name'].queryset = Subproject.objects.none()
        self.fields['Subproject_name'].widget.attrs['class'] = 'form-control'
        self.fields['Task'].widget.attrs['class'] = 'form-control'
        
        if 'Project_name' in self.data:
            try:
                pro_id = int(self.data.get('Project_name'))
                self.fields['Subproject_name'].queryset = Subproject.objects.filter(Project_name=pro_id).order_by('Subproject_name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            print(self.instance.Project_name)
            self.fields['Attendence']     = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect(),initial=self.instance.Attendence)
            self.fields['Subproject_name'].queryset = Subproject.objects.filter(Project_name=self.instance.Project_name).order_by('Subproject_name')
        if self.user != None:
            self.fields['Project_name']    = forms.ModelChoiceField(queryset=Project.objects.filter(Team_name=(Team.objects.filter(Teamname=self.user.Team).values('id'))[0]['id']).order_by('Projectname'),required=False,widget=forms.Select(attrs={'class': 'form-control'}))
    class Meta:
        model = Report
        fields = ('Report_date','Attendence','Project_name', 'Subproject_name','Task','No_hours','start_time','End_time','Comments')
        
