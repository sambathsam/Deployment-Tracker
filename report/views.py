from django.shortcuts import render, redirect,render_to_response
from .forms import CustomUserCreationForm,CustomUserChangeForm,ReportForm,ReportFormup,ReviewForm,ProjectForm,TeamForm,SubproForm
from django.core import serializers
from .models import CustomUser,Project,Subproject,Report,Review,datesofmonth,projectTask
from django.views import generic
from django.urls import reverse_lazy
from django.http.response import HttpResponseRedirect
import datetime
from datetime import timedelta
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from django.db.models import Sum
from django.contrib import messages
from django.template.loader import render_to_string
from django.db.models import Q
from django.shortcuts import get_object_or_404
import re,json,xlwt
from django.http import JsonResponse,HttpResponse
from report.models import Team,Task,Designation
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.views.generic.detail import DetailView
# Create your views here.

# class user_profile(DetailView):
#     model = CustomUser
#     template_name = 'users/userprofile.html'
#     def get_object(self):
#         print(self.kwargs['username'])
#         return CustomUser.objects.get(Empid=self.kwargs['username'])
    
def profile(request,eid):
    Emp =request.user.Empid
    print(Emp)
    if request.user.is_superuser or Emp==eid:
        result_set = get_object_or_404(CustomUser, Empid=eid)
        form = CustomUserChangeForm(request.FILES, instance=result_set)
        return render(request, 'users/userprofile.html',{'form':form,'data':result_set})
    else:
        return redirect('login')
    
def Addsome(request):
    form = ProjectForm()
    team = Team.objects.all()
    a= {'Add Team':TeamForm(request.POST),'Add Project':ProjectForm(request.POST),'Add SubProject':SubproForm(request.POST)}
    if request.method == 'GET' and 'Team_name' in str(request):
        team_id = request.GET.get('Team_name')
        print(team_id)
        subpro = Project.objects.filter(Team_name=team_id).order_by('Projectname')
        return render(request, 'registration/pro_dropdown_list.html', {'data': subpro})
    if request.method == 'POST':
        print(request.POST),len(request.POST)
        if 'Team_name' in str(request.POST):
            form = ProjectForm(request.POST)
        elif 'Teamname' in  str(request.POST):
            form = TeamForm(request.POST)
        else:
            form = SubproForm(request.POST)
        if form.is_valid():
            form.save()
            messages.warning(request, 'Saved Successfully')
        
        return render(request,'registration/TPSadd.html',{'form':form,'team':team})
    else:   
        return render(request,'registration/TPSadd.html',{'form':form,'team':team})
    
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
        else:
            messages.error(request, "New password and confirm password does not match.")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'registration/change_password.html', {'form': form})

# class SignUp(generic.CreateView):
#     form_class    = CustomUserCreationForm
#     success_url   = reverse_lazy('userlist')
#     template_name = 'registration/signup.html'
    
