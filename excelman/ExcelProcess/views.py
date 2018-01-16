from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from .forms import DocumentForm
from .models import Document
import csv
from collections import Counter
from datetime import datetime
import os
from glob import glob
import shutil
import xlsxwriter
from dateutil.parser import parse
import django_excel
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User

#excel=''
fdata=[]
cols = ['All','SM+','M+','SA-']
percent={}
s_case = {'SM+':['SM','AD','D','AVP','VP'], 'M+':['M','SM','AD','D','AVP','VP'], 'SA-':['PAT','PA','A','SA']}	
form_vals={}
conditions=[]
body=[]
lim=0

def is_date(string):
    try: 
        parse(string)
        return True
    except ValueError:
        return False
		
def home(request):
	global cols, fdata, body
	#selected = ''
	#fdata=[]
	cols = ['All','SM+','M+','SA-']
	form = DocumentForm()	
	excel =  [(os.path.getctime('documents/'+x), x) for x in os.listdir("documents/")]
	if len(excel)<1:
		return render(request, 'ExcelProcess/home.html', {'form':form})
	excel.sort()
	excel=excel[-1][1]
	
	fdata=[]
	with open('documents/'+excel, encoding='latin-1') as f:
					xl = csv.reader(f)
					for r in xl:
						fdata.append(r)
					cols.extend(fdata.pop(0))
	
	time = Document.objects.latest('pub_date')
	
	t = [ x for x in zip(*fdata) ]
	branches={}
	i=4
	for x in t:
		branches[cols[i]] = list(set(x[1:]))
		i+=1
	###############################################################################################################################
	
	if request.method=='POST':
		#return fdata
		if request.POST.get("logout"):
			user = User.objects.get(username=request.user)

			for s in Session.objects.all():
				if s.get_decoded().get('_auth_user_id') == user.id:
					s.delete() 
			return render(request, 'registration/login.html')
			
			
		if request.POST.get("upload"): 
			
			#######################################################################################################################
			cols=['All','SM+','M+','SA-']
			fdata=[]
			form = DocumentForm(request.POST, request.FILES)
			t=datetime.now()
			if form.is_valid():
				newdoc = Document(docfile=request.FILES['docfile'], pub_date=t)
				d=str(t.strftime('%Y-%m-%d_%H%M%S'))+'.csv'
				#for f in os.listdir('documents/'):
					#shutil.move('documents/'+f, 'documents/'+d)
				newdoc.save()
				excel = request.FILES['docfile'].name
				excel = excel.replace(' ','_')
				shutil.move('documents/'+excel, 'documents/'+d)
				
				with open('documents/'+d, encoding='latin-1') as f:
					xl = csv.reader(f)
					for r in xl:
						fdata.append(r)
					cols.extend(fdata.pop(0))
					#cols = list(filter(lambda x: x.strip()!='', cols))
				time = Document.objects.latest('pub_date')	
				return render(request, 'ExcelProcess/home.html', {'options':cols, 'branches':branches, 'form':DocumentForm(), 'time':time})
		#############################################################################################################################
		
		elif request.POST.get("generate"):
			#return fdata
			global body, lim
			lim=0
			#body=[]
			form_vals['of']=request.POST['pof']
			form_vals['ag']=request.POST['pag']
			body=process()
			if form_vals['of'] != 'All':
				return render(request, 'ExcelProcess/home.html',{'options':cols,'body': body, 'time':time})
			sbody = [body[0]]
			sbody.extend(body[(lim*20+1):(lim*20+1)+min([len(body),20])])
			lim+=1
					#data = request.POST.get['body']
			#body.insert(0, body[0])
			#download(body)
			#header = body.pop(0)
			#footer= body.pop()
			return render(request, 'ExcelProcess/home.html',{'options':cols, 'branches':branches, 'body': sbody, 'time':time})
		#############################################################################################################################
		elif request.POST.get("Next"):
			#global lim
			sbody = [body[0]]
			sbody.extend(body[min([len(body),(lim*20+1)]):min([len(body),(lim*20+1)+20])])
			lim+=1
			return render(request, 'ExcelProcess/home.html',{'options':cols, 'branches':branches, 'body': sbody, 'time':time})
		elif request.POST.get("download"):
			
			data=[[1,2,3,4,5],[6,7,8,9,10]]
			
			resp = HttpResponse(content_type='xlsx')
			row = 0
			col = 0
			workbook = xlsxwriter.Workbook(resp)
			worksheet = workbook.add_worksheet()
			for r in body:
				col=0
				#w.writerow(r)
				for c in r:
					worksheet.write(row, col, c)
					
					col+=1
				row += 1
			
			resp['Content-Disposition'] = 'attachment;filename=table.xlsx'
			#workbook.save(resp)
			return resp
			
			pass
				
			
		elif request.POST.get("add_to_conditions"):
			#cond=request.POST["all"]+'\n'+ request.POST["field"]
			global conditions
			if request.POST['col']!='All':
				conditions.insert(0, request.POST['col']+'\t'+request.POST['signs']+'\t'+ ",".join(request.POST.getlist("field")))
			
			return render(request, 'ExcelProcess/home.html', {'options':cols, 'form':DocumentForm(), 'branches':branches,  'time':time, 'conditions': conditions}) 
		#############################################################################################################################
			
		elif request.POST.get("clear"):
			#global conditions
			conditions=[]
			return render(request, 'ExcelProcess/home.html', {'options':cols, 'time':time, 'branches':branches,  'form':DocumentForm()})
		#############################################################################################################################
	
	
	return render(request, 'ExcelProcess/home.html', {'options':cols,'form':form, 'branches':branches, 'time':time})
	
	

	
