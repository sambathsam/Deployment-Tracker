from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm,ReportForm,ReportFormup,ReviewForm
from django.core import serializers
from .models import CustomUser,Project,Subproject,Report,Review,datesofmonth
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
# Create your views here.

def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('create_logs')
        else:
            messages.error(request, 'Please correct the error below.')
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
def UserList(request):
    if request.user.is_staff:
        queryset = CustomUser.objects.all()
    else:
        queryset = CustomUser.objects.filter(Team=request.user.Team)
    page = request.GET.get('page', 1)
    paginator = Paginator(queryset, 10)
    try:
        queryset = paginator.page(page)
    except PageNotAnInteger:
        queryset = paginator.page(1)
    except EmptyPage:
        queryset = paginator.page(paginator.num_pages)
    print(request.user.Team)
    return render(request,'users/usrlist.html',{'emp_list':queryset})

def save_report_form(request, form, template_name):
    team = (Team.objects.filter(Teamname=request.user.Team).values('id'))[0]['id']
    data1 = Project.objects.filter(Team_name=team)
    data  = dict()
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            data['form_is_valid']    = True
            reports = Report.objects.filter(Empid=request.user.Empid,dtcollected=datetime.date.today(),status=2).order_by('Report_date')
            data['html_report_list'] = render_to_string('report/includes/partial_report_list.html', {
                'reports': reports
            })
        else:
            data['form_is_valid'] = False
    context = {'form': form,'data':data1}
    data['html_form'] = render_to_string(template_name, context, request=request)
    return JsonResponse(data)

def valuecheck(request,hours):
    hour_issue = False 
    if request.POST['start_time'] != '' and request.POST['End_time'] !='':
        start_time = re.search(r"(.*? \d+:\d+)",re.sub("T",' ',str(request.POST['start_time']))).group(1)
        end_time =  re.search(r"(.*? \d+:\d+)",re.sub("T",' ',str(request.POST['End_time']))).group(1)
        print(start_time,end_time)
        request.POST = request.POST.copy()
        request.POST['start_time']= start_time
        request.POST['End_time']= end_time
        duration = (datetime.datetime.strptime(str(end_time), '%Y-%m-%d %H:%M') - datetime.datetime.strptime(str(start_time), '%Y-%m-%d %H:%M')).total_seconds()
        num_hr = get_duration(duration)
        print(num_hr)
        hours =  Report.objects.filter(Empid=request.user.Empid,Report_date=request.POST['Report_date']).aggregate(Sum('hold_hours'))
        print(hours)
        if hours['hold_hours__sum'] == None:
            t_hr = float(re.sub(r":",".",str(num_hr)))
        else:
            t_hr = float(re.sub(r":",".",str(num_hr)))+float(hours['hold_hours__sum'])
        print(t_hr)
        hr_format = datetime.timedelta(hours = int(str(t_hr).split('.')[0]), minutes=int(str(t_hr).split('.')[1])).total_seconds()
        hr_format = float(re.sub(r":",".",str(get_duration(hr_format))))
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
        request.POST['Task'] =''
        request.POST['Project_name'] = None
        request.POST['Subproject_name'] = None
    return request,hour_issue

def pendingdate(request,empid):
    reportsdate = Report.objects.values('Report_date').filter(Empid=empid)
    daterange = datesofmonth.objects.exclude(weekday__in = reportsdate)
    missdates = daterange.filter(weekday__range=(datetime.date.today().replace(day=1),datetime.date.today()))
    newdict  = {}
    some_day_last_week = timezone.now().date() - timedelta(days=7)
    datadict =  Report.objects.filter(Empid=empid,Report_date__range=[some_day_last_week,datetime.date.today()])#,created_at__Report_date=monday_of_last_week, created_at__Report_date=monday_of_this_week)
    datadict = serializers.serialize("json", datadict)
    for fields in json.loads(datadict):
        fields['fields']['pk']=fields['pk']
        if fields['fields']['Project_name'] != None:
            fields['fields']['Pro']=(Project.objects.filter(id=fields['fields']['Project_name']).values('Projectname'))[0]['Projectname']
        if fields['fields']['Subproject_name'] !=None:
            fields['fields']['Spro']=(Subproject.objects.filter(id=fields['fields']['Subproject_name']).values('Subproject_name'))[0]['Subproject_name']
        if (str(fields['fields']['Report_date'])) in newdict:
            newdict[str(fields['fields']['Report_date'])].append(fields['fields'])
        else:
            newdict[str(fields['fields']['Report_date'])] = [fields['fields']]
    newdict = sorted(newdict.items())
    return newdict,missdates