def SignUp(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            team_name = Team.objects.all()
            pro = Project.objects.all()
        else:
            team_name = [request.user.Team]
            team_f = (Team.objects.filter(Teamname=request.user.Team).values('id'))[0]['id']
            pro = Project.objects.filter(Team_name=team_f)
        if request.method =="POST":
            print(request.POST)
            if CustomUser.objects.filter(Empid=request.POST['Empid']):
                messages.warning(request, 'Employee Id Already Exists.')
                form = CustomUserCreationForm()
            else:
                form = CustomUserCreationForm(request.POST,request.FILES)
                if form.is_valid():
                    form.save()
                    return redirect('userlist')
                else:
                    print("invalid")
        else:
            form = CustomUserCreationForm()
        return render(request, 'registration/signup.html',{'form':form,'Teams':team_name,'Pro':pro,'task':Task.objects.all(),'title':Designation.objects.all()})
    else:
        return redirect('login')
def HomePageView(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('login')
    else:
        return HttpResponseRedirect('login')
    
# class UserList(generic.ListView):
#     context_object_name = 'emp_list'   
#     queryset = CustomUser.objects.all()
#     template_name = 'users/usrlist.html'
# @login_required(login_url='/login')

def UserList(request):
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    if request.user.is_staff:
        queryset = CustomUser.objects.filter(Empstatus='Active').order_by('Team')
    else:
        queryset = CustomUser.objects.filter(Empstatus='Active',Team=request.user.Team).order_by('Team')
    page      = request.GET.get('page', 1)
    paginator = Paginator(queryset, 100)
    try:
        queryset = paginator.page(page)
    except PageNotAnInteger:
        queryset = paginator.page(1)
    except EmptyPage:
        queryset = paginator.page(paginator.num_pages)
    
    return render(request,'users/usrlist.html',{'emp_list':queryset})

def save_report_form(request, form, template_name):
    team = (Team.objects.filter(Teamname=request.user.Team).values('id'))[0]['id']
    data1 = Project.objects.filter(Team_name=team)
    task_data = projectTask.objects.all()
    data  = dict()
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            usr_ide = 'Yes' if request.user.is_superuser else 'No'
            data['form_is_valid']    = True
            reports = Report.objects.filter(Empid=request.user.Empid,dtcollected=datetime.date.today(),status=2).order_by('Report_date')
            data['html_report_list'] = render_to_string('report/includes/partial_report_list.html', {
                'reports': reports,'user_iden':usr_ide
            })
        else:
            data['form_is_valid'] = False
    context = {'form': form,'data':data1,'taskdata':task_data}
    data['html_form'] = render_to_string(template_name, context, request=request)
    return JsonResponse(data)

def valuecheck(request):
    hour_issue = False 
    chk_ls = ['Leave','GH','Half day leave','WO']
    if str(request.POST['Attendence']) not in str(chk_ls):
        if request.POST['excepted_DAT_0'] != '' and request.POST['excepted_DAT_1'] !='' and request.POST['excepted_TAT_0'] !='' and request.POST['excepted_TAT_1'] !='':
            request.POST = request.POST.copy()
            request.POST['start_time']= str(request.POST['excepted_DAT_0'])+'T'+str(request.POST['excepted_DAT_1'])
            request.POST['End_time']= str(request.POST['excepted_TAT_0'])+'T'+str(request.POST['excepted_TAT_1'])
        else:
            hour_issue = True
            return request,hour_issue,'Please select valid date time.'
    else:
        request.POST = request.POST.copy()
        request.POST['start_time']= ''
        request.POST['End_time']= ''
    if request.user.is_superuser:
        request.POST = request.POST.copy()
        request.POST['Reportstatus']= 'Approved'
    
    Atten = request.POST['Attendence'];Reportdate=request.POST['Report_date']
    rset = Report.objects.filter(~Q(Reportstatus = 'Rejected'),Report_date=Reportdate,Empid=request.user.Empid).values('Report_date','Attendence','Reportstatus')
    if rset:
        date_db   = rset[0]['Report_date']
        att_db    = rset[0]['Attendence']
        status_db = rset[0]['Reportstatus']
        if att_db == "Leave":
            hour_issue = True
            return request,hour_issue,'Already Applied leave for this date.'
        if Atten != 'Present':
            if Atten != 'Half day leave' and Atten != 'Permission':
                if Atten =='WFH' and att_db =='WFH':
                    None
                else:
                    hour_issue = True
                    return request,hour_issue,'Already Reported for this date.You not able to apply '+Atten
            
    if request.POST['start_time'] != '' and request.POST['End_time'] !='':
        start_time = re.search(r"(.*? \d+:\d+)",re.sub("T",' ',str(request.POST['start_time']))).group(1)
        end_time =  re.search(r"(.*? \d+:\d+)",re.sub("T",' ',str(request.POST['End_time']))).group(1)
        
        request.POST = request.POST.copy()
        request.POST['start_time']= start_time
        request.POST['End_time']= end_time
        duration = (datetime.datetime.strptime(str(end_time), '%Y-%m-%d %H:%M') - datetime.datetime.strptime(str(start_time), '%Y-%m-%d %H:%M')).total_seconds()
        num_hr = get_duration(duration)
        print(duration)
        print(num_hr)
        hr_format = re.sub(r":",".",str(num_hr))
        print(hr_format)
    else:
        hr_format = 0
    request.POST = request.POST.copy()
    request.POST['No_hours']=hr_format
    request.POST['status']=2
    if str(request.POST['Attendence'])== "Permission":
        request.POST = request.POST.copy()
        request.POST['Task'] =''
        request.POST['Project_name'] =None
        request.POST['Subproject_name'] =None
    elif (str(request.POST['Attendence'])!= "Present") and (str(request.POST['Attendence'])!= "OT") and (str(request.POST['Attendence'])!= "WFH"):
        request.POST = request.POST.copy()
        if (str(request.POST['Attendence'])== "Leave"):
            request.POST['No_hours']=0
        request.POST['Task'] =''
        request.POST['Project_name'] = None
        request.POST['Subproject_name'] = None
    return request,hour_issue,''

def pendingdate(request,empid):
    reportsdate = Report.objects.values('Report_date').filter(Empid=empid)
    daterange = datesofmonth.objects.filter(weekday__gte=request.user.date_join).exclude(weekday__in = reportsdate)
    tbl_first = datesofmonth.objects.values('weekday').order_by('weekday')[0]
    missdates = daterange.filter(weekday__range=(tbl_first['weekday'],datetime.date.today()))
    newdict  = {}
    some_day_last_week = timezone.now().date() - timedelta(days=7)
    datadict =  Report.objects.filter(Empid=empid,Report_date__range=[some_day_last_week,datetime.date.today()])#,created_at__Report_date=monday_of_last_week, created_at__Report_date=monday_of_this_week)
    datadict = serializers.serialize("json", datadict)
    for fields in json.loads(datadict):
        fields['fields']['pk']=fields['pk']
        if fields['fields']['Project_name'] != None:
            fields['fields']['Pro']=(Project.objects.filter(id=fields['fields']['Project_name']).values('Projectname'))[0]['Projectname']
        else:
            fields['fields']['Pro']=fields['fields']['Attendence']
        if fields['fields']['Subproject_name'] !=None:
            fields['fields']['Spro']=(Subproject.objects.filter(id=fields['fields']['Subproject_name']).values('Subproject_name'))[0]['Subproject_name']
        
        dater = datetime.datetime.strptime(str(fields['fields']['Report_date']), '%Y-%m-%d').strftime("%b.%d, %Y")
        if (str(dater)) in newdict:
            fields['fields']['Report_date'] = dater
            newdict[dater].append(fields['fields'])
        else:
            fields['fields']['Report_date'] = dater
            newdict[(dater)] = [fields['fields']]
            
    newdict = sorted(newdict.items())
    return newdict,missdates

def edit_report(request):
    if request.user.is_authenticated:
        if request.method=='POST':
            if (request.POST['show_date']) !='':
                date_d = (datetime.datetime.now()+datetime.timedelta(days=-3)) > datetime.datetime.strptime(str(request.POST['show_date']),'%Y-%m-%d')
                if date_d:
                    return HttpResponse("<h2>Exceeded More than 3 days to Edit report for given date.</h2><br><h3>Reload current page to back</h3>")
                reports = Report.objects.filter(Empid=request.user.Empid,Report_date=request.POST['show_date'],status=2)
                return render(request,'report/edit_report.html', {'reports': reports})
            else:
                return HttpResponse("<h2> Please select date before search</h2>")
        else:
            return render(request,'report/edit_report.html',{})
    else:
        return redirect("login")
    
def review(request,eid):
    if request.user.is_authenticated:
        pro = Project.objects.filter()
        result_set = get_object_or_404(CustomUser, Empid=eid)
        if request.method =="POST":
            form = ReviewForm(request.POST)
            request.POST = request.POST.copy()
            if form.is_valid():
                form.save()
                return redirect('userlist')
            else:
                print("invalid")
        else:
            form = ReviewForm()
        return render(request, 'review/review.html',{'form':form,'data':result_set,'Pro':pro})
    else:
        return redirect('login')
    
def reviewlist(request):
    if request.user.is_authenticated:
        empid=request.user.Empid
        review_dict = {}
        
        datadict =  Review.objects.filter(EmpID=empid,dtcollected__range=[(datetime.datetime.now()+datetime.timedelta(weeks=-24)).strftime("%Y-%m-%d"),datetime.datetime.now().strftime("%Y-%m-%d")])
        datadict = serializers.serialize("json", datadict)
        for fields in json.loads(datadict):
#             dater = datetime.datetime.strptime(str(fields['fields']['dtcollected']), '%Y-%m-%d').strftime("%b.%d, %Y")
            dater = str(fields['fields']['Review_month'])
            if (str(dater)) in review_dict:
                fields['fields']['Review_month'] = dater
                review_dict[dater].append(fields['fields'])
            else:
                fields['fields']['Review_month'] = dater
                review_dict[(dater)] = [fields['fields']]
            
        review_dict = sorted(review_dict.items())
        newdict,missdates = pendingdate(request,empid)
        return render(request, "review/reviewlist.html", {'form': review_dict, 'dates' : missdates})
    else:
        return redirect('login')
    
def reviewlist_emp(request,eid):
    if request.user.is_superuser:
        review_dict = {}
        datadict =  Review.objects.filter(EmpID=eid)#,created_at__Report_date=monday_of_last_week, created_at__Report_date=monday_of_this_week)
        datadict = serializers.serialize("json", datadict)
        for fields in json.loads(datadict):
#             dater = datetime.datetime.strptime(str(fields['fields']['dtcollected']), '%Y-%m-%d').strftime("%b.%d, %Y")
            dater = str(fields['fields']['Review_month'])
            if (str(dater)) in review_dict:
                fields['fields']['Review_month'] = dater
                review_dict[dater].append(fields['fields'])
            else:
                fields['fields']['Review_month'] = dater
                review_dict[(dater)] = [fields['fields']]
        review_dict = sorted(review_dict.items())
        newdict,missdates = pendingdate(request,eid)
        uname = get_object_or_404(CustomUser, Empid=eid)
        return render(request, "review/reviewlist.html", {'form': review_dict, 'dates' : missdates,'usrname':uname})
    else:
        return HttpResponse("<h3>Your are not Superuser</h3>")
def reviewchart(request,eid=None):
    if eid:
        if request.user.is_superuser:
            datadict =  Review.objects.filter(EmpID=eid).order_by('dtcollected').values('Review_month','Total')#,created_at__Report_date=monday_of_last_week, created_at__Report_date=monday_of_this_week)
            uname = get_object_or_404(CustomUser, Empid=eid)
        else:
            return HttpResponse("<h3>Your are not Superuser</h3>")
    else:
        eid=request.user.Empid;uname=''
        datadict =  Review.objects.filter(EmpID=eid).order_by('dtcollected').values('Review_month','Total')#,created_at__Report_date=monday_of_last_week, created_at__Report_date=monday_of_this_week)
        
    label_ls = [];value_ls=[];data_ls=[]
    for rdict in datadict:
        a ={}
        for key,value in rdict.items():
            if re.search(r"\d",str(value)):
                label_ls.append(value);a['y']=float(value)
            else:
                value_ls.append(str(value));a['label']=value
        data_ls.append(a)
#     data_dict = {"data":json.dumps({'labels': label_ls,'data': value_ls}),'usrname':uname}#chart 1
    data_dict = {"data":data_ls,'usrname':uname}
    return render(request, "review/chart.html", data_dict)
def reportList(request):
    if request.user.is_authenticated:
        empid=request.user.Empid
        usr_id = 'Yes' if request.user.is_superuser else 'No'
        reports = Report.objects.filter(Empid=request.user.Empid,dtcollected=datetime.date.today(),status=2).order_by('Report_date')
        newdict,missdates = pendingdate(request,empid)
        return render(request,'report/report_list.html', {'reports': reports,'dates':missdates,'user_iden':usr_id})    
    else:
        return redirect("home")
    
def report_create(request):
    if request.method == 'POST':
        request,hr_issue,error_msg = valuecheck(request)
        chk_ls = ['Leave','GH']
        date_d = (datetime.datetime.now()+datetime.timedelta(days=-3)) > datetime.datetime.strptime(str(request.POST['Report_date']),'%Y-%m-%d')
        if hr_issue:
            messages.warning(request, error_msg)
            form = ReportForm()
        else:
            form = ReportForm(request.POST)
        if date_d and str(request.POST['Attendence']) not in chk_ls:
            messages.warning(request, 'Exceeded More than 3 days to fill report for given date.')
            form = ReportForm()
    else:
        form = ReportForm()
    return save_report_form(request, form, 'report/includes/partial_report_create.html')

def report_update(request, pk):
    report = get_object_or_404(Report, pk=pk)
    report.status=2
    if request.method == 'POST':
#         hours =  Report.objects.filter(~Q(id = pk),Empid=request.user.Empid,Report_date=datetime.date.today()).aggregate(Sum('No_hours'))
        request,hr_issue,error_msg = valuecheck(request)
        if hr_issue:
            messages.warning(request, error_msg)
            form = ReportFormup(instance=report,user=request.user)
        else:
            form = ReportFormup(request.POST, instance=report)
        chk_ls = ['Leave','GH']
        date_d = (datetime.datetime.now()+datetime.timedelta(days=-3)) > datetime.datetime.strptime(str(request.POST['Report_date']),'%Y-%m-%d')
        if date_d and str(request.POST['Attendence']) not in chk_ls:
            messages.warning(request, 'Exceeded More than 3 days to fill report for given date.')
            form = ReportFormup(instance=report,user=request.user)
    else:
        form = ReportFormup(instance=report,user=request.user)
#     return save_report_form(request, form, 'report/includes/partial_report_update.html')
    return save_report_form(request, form, 'report/includes/report_up.html')

def report_delete(request, pk):
    report = get_object_or_404(Report, pk=pk)
    data = dict()
    if request.method == 'POST':
        report.delete()
        data['form_is_valid'] = True 
        reports = Report.objects.filter(Empid=request.user.Empid,dtcollected=datetime.date.today(),status=2).order_by('Report_date')
        data['html_report_list'] = render_to_string('report/includes/partial_report_list.html', {
            'reports': reports
        })
    else:
        context = {'reports': report}
        data['html_form'] = render_to_string('report/includes/partial_report_delete.html',
            context,
            request=request,
        )
    return JsonResponse(data)

def reportlist(request):
    if request.user.is_authenticated:
        empid = request.user.Empid
        newdict,missdates = pendingdate(request,empid)
        if request.method=='POST':
            newdict = {}
            if str(request.POST['show_date']) != '':
                datadict = Report.objects.filter(Empid=request.user.Empid,Report_date=request.POST['show_date'])
                datadict = serializers.serialize("json", datadict)
                for fields in json.loads(datadict):
                    fields['fields']['pk']=fields['pk']
                    if (fields['fields']['Project_name']) != None:
                        fields['fields']['Pro']=(Project.objects.filter(id=fields['fields']['Project_name']).values('Projectname'))[0]['Projectname']
                    if (fields['fields']['Subproject_name']) != None:
                        fields['fields']['Spro']=(Subproject.objects.filter(id=fields['fields']['Subproject_name']).values('Subproject_name'))[0]['Subproject_name']
                    
                    dater = datetime.datetime.strptime(str(fields['fields']['Report_date']), '%Y-%m-%d').strftime("%b.%d, %Y")
                    if (str(dater)) in newdict:
                        fields['fields']['Report_date'] = dater
                        newdict[dater].append(fields['fields'])
                    else:
                        fields['fields']['Report_date'] = dater
                        newdict[(dater)] = [fields['fields']]
                newdict = sorted(newdict.items())
                return render(request, "report/reportlist.html", {'form': newdict, 'dates' : missdates})
            else:
                return HttpResponse ("<h2>Please select the date before Click Search Button</h2><br><h4> Reload current page</h4>")
        else:
            return render(request, "report/reportlist.html", {'form': newdict, 'dates' : missdates})
    else:
        return redirect('login')
    
def reportlist_emp(request,eid):
    if request.user.is_superuser:
        newdict,missdates = pendingdate(request,eid)
        uname = get_object_or_404(CustomUser, Empid=eid)
        if request.method=='POST':
            newdict = {}
            if str(request.POST['show_date']) != '':
                datadict = Report.objects.filter(Empid=eid,Report_date=request.POST['show_date'])
                datadict = serializers.serialize("json", datadict)
                for fields in json.loads(datadict):
                    fields['fields']['pk']=fields['pk']
                    if (fields['fields']['Project_name']) != None:
                        fields['fields']['Pro']=(Project.objects.filter(id=fields['fields']['Project_name']).values('Projectname'))[0]['Projectname']
                    if (fields['fields']['Subproject_name']) != None:
                        fields['fields']['Spro']=(Subproject.objects.filter(id=fields['fields']['Subproject_name']).values('Subproject_name'))[0]['Subproject_name']
                    
                    dater = datetime.datetime.strptime(str(fields['fields']['Report_date']), '%Y-%m-%d').strftime("%b.%d, %Y")
                    if (str(dater)) in newdict:
                        fields['fields']['Report_date'] = dater
                        newdict[dater].append(fields['fields'])
                    else:
                        fields['fields']['Report_date'] = dater
                        newdict[(dater)] = [fields['fields']]
                newdict = sorted(newdict.items())
                return render(request, "report/reportlist.html", {'form': newdict, 'dates' : missdates,'usrname':uname})
            else:
                return HttpResponse ("<h2>Please select the date before Click Search Button</h2><br><h4> Reload current page</h4>")
        else:
            return render(request, "report/reportlist.html", {'form': newdict, 'dates' : missdates,'usrname':uname})
    else:
        return redirect('login')
def reportstatus(request,rid,eid,status):
    print(request)
    report= get_object_or_404(Report, pk=rid)
    if str(status)=="App":
        report.Reportstatus = "Approved"
    else:
        report.Reportstatus = "Rejected"
    report.save()
    return redirect('/reportlist/'+eid)
    
def edit_user(request,eid):
    if request.user.is_authenticated:
        if request.user.is_staff:
            team_name = Team.objects.all()
            pro = Project.objects.all()
        else:
            team_name = [request.user.Team]
            team_f = (Team.objects.filter(Teamname=request.user.Team).values('id'))[0]['id']
            pro = Project.objects.filter(Team_name=team_f)
        
        result_set = get_object_or_404(CustomUser, Empid=eid)
        if request.method =="POST":
            print(request.POST)
            if CustomUser.objects.filter(~Q(username = request.POST['username']),Empid=request.POST['Empid']):
                messages.warning(request, 'Employee Id Already Exists.')
                form = CustomUserChangeForm(instance=result_set)
            else:
                form = CustomUserChangeForm(request.POST,request.FILES, instance=result_set)
                if form.is_valid():
                    form.save()
                    try:
                        return redirect('userlist')
                    except:
                        return redirect('create_logs')
                else:
                    print("invalid")
        else:
            form = CustomUserChangeForm(instance=result_set)
        return render(request, 'users/edit_user.html',{'form':form,'Teams':(team_name),'Pro':pro,'task':Task.objects.all(),'title':Designation.objects.all()})
    else:
        return redirect('login')
def get_duration(duration):
    hours = int(duration / 3600)
    minutes = int(duration % 3600 / 60)
    seconds = int((duration % 3600) % 60)
    return '{:02d}:{:02d}'.format(hours, minutes)
def datainsert(request):
    hour_issue = False
    Atten = "Present";Reportdate=request.POST['Report_date']
    rset = Report.objects.filter(~Q(Reportstatus = 'Rejected'),Report_date=Reportdate,Empid=request.user.Empid).values('Report_date','Attendence','Reportstatus')
    print(rset)
    if rset:
        date_db   = rset[0]['Report_date']
        att_db    = rset[0]['Attendence']
        status_db = rset[0]['Reportstatus']
        print(date_db,status_db,att_db)
        if att_db == "Leave":
            hour_issue = True
            return request,hour_issue,'Already Applied leave for this date.'
        if Atten != 'Present':
            if Atten != 'Half day leave' and Atten != 'Permission':
                hour_issue = True
                return request,hour_issue,'Already Reported for this date.You not able to apply '+Atten
    request.POST = request.POST.copy()
    request.POST['start_time']= (datetime.datetime.now()+datetime.timedelta(hours = int('05'), minutes=30)).strftime('%Y-%m-%d %H:%M')
    request.POST['End_time']  = (datetime.datetime.now()+datetime.timedelta(hours = int('05'), minutes=30)).strftime('%Y-%m-%d %H:%M')
    request.POST['No_hours']  = 0
    request.POST['Comments']  = None
    request.POST['Attendence'] = "Present"
    return request,hour_issue,''
def hour_calc(report):
    cur_tym = (datetime.datetime.now()+datetime.timedelta(hours = int('05'), minutes=30)).strftime('%Y-%m-%d %H:%M')
    duration = (datetime.datetime.strptime(str(cur_tym), '%Y-%m-%d %H:%M') - datetime.datetime.strptime(re.sub(r':00\+.*','',str(report.start_time)), '%Y-%m-%d %H:%M')).total_seconds()
    num_hr = get_duration(duration)
    nh = re.sub(r":",".",str(num_hr))
    nm = str(report.hold_hours)
    h1  = int(nh.split('.')[0])+int(nm.split('.')[0])
    m1  = int(nh.split('.')[1])+int(nm.split('.')[1])
    pending = datetime.timedelta(hours = int(h1), minutes=int(m1))
    duration= pending.seconds
    hours = int(duration / 3600)+int(pending.days)*24
    minutes = int(duration % 3600 / 60)
    seconds = int((duration % 3600) % 60)
    hr_format= '{:02d}.{:02d}'.format(hours, minutes)
    print(hr_format)
    return hr_format

def log_resume(request,pk):
    report = get_object_or_404(Report, pk=int(pk))
    report.start_time= (datetime.datetime.now()+datetime.timedelta(hours = int('05'), minutes=30)).strftime('%Y-%m-%d %H:%M')
    report.End_time  = (datetime.datetime.now()+datetime.timedelta(hours = int('05'), minutes=30)).strftime('%Y-%m-%d %H:%M')
    report.Comments  = None
    report.save()
    return redirect('/create')
def log_hold(request,pk):
    report = get_object_or_404(Report, pk=int(pk))
    report.Comments = "On Hold"
    report.End_time = (datetime.datetime.now()+datetime.timedelta(hours = int('05'), minutes=30)).strftime('%Y-%m-%d %H:%M')
    report.hold_hours = hour_calc(report)
    report.save()
    return redirect('/create')

def logpage(request):
    #print(request)
    if request.user.is_authenticated:
        team = (Team.objects.filter(Teamname=request.user.Team).values('id'))[0]['id']
        data1 = Project.objects.filter(Team_name=team)
        task_data = projectTask.objects.all()
        newdict,missdates = pendingdate(request,request.user.Empid)
        reports = Report.objects.filter(Q(Empid=request.user.Empid,dtcollected=datetime.date.today())| Q(Empid=request.user.Empid,status=0)).order_by('Report_date')
        disbtn =  Report.objects.filter(Q(Empid=request.user.Empid,status=0,Comments__isnull=True)).order_by('Report_date')
        btnstatus = '1' if len(disbtn) else '0'
        #print(btnstatus)
        form  = ReportForm()
        if request.method == 'POST':
            print(request.POST)
            if 'Comments' in str(request.POST):
                id_r = re.search(r'Comments_(\d+)', str(request.POST)).group(1)
                report = get_object_or_404(Report, pk=int(id_r))
                request.POST = request.POST.copy()
                report.Comments = request.POST['Comments_'+id_r]
                request.POST['End_time']  = (datetime.datetime.now()+datetime.timedelta(hours = int('05'), minutes=30)).strftime('%Y-%m-%d %H:%M')
                if request.user.is_superuser:
                    report.Reportstatus= 'Approved'
                    print("herere upated")
                print(request.POST)
                report.End_time = request.POST['End_time'];report.status = 1
                report.No_hours = hour_calc(report)
                report.save()
                reports = Report.objects.filter(Q(Empid=request.user.Empid,dtcollected=datetime.date.today())| Q(Empid=request.user.Empid,status=0)).order_by('Report_date')
                disbtn =  Report.objects.filter(Q(Empid=request.user.Empid,status=0,Comments__isnull=True)).order_by('Report_date')
                btnstatus = '1' if len(disbtn) else '0'
                return render(request,'report/log_create.html',{'pro':data1,'taskdata':task_data,'form':form,'reports':reports,'dates' : missdates,'btnstatus':btnstatus})
            else:
                request,hr_issue,error_msg = datainsert(request)
                if hr_issue:
                    messages.warning(request, error_msg)
                    return redirect('create_logs')
                form = ReportForm(request.POST)
                if form.is_valid():
                    form.save()
                reports = Report.objects.filter(Q(Empid=request.user.Empid,dtcollected=datetime.date.today())| Q(Empid=request.user.Empid,status=0)).order_by('Report_date')
                disbtn =  Report.objects.filter(Q(Empid=request.user.Empid,status=0,Comments__isnull=True)).order_by('Report_date')
                btnstatus = '1' if len(disbtn) else '0'
#                 return render_to_response('report/log_create.html',{'pro':data1,'form':form,'reports':reports,'dates' : missdates,'btnstatus':btnstatus})
                return redirect('create_logs')
        else:
            return render(request,'report/log_create.html',{'pro':data1,'taskdata':task_data,'form':form,'reports':reports,'dates' : missdates,'btnstatus':btnstatus})
    else:
        return redirect('login')
def load_subpro(request):
    if request.GET.get('Project_name'):
        project_id = request.GET.get('Project_name')
        subpro = Subproject.objects.filter(Project_name=project_id).order_by('Subproject_name')
        return render(request, 'hr/subpro_dropdown_list.html', {'data': subpro})
    else:
        team_id = request.GET.get('Team_name')
        subpro = Project.objects.filter(Team_name=team_id).order_by('Projectname')
        return render(request, 'registration/pro_dropdown_list.html', {'data': subpro})

def attendence(request):
    if request.user.is_superuser:
        import calendar
        team_name = Team.objects.all()
        if request.method =="POST":
            month = request.POST['Month']
            yyr   = request.POST['Year']
            team  = request.POST['Team']
#             currmonth = datetime.date.today().strftime('%Y-%m')
#             year  = currmonth.split('-')[0]
            num_days = calendar.monthrange(int(yyr), int(month))[1]
            days = [datetime.date(int(yyr),int(month), day) for day in range(1, num_days+1)]
            if request.user.is_staff:
                rows = Report.objects.filter(~Q(Empid = '1'),Report_date__month=int(month),Report_date__year=int(yyr),Team=team).values_list('Empid','Name','Report_date','Attendence').order_by('Empid')
                Name_detail = CustomUser.objects.filter(~Q(Empid = '1'),Team=team).values_list('Empid','EmpName')
            else:
                rows = Report.objects.filter(~Q(Empid = '1'),Report_date__month=int(month),Report_date__year=int(yyr),Team=team).values_list('Empid','Name','Report_date','Attendence').order_by('Empid')
                Name_detail = CustomUser.objects.filter(~Q(Empid = '1'),Team=team).values_list('Empid','EmpName')
            if len(rows)==0:
                return HttpResponse("<h2>No reports for Selected Month</h2><h3> Refresh  page</h3>")
            a= {};i=1
            for name in Name_detail:
                name = name[1]
                a[name.lower()] = i
                i+=1
            response = HttpResponse(content_type='application/ms-excel')
            response['Content-Disposition'] = 'attachment; filename="Attendence.xls"'
            wb = xlwt.Workbook(encoding='utf-8');ws = wb.add_sheet('Attendence',cell_overwrite_ok=True)
            # Sheet header, first row
            row_num = 0;font_style = xlwt.XFStyle();font_style.font.bold = True
            aday = ['Empid','Name']
            for da_t in days:
                aday.append(str(da_t))
            aday.append('P');aday.append('EL');aday.append('HEL');aday.append('WFH')
            columns = aday
            for col_num in range(len(columns)):
                ws.write(row_num, col_num, columns[col_num], font_style)
            # Sheet body, remaining rows
            font_style = xlwt.XFStyle()
            for row in Name_detail:
                row_num += 1
                for col_num in range(len(row)):
                    ws.write(row_num, col_num, row[col_num], font_style)
            atten = {'Present':'P','Leave':'EL','Half day leave':'HEL','WO':'WO','OT':'OT','Permission':'P','GH':'GH','WFH':'WFH','OTH':'OTH','HWFH':'HWFH'}
            name_mat = '';date_mat = '';atte_mat = ''
            Mday = [str(da_t) for da_t in days]
            arr_date = []
            for M_week in Mday:
                day_ = datetime.datetime.strptime(str(M_week),'%Y-%m-%d').strftime('%a')
                if str(day_) =='Sun' or str(day_) =='Sat':
                    arr_date.append(M_week)
            for row in rows:
                Name_r = row[1];date_r = row[2];atte_r = atten[str(row[3])]
                if Name_r !=name_mat:
                    for c in ['P','EL','HEL','WFH']:
                        ws.write(row_num, aday.index(str(c)), xlwt.Formula('COUNTIF(C'+str(row_num+1)+':AG'+str(row_num+1)+',"'+str(c)+'")'))
                    for wend in arr_date:
                        row_num = int(a[str(Name_r.lower())]);col_num = aday.index(str(wend))
                        ws.write(row_num, col_num, 'WO', font_style)
                if Name_r ==name_mat and date_mat == date_r:
                    if atte_r=='P' and atte_mat=='HEL':
                        atte_r = 'HEL'
                row_num = int(a[str(Name_r.lower())]);col_num = aday.index(str(date_r))
                ws.write(row_num, col_num, atte_r, font_style)
                name_mat = Name_r;date_mat = date_r;atte_mat = atte_r
            for c in ['P','EL','HEL','WFH']:
                ws.write(row_num, aday.index(str(c)), xlwt.Formula('COUNTIF(C'+str(row_num+1)+':AG'+str(row_num+1)+',"'+str(c)+'")'))
            wb.save(response)
            return response
        else:
            return render(request, 'review/Attendence.html',{'team':team_name})
    else:
        return redirect('login')
    
def export_users_xls(request):
    if request.user.is_superuser:
        if request.user.is_staff:
            teamreport = 1
        else:
            teamreport = None
        if request.method=="POST":
            print(request.POST)
            if 'Team' in  str(request.POST):
                print("here tteamm")
                if str(request.POST['Team']) != '' and 'overall' in str(request.POST):
                    return HttpResponse("<h2>Please select Team Or Over all,You selected Both.</h2><br><h2>Reload current Page</h2>")
                elif str(request.POST['Team']) == '' and 'overall' not in str(request.POST):
                    return HttpResponse("<h2>Please select Team Or Over all</h2><br><h2>Reload current Page</h2>")
                elif 'Team' in  str(request.POST) and 'overall' not in str(request.POST):
                    rows = Report.objects.filter(Team=request.POST['Team'],Reportstatus = 'Approved',Report_date__range=[request.POST['start_date'],request.POST['end_date']]).values_list('Empid','Name','Primarytask','Team','Report_date','Attendence','Project_name', 'Subproject_name','Task','No_hours','Comments').order_by('Empid')
                elif str(request.POST['Team']) == '' and 'overall' in str(request.POST):
                    rows = Report.objects.filter(Reportstatus = 'Approved',Report_date__range=[request.POST['start_date'],request.POST['end_date']]).values_list('Empid','Name','Primarytask','Team','Report_date','Attendence','Project_name', 'Subproject_name','Task','No_hours','Comments').order_by('Team')
            elif str(request.POST['Project_name'])!='' or str(request.POST['Subproject_name'])!='' or str(request.POST['start_date'])!='' or request.POST['end_date'] != '':
                project_re = request.POST['Project_name'];subpro_re=request.POST['Subproject_name']
                if str(project_re)!='' and str(subpro_re)!='' and  str(request.POST['start_date'])!='' and request.POST['end_date'] != '':
                    rows = Report.objects.filter(Project_name=project_re,Reportstatus = 'Approved',Subproject_name=subpro_re,Report_date__range=[request.POST['start_date'],request.POST['end_date']]).values_list('Empid','Name','Primarytask','Team','Report_date','Attendence','Project_name', 'Subproject_name','Task','No_hours','Comments').order_by('Empid')
                elif str(project_re)!='' and str(subpro_re)=='' and  str(request.POST['start_date'])!='' and request.POST['end_date'] != '':
                    rows = Report.objects.filter(Project_name=project_re,Reportstatus = 'Approved',Report_date__range=[request.POST['start_date'],request.POST['end_date']]).values_list('Empid','Name','Primarytask','Team','Report_date','Attendence','Project_name', 'Subproject_name','Task','No_hours','Comments').order_by('Empid')
                elif str(project_re)=='' and str(subpro_re)!='' and  str(request.POST['start_date'])!='' and request.POST['end_date'] != '':
                    rows = Report.objects.filter(Subproject_name=subpro_re,Reportstatus = 'Approved',Report_date__range=[request.POST['start_date'],request.POST['end_date']]).values_list('Empid','Name','Primarytask','Team','Report_date','Attendence','Project_name', 'Subproject_name','Task','No_hours','Comments').order_by('Empid')
                elif str(project_re)=='' and str(subpro_re)=='':
                    return HttpResponse("<h2>Please select Project</h2><br><h2>Reload current Page</h2>")
#                     rows = Report.objects.filter(Report_date__range=[request.POST['start_date'],request.POST['end_date']],Reportstatus = 'Approved',Team=request.user.Team).values_list('Empid','Name','Primarytask','Team','Report_date','Attendence','Project_name', 'Subproject_name','Task','No_hours','Comments').order_by('Empid')
#                 elif str(project_re)!='' and str(subpro_re)!='' and  str(request.POST['start_date']) =='' and request.POST['end_date'] == '':
#                     rows = Report.objects.filter(Project_name=project_re,Reportstatus = 'Approved',Subproject_name=subpro_re).values_list('Empid','Name','Primarytask','Team','Report_date','Attendence','Project_name', 'Subproject_name','Task','No_hours','Comments').order_by('Empid')
#                 elif str(project_re)!='' and str(subpro_re)=='' and  str(request.POST['start_date']) =='' and request.POST['end_date'] == '':
#                     rows = Report.objects.filter(Project_name=project_re,Reportstatus = 'Approved').values_list('Empid','Name','Primarytask','Team','Report_date','Attendence','Project_name', 'Subproject_name','Task','No_hours','Comments').order_by('Empid')
#                 elif str(project_re)=='' and str(subpro_re)!='' and  str(request.POST['start_date']) =='' and request.POST['end_date'] == '':
#                     rows = Report.objects.filter(Subproject_name=subpro_re,Reportstatus = 'Approved').values_list('Empid','Name','Primarytask','Team','Report_date','Attendence','Project_name', 'Subproject_name','Task','No_hours','Comments').order_by('Empid')
                else:
                    return HttpResponse("<h2>Please Select Dates Correctly</h2>")
            else:
                return HttpResponse("<h2>Please select Project Or Dates</h2><br><h2>Reload current Page</h2>")
            
            if len(rows)==0:
                return HttpResponse("<h2>No reports for Selected Dates</h2><h4>Reload current page</h4>")
            response = HttpResponse(content_type='application/ms-excel')
            response['Content-Disposition'] = 'attachment; filename="Reports.xls"'
            wb = xlwt.Workbook(encoding='utf-8')
            ws = wb.add_sheet('Reports')
            # Sheet header, first row
            row_num = 0
            font_style = xlwt.XFStyle()
            font_style.font.bold = True
            columns = ['Empid','Name','Primarytask','Team','Report_date','Attendence','Project_name', 'Subproject_name','Task','No_hours','Comments']
            for col_num in range(len(columns)):
                ws.write(row_num, col_num, columns[col_num], font_style)
            # Sheet body, remaining rows
            font_style = xlwt.XFStyle()
            for row in rows:
                lt = list(row)
                lt[4]=str(row[4])
                if row[6]!=None:
                    lt[6]=str(Project.objects.get(id=int(row[6])))
                if row[7]!=None:
                    lt[7]=str(Subproject.objects.get(id=int(row[7])))
                row = tuple(lt)
                row_num += 1
                for col_num in range(len(row)):
                    ws.write(row_num, col_num, row[col_num], font_style)
            wb.save(response)
            return response
        else:
            team_names = Team.objects.all()
            if teamreport ==1:
                pro     = Project.objects.all()
                context = {'pro':pro,'teamreport':teamreport,'Teams':team_names}
            else:
                team_f = (Team.objects.filter(Teamname=request.user.Team).values('id'))[0]['id']
                pro = Project.objects.filter(Team_name=team_f)
                context = {'pro':pro,'teamreport':teamreport,'Teams':team_names}
            return render(request, 'report/export_report.html',context)
    else:
        return redirect('login')
        
        