def process():
	
	global fdata, cols
	#fdata = data
	#return fdata
	if len(conditions)<1:
		return generate_csv()#fdata) #generate_without_conditions
	elif 'All Selected' not in conditions:
		#conditions = conditions.strip().split('\n\n')
		conds=[]
		#return [fdata[0]]
		##print conditions, 'aaa'
		for r in conditions:
			##print 'conds_r=',r,'\n\n'
			conds.append(r.split('\t'))
			conds[-1].append(cols.index(conds[-1][0].strip())-4)
			if len(conds[-1])>=3:
				if ',' in conds[-1][2]:
					conds[-1][2]=conds[-1][2].split(',')
					conds[-1][2]=[x.strip() for x in conds[-1][2]]
		
		x=len(conds)
		#return [conds]
		count=0
		for c in conds:
			count+=1
			##print count
			if len(c)>2:
				if c[1]=='<':
					if is_date(c[2].strip()):
						fdata = filter(lambda x: parse(x[c[-1]])<parse(c[2].strip()), fdata)
					else:
						fdata = filter(lambda x: int(x[c[-1]])<int(c[2].strip()), fdata)
				elif c[1]=='>':
					if is_date(c[2].strip()):
						fdata = filter(lambda x: parse(x[c[-1]])>parse(c[2].strip()), fdata)
					else:
						fdata = filter(lambda x: int(x[c[-1]])>int(c[2].strip()), fdata)
					###print filter(lambda x: x[c[-1]]>int(c[2].strip()), fdata)
				elif c[1]=="between":
					###print c[2], type(c[2])
					if is_date(c[2].strip()):
						fdata = filter(lambda x: parse(x[c[-1]]) > parse(c[2][0].strip()) and parse(x[c[-1]]) < parse(c[2][1].strip()), fdata)
					else:
						fdata = filter(lambda x: int(x[c[-1]]) > int(c[2][0].strip()) and int(x[c[-1]]) < int(c[2][1].strip()), fdata)
				elif c[1]=='=':
					###print 'c(-1)=',c[-1], 'c(2)=',c[2]
					
					if isinstance(c[2], list):
						fdata = list(filter(lambda x: x[c[-1]] in c[2], fdata))
					else:
						if is_date(c[2].strip()):
							fdata = list(filter(lambda x: parse(x[c[-1]].strip()) == parse(c[2]), fdata))
						else:
							fdata = list(filter(lambda x: x[c[-1]] == c[2], fdata))
					
					
				##print 'xxx'
#######################################################################################################################################
		return generate_csv()#fdata)
		