def edit_report(request):
    if request.user.is_authenticated:
        if request.method=='POST':
            if (request.POST['show_date']) !='':
                print(request.POST['show_date'])
                date_d = (datetime.datetime.now()+datetime.timedelta(days=-7)) > datetime.datetime.strptime(str(request.POST['show_date']),'%Y-%m-%d')
                if date_d:
                    print('here')
                    return HttpResponse("<h2>Exceeded More than 7 days to Edit report for given date.</h2><br><h3>Reload current page to back</h3>")
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
        return render(request, 'review/review.html',{'form':form,'data':result_set})
def reviewlist(request):
    if request.user.is_authenticated:
        empid=request.user.Empid
        review_dict = {}
        datadict =  Review.objects.filter(EmpID=empid,dtcollected__month__gte=((datetime.datetime.now()+datetime.timedelta(weeks=-24)).strftime("%m")),dtcollected__month__lte=datetime.datetime.now().strftime("%m"))
        datadict = serializers.serialize("json", datadict)
        for fields in json.loads(datadict):
            if (str(fields['fields']['dtcollected'])) in review_dict:
                review_dict[str(fields['fields']['dtcollected'])].append(fields['fields'])
            else:
                review_dict[str(fields['fields']['dtcollected'])] = [fields['fields']]
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
            if (str(fields['fields']['dtcollected'])) in review_dict:
                review_dict[str(fields['fields']['dtcollected'])].append(fields['fields'])
            else:
                review_dict[str(fields['fields']['dtcollected'])] = [fields['fields']]
        review_dict = sorted(review_dict.items())
        newdict,missdates = pendingdate(request,eid)
        uname = get_object_or_404(CustomUser, Empid=eid)
        return render(request, "review/reviewlist.html", {'form': review_dict, 'dates' : missdates,'usrname':uname})
    else:
        return HttpResponse("<h3>Your are not Superuser</h3>")
def reportList(request):
    if request.user.is_authenticated:
        empid=request.user.Empid
        reports = Report.objects.filter(Empid=request.user.Empid,dtcollected=datetime.date.today(),status=2).order_by('Report_date')
        newdict,missdates = pendingdate(request,empid)
        return render(request,'report/report_list.html', {'reports': reports,'dates':missdates})    
    else:
        return redirect("home")
    
def report_create(request):
    if request.method == 'POST':
        hours =  Report.objects.filter(Empid=request.user.Empid,Report_date=datetime.date.today()).aggregate(Sum('No_hours'))
        request,hr_issue = valuecheck(request,hours)
        print(request.POST)
        date_d = (datetime.datetime.now()+datetime.timedelta(days=-7)) > datetime.datetime.strptime(str(request.POST['Report_date']),'%Y-%m-%d')
        if date_d:
            messages.warning(request, 'Exceeded More than 7 days to fill report for given date.')
            form = ReportForm()
        else:
            form = ReportForm(request.POST)
        print(request.POST)
    else:
        form = ReportForm()
    return save_report_form(request, form, 'report/includes/partial_report_create.html')

def report_update(request, pk):
    report = get_object_or_404(Report, pk=pk)
    report.status=2
    if request.method == 'POST':
        hours =  Report.objects.filter(~Q(id = pk),Empid=request.user.Empid,Report_date=datetime.date.today()).aggregate(Sum('No_hours'))
        request,hr_issue = valuecheck(request,hours)
        date_d = (datetime.datetime.now()+datetime.timedelta(days=-7)) > datetime.datetime.strptime(str(request.POST['Report_date']),'%Y-%m-%d')
        if date_d:
            messages.warning(request, 'Exceeded More than 7 days to fill report for given date.')
            form = ReportFormup(instance=report)
        else:
            form = ReportFormup(request.POST, instance=report)
    else:
        form = ReportFormup(instance=report)
    return save_report_form(request, form, 'report/includes/partial_report_update.html')

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
                    fields['fields']['Pro']=(Project.objects.filter(id=fields['fields']['Project_name']).values('Projectname'))[0]['Projectname']
                    fields['fields']['Spro']=(Subproject.objects.filter(id=fields['fields']['Subproject_name']).values('Subproject_name'))[0]['Subproject_name']
                    if (str(fields['fields']['Report_date'])) in newdict:
                        newdict[str(fields['fields']['Report_date'])].append(fields['fields'])
                    else:
                        newdict[str(fields['fields']['Report_date'])] = [fields['fields']]
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
                    fields['fields']['Pro']=(Project.objects.filter(id=fields['fields']['Project_name']).values('Projectname'))[0]['Projectname']
                    fields['fields']['Spro']=(Subproject.objects.filter(id=fields['fields']['Subproject_name']).values('Subproject_name'))[0]['Subproject_name']
                    if (str(fields['fields']['Report_date'])) in newdict:
                        newdict[str(fields['fields']['Report_date'])].append(fields['fields'])
                    else:
                        newdict[str(fields['fields']['Report_date'])] = [fields['fields']]
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
    if request.user.is_staff:
        team_name = Team.objects.all()
        pro = Project.objects.all()
    else:
        team_name = [request.user.Team]
        team_f = (Team.objects.filter(Teamname=request.user.Team).values('id'))[0]['id']
        pro = Project.objects.filter(Team_name=team_f)
    if request.user.is_authenticated:
        result_set = get_object_or_404(CustomUser, Empid=eid)
        if request.method =="POST":
            form = CustomUserCreationForm(request.POST,request.FILES, instance=result_set)
            if form.is_valid():
                form.save()
                return redirect('userlist')
            else:
                print("invalid")
        form = CustomUserCreationForm(instance=result_set)
        return render(request, 'users/edit_user.html',{'form':form,'Teams':(team_name),'Pro':pro,'task':Task.objects.all(),'title':Designation.objects.all()})
    
def get_duration(duration):
    hours = int(duration / 3600)
    minutes = int(duration % 3600 / 60)
    seconds = int((duration % 3600) % 60)
    return '{:02d}:{:02d}'.format(hours, minutes)
def datainsert(request):
    request.POST = request.POST.copy()
    request.POST['start_time']= (datetime.datetime.now()+datetime.timedelta(hours = int('05'), minutes=30)).strftime('%Y-%m-%d %H:%M')
    request.POST['End_time']  = (datetime.datetime.now()+datetime.timedelta(hours = int('05'), minutes=30)).strftime('%Y-%m-%d %H:%M')
    request.POST['No_hours']  = 0
    request.POST['Comments']= None
    request.POST['Attendence'] = "Present"
    return request
def hour_calc(report):
    cur_tym = (datetime.datetime.now()+datetime.timedelta(hours = int('05'), minutes=30)).strftime('%Y-%m-%d %H:%M')
    duration = (datetime.datetime.strptime(str(cur_tym), '%Y-%m-%d %H:%M') - datetime.datetime.strptime(re.sub(r':00\+.*','',str(report.start_time)), '%Y-%m-%d %H:%M')).total_seconds()
    num_hr = get_duration(duration)
    t_hr = float(re.sub(r":",".",str(num_hr)))+float(report.hold_hours)
    hr_format = datetime.timedelta(hours = int(str(t_hr).split('.')[0]), minutes=int(str(t_hr).split('.')[1])).total_seconds()
    hr_format = float(re.sub(r":",".",str(get_duration(hr_format))))
    return hr_format