def generate_csv():#fdata):
	of = form_vals['of']
	ag = form_vals['ag']
	fname = 'result.csv' #OUTPUT FILE NAME
	global body
	global cols
	global fdata
	body=[]
	if of!='All' and of != 'SM+' and of!='M+' and of!='SA-':	
		of_index = cols.index(of)-4
		#elts = [r[of_index] for r in data]
		
		if ag=='All':
			elts = [r[of_index] for r in fdata]
		#return fdata
			elts = filter(lambda x:x.strip()!='',elts)
			ag='Count'
			percent = dict(Counter(elts)) # total
			header = [of,'Counts','Percent']
			body = []
			body.append(header)
			for k,v in percent.items():
				body.append([k,v,round((v*100.0)/sum(percent.values()),2)])
			footer = ['Total',sum(percent.values())]
			body.append(footer)
			
			return body#{'header':header, 'body':body, 'footer':footer}
		
		else:
			ag_index = cols.index(ag)-4
			xcol=[]
			ycol=[]
			for r in fdata:
				xcol.append(r[of_index])
				ycol.append(r[ag_index])
			xcol = list(filter(lambda x: x.strip()!='' and x!=of,set(xcol)))
			ycol = list(filter(lambda x: x.strip()!='' and x!=ag,set(ycol)))
			x=len(xcol)
			y=len(ycol)
			
			#return [xcol,ycol]
			percent = []
			for i in range(x):
				t=[]
				for j in range(y):
						t.append(0)
				percent.append(t)
			#return percent	
			for r in fdata:
					percent[xcol.index(r[of_index])][ycol.index(r[ag_index])] += 1
			#return percent
			header = [of+'//'+ag]
			header.extend(ycol)
			header.extend(map(lambda x: x+'%', ycol))
			header.extend(['GRAND TOTAL','TOTAL PROPORTION'])
			header = filter(lambda x: x.strip()!='', header)
			
			gtotal = [ sum(x) for x in zip(*percent) ]
			footer=['GRAND TOTAL']    #ADD GRAND TOTAL IN THE END
			footer.extend(gtotal)     #ADD TOTAL OF EACH COLUMN
			footer.extend(map(lambda x:round(x*100.0/sum(gtotal),2),gtotal))  #ADD PERCENT OF EACH COLUMN SUM
			footer.append(sum(gtotal))
			body=[]
			body.append(header)
			for i in range(len(xcol)):
					row_sum = sum(percent[i])
					t=[xcol[i]]
					t.extend(percent[i])
					t.extend(map(lambda x: round(x*100.0/row_sum, 2), percent[i]))
					t.extend([row_sum, round(row_sum*100.0/sum(gtotal),2)])
					body.append(t)
			body.append(footer)		

				######################################################################################################################################
				########################################## S P E C I A L       C A S E S #############################################################
			global s_case
			if of=='Grade' and len(conditions)<1:
				special=[]
				#return body
				for k,v in s_case.items():
					t=[]
					#print xcol
					for e in v:
							if e in xcol:##print percent[xcol.index(e)]
							    t.append(percent[xcol.index(e)])
					sbody = [ sum(x) for x in zip(*t)]
					#sbody.insert(0,k)
					a=list(map(lambda x: round(x*100.0/sum(sbody),2),sbody))
					a.extend([sum(sbody), round(sum(sbody)*100.0/body[-1][-1], 2)])
					sbody.extend(a)
					sbody.insert(0,k)
					special.append(sbody)
					#return [a]
				body.extend(special)
			
			return body#{'header':header, 'body':body, 'footer':footer}#, 'sbody':sbody}
	
	elif of =='SM+' or of=='M+' or of=='SA-':
		#return [fdata[0]]
		if ag=='All':
			k=cols.index('Grade')-4
			count=0
			ttl=len(fdata)
			for row in fdata:
				if row[k] in s_case[of]:
					count+=1
			body.append(['Grades', 'Total', 'Out of', 'Proportion'])
			body.append([of, count, ttl, round(count*100.0/ttl,3)])
			return body
		else:
			ag_index = cols.index(ag)-4
			k=cols.index('Grade')-4
			ycol=[]
			for r in fdata:
				ycol.append(r[ag_index])
			ycol = list(filter(lambda x: x.strip()!='' and x!=ag,set(ycol)))
			y=len(ycol)
			percent = []
			for j in range(y):
					percent.append(0)
			for r in fdata:
					if r[k] in s_case[of]:
						percent[ycol.index(r[ag_index])] += 1
			#return percent	
			header=['Grades//'+ag]
			header.extend(ycol)
			header.extend([x+'%' for x in ycol])
			header.extend(['Grand Total'])
			
			sbody=[of]
			sbody.extend(percent)
			sbody.extend([round(x*100.0/sum(percent),3) for x in percent])
			sbody.extend([sum(percent)])
			body.append(header)
			body.append(sbody)
			return body
			
			
			
	else:
		x=[]
		x.append(cols[4:])
		x.extend(fdata)
		return x