def log_resume(request,pk):
    print("here log resume")
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
    print(request)
    team = (Team.objects.filter(Teamname=request.user.Team).values('id'))[0]['id']
    data1 = Project.objects.filter(Team_name=team)
    newdict,missdates = pendingdate(request,request.user.Empid)
    reports = Report.objects.filter(Q(Empid=request.user.Empid,dtcollected=datetime.date.today())| Q(Empid=request.user.Empid,status=0)).order_by('Report_date')
    form  = ReportForm()
    if request.method == 'POST':
        if 'Comments' in str(request.POST):
            print(request.POST)
            id_r = re.search(r'Comments_(\d+)', str(request.POST)).group(1)
            report = get_object_or_404(Report, pk=int(id_r))
            request.POST = request.POST.copy()
            report.Comments = request.POST['Comments_'+id_r]
            request.POST['End_time']  = (datetime.datetime.now()+datetime.timedelta(hours = int('05'), minutes=30)).strftime('%Y-%m-%d %H:%M')
            report.End_time = request.POST['End_time'];report.status = 1
            report.No_hours = hour_calc(report)
            report.save()
            reports = Report.objects.filter(Q(Empid=request.user.Empid,dtcollected=datetime.date.today())| Q(Empid=request.user.Empid,status=0)).order_by('Report_date')
            return render(request,'report/log_create.html',{'pro':data1,'form':form,'reports':reports,'dates' : missdates})
        else:
            request = datainsert(request)
            form = ReportForm(request.POST)
            if form.is_valid():
                form.save()
            reports = Report.objects.filter(Q(Empid=request.user.Empid,dtcollected=datetime.date.today())| Q(Empid=request.user.Empid,status=0)).order_by('Report_date')
            return render(request,'report/log_create.html',{'pro':data1,'form':form,'reports':reports,'dates' : missdates})
    else:
        return render(request,'report/log_create.html',{'pro':data1,'form':form,'reports':reports,'dates' : missdates})

def load_subpro(request):
    project_id = request.GET.get('Project_name')
    subpro = Subproject.objects.filter(Project_name=project_id).order_by('Subproject_name')
    return render(request, 'hr/subpro_dropdown_list.html', {'data': subpro})

def attendence(request):
    if request.user.is_superuser:
        import calendar
        if request.method =="POST":
            month = request.POST['Month']
            if month == '':
                return HttpResponse('<h2> Please Select the Month</h2>')
            a= {};i=1
            Name_detail = CustomUser.objects.filter(~Q(Empid = 1)).values_list('Empid','EmpName')
            for name in Name_detail:
                name = name[1]
                a[name.lower()] = i
                i+=1
            currmonth = datetime.date.today().strftime('%Y-%m')
            year  = currmonth.split('-')[0]
            num_days = calendar.monthrange(int(year), int(month))[1]
            days = [datetime.date(int(year),int(month), day) for day in range(1, num_days+1)]
            rows = Report.objects.filter(~Q(Empid = 1),Report_date__month=int(month)).values_list('Empid','Name','Report_date','Attendence').order_by('Empid')
            if len(rows)==0:
                return HttpResponse("<h2>No reports for Selected Month</h2>")
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
            atten = {'Present':'P','Leave':'EL','Half day leave':'HEL','WO':'WO','OT':'OT','Permission':'P','GH':'GH','WFH':'WFH'}
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
            return render(request, 'review/Attendence.html')
    else:
        return redirect('login')
def export_users_xls(request):
    if request.user.is_superuser:
        if request.user.is_staff:
            teamreport = 1
        else:
            teamreport = None
        if request.method=="POST":
            project_re = request.POST['Project_name'];subpro_re  = request.POST['Subproject_name']
    #         Team = request.POST['Team'];overall = request.POST['overall']
            if 'Team' in  str(request.POST):
                if str(request.POST['Team']) != '' and 'overall' in str(request.POST):
                    return HttpResponse("<h2>Please select Team Or Over all</h2>")
                elif 'Team' in  str(request.POST) and 'overall' not in str(request.POST):
                    rows = Report.objects.filter(Team=request.POST['Team']).values_list('Empid','Name','Primarytask','Team','Report_date','Attendence','Project_name', 'Subproject_name','Task','No_hours','Comments').order_by('Empid')
                elif str(request.POST['Team']) == '' and 'overall' in str(request.POST):
                    rows = Report.objects.all().values_list('Empid','Name','Primarytask','Team','Report_date','Attendence','Project_name', 'Subproject_name','Task','No_hours','Comments').order_by('Team')
            elif str(project_re)!='' or str(subpro_re)!='' or str(request.POST['start_date'])!='' or request.POST['end_date'] != '':
                if str(project_re)!='' and str(subpro_re)!='' and  str(request.POST['start_date'])!='' and request.POST['end_date'] != '':
                    rows = Report.objects.filter(Project_name=project_re,Subproject_name=subpro_re,Report_date__range=[request.POST['start_date'],request.POST['end_date']]).values_list('Empid','Name','Primarytask','Team','Report_date','Attendence','Project_name', 'Subproject_name','Task','No_hours','Comments').order_by('Empid')
                elif str(project_re)!='' and str(subpro_re)=='' and  str(request.POST['start_date'])!='' and request.POST['end_date'] != '':
                    rows = Report.objects.filter(Project_name=project_re,Report_date__range=[request.POST['start_date'],request.POST['end_date']]).values_list('Empid','Name','Primarytask','Team','Report_date','Attendence','Project_name', 'Subproject_name','Task','No_hours','Comments').order_by('Empid')
                elif str(project_re)=='' and str(subpro_re)=='' and  str(request.POST['start_date'])!='' and str(request.POST['end_date']) != '':
                    rows = Report.objects.filter(Report_date__range=[request.POST['start_date'],request.POST['end_date']]).values_list('Empid','Name','Primarytask','Team','Report_date','Attendence','Project_name', 'Subproject_name','Task','No_hours','Comments').order_by('Empid')
                elif str(project_re)=='' and str(subpro_re)!='' and  str(request.POST['start_date'])!='' and request.POST['end_date'] != '':
                    rows = Report.objects.filter(Subproject_name=subpro_re,Report_date__range=[request.POST['start_date'],request.POST['end_date']]).values_list('Empid','Name','Primarytask','Team','Report_date','Attendence','Project_name', 'Subproject_name','Task','No_hours','Comments').order_by('Empid')
                elif str(project_re)!='' and str(subpro_re)!='' and  str(request.POST['start_date']) =='' and request.POST['end_date'] == '':
                    rows = Report.objects.filter(Project_name=project_re,Subproject_name=subpro_re).values_list('Empid','Name','Primarytask','Team','Report_date','Attendence','Project_name', 'Subproject_name','Task','No_hours','Comments').order_by('Empid')
                elif str(project_re)!='' and str(subpro_re)=='' and  str(request.POST['start_date']) =='' and request.POST['end_date'] == '':
                    rows = Report.objects.filter(Project_name=project_re).values_list('Empid','Name','Primarytask','Team','Report_date','Attendence','Project_name', 'Subproject_name','Task','No_hours','Comments').order_by('Empid')
                elif str(project_re)=='' and str(subpro_re)!='' and  str(request.POST['start_date']) =='' and request.POST['end_date'] == '':
                    rows = Report.objects.filter(Subproject_name=subpro_re).values_list('Empid','Name','Primarytask','Team','Report_date','Attendence','Project_name', 'Subproject_name','Task','No_hours','Comments').order_by('Empid')
                else:
                    return HttpResponse("<h2>Please Select Dates Correctly</h2>")
                if len(rows)==0:
                    return HttpResponse("<h2>No reports for Selected Dates</h2>")
            else:
                return HttpResponse("<h2>Please select Project Or Dates</h2><br><h2>Reload current Page</h2>")
            
            response = HttpResponse(content_type='application/ms-excel')
            if str(request.POST['start_date']) !='':
                response['Content-Disposition'] = 'attachment; filename="Reports_'+str(str(request.POST['start_date']))+'.xls"'
            else:
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
        
        
