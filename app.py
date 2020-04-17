from flask import Flask, session, render_template ,url_for
import os
from storage.postgresHelper import PostgresDBHelper
from storage.mongoHelper import MongoDBHelper

from flask import *

postgres_db = PostgresDBHelper()
mongo_db = MongoDBHelper()
mongo_db.updateRoutes()

department_dict = {  'Computer Science':1,'Electrical' :2,'Civil' :4,'Mechanical' :5, 'Chemical' :6,'student_affairs': 7 ,'academic': 8,'None' :9}

app = Flask(__name__)

@app.route('/')
def home():
  return render_template('home.html') 

@app.route('/about')
def about():
  return render_template('about.html')

@app.route('/faculty/<uname>')
def faculty(uname):
	if uname == 'show_list':
		try:
			faculties = postgres_db.fetchEmployees()
			return render_template('faculty.html',name=uname, faculties = faculties  )
		except Exception as e:
			print(e) 
	else:
  		return render_template('faculty.html',name=uname)


@app.route('/register/<typeOfRegistration>')
def register(typeOfRegistration):
	return render_template('register.html', name = typeOfRegistration, name1 = None)

@app.route('/register_emp')
def register_emp():
	return render_template('register.html', name ='employee', name1 = None)

@app.route('/register_dep')
def register_dep():
	return render_template('register.html', name ='department', name1 = None)

@app.route('/log')
def log():
	applications =postgres_db.fetch_log()
	return render_template('log.html', applications = applications)

@app.route('/special_faculty/<section>')
def special_faculty(section):
	if section == 'view':
		director = postgres_db.get_current_cc_faculty(type =1)
		deans = postgres_db.get_current_cc_faculty(type =2)
		hods = postgres_db.get_current_cc_faculty(type=3)

		cc_faculty =[]
		cc_faculty.append(director)
		cc_faculty.append(deans)
		cc_faculty.append(hods)
		return render_template('special_faculty.html',name=section, cc_faculty = cc_faculty)
	else:
 		 return render_template('special_faculty.html',name=section)


@app.route('/admin', methods=['GET', 'POST'])
def admin():
	error = None
	if request.method == 'POST':
		if request.form['username'] != 'admin' or request.form['password'] != 'admin':
			return render_template('show_info.html', message = 'Invalid Credentials. Please try again.')
		else:
			return render_template('admin.html' , name='success', error = error)

	return render_template('admin.html', error=error)

@app.route('/update/<field>', methods = ['GET', 'POST'])
def generalUpdate(field):
	error = False
	if field == 'path':
		return render_template('admin.html', name = 'updateRoute')
	if field == 'route':
		if request.method == 'POST':
			try:
				mongo_db.updateRoutes(request.form['normal_faculty_final_reviewer'], 
					request.form['hod_final_reviewer'], request.form['dean_final_reviewer'])
			except Exception as e:
				error = True
				print(e)
				return render_template('show_info.html', message = 'Could not update routes. See terminal for more details')
			if not error:
				return render_template('show_info.html', message = 'Routes were successfully updated')
	if field == 'leaves' :
		return render_template('admin.html', name = 'update_leaves')			


@app.route('/<field>/<dept>', methods = ['GET', 'POST'])
def cc_faculty_desks(field, dept):
	applications = []
	if field == 'hod':
		applications = postgres_db.fetchApplications('hod', dept)
	if field == 'dean':
		applications = postgres_db.fetchApplications('dean')
	if field == 'director':
		applications = postgres_db.fetchApplications('director')
	comments = ""	
	if applications != []:
		comments = mongo_db.getComment(applications[0])
	return render_template('faculty.html', section = "processCVs", applications = applications ,comments = comments)



@app.route('/updateLeaveStatus', methods = ['GET', 'POST'])
def updateLeaveStatus():
	if request.method == 'POST':
		try:
			assign_status = request.form['assign_status']
			comment = request.form['comment']
			emp_id = request.form['id']
			assign_status = int(assign_status)
			print('Update Leaves emp_id {}'.format(emp_id))
			application_no, comment_by = postgres_db.updateLeaveStatus(emp_id, assign_status)

			mongo_db.insertComment(application_no ,comment, comment_by)

			return render_template('show_info.html', emp_id = emp_id, message = '''The leave application has successfuly been
						updated by you!''')
		except Exception as e:
			print(e)
			return render_template('show_info.html', emp_id = emp_id, message = '''The leave application could not be
						updated !!!''')

@app.route('/login', methods=['GET', 'POST'])
def login():
	 return render_template('login.html' , name="")


	 

@app.route('/verify', methods=['GET', 'POST'])
def verify():
	error = None
	if request.method == 'POST':
		result = postgres_db.getLoginDetails(email = request.form['email'])
		
		if result == None:	#result[4] is e-mail
			return render_template('show_info.html', message = "Please ask Admin to register you as a faculty.")
		else:
			if result[5] == request.form['password']:	#result[5] is Password

				url= "/profile/"+ str(result[4]) + '/verified'
				special_url = "/profile/"+ str(result[4]) + "/special"
				emp_type = postgres_db.getEmployeeType(result[0])
				
				return render_template('login.html',name= "success",profile_url = url, 
					profile_special = special_url, emp_type = emp_type)
			else:
				return render_template('show_info.html', message = "Invalid Credentials. Please Login Again.")


@app.route('/profile/<uemail>/<section>')
def profile(uemail,section = ''):
		result = postgres_db.getLoginDetails(email = uemail)
		lastApplication = postgres_db.getLastLeaveApplication(result[0])
		comments = []
		if lastApplication != []:
			comments = mongo_db.getComment(lastApplication[0])
		cv = mongo_db.getCV(result[0])
		emp_type = postgres_db.getEmployeeType(result[0])
		
		update_cv_url = '/cv/' + str(result[0])
		return render_template('faculty.html',   emp_details = result, result = cv, section = section, 
				update_cv_url = update_cv_url,  lastApplication = lastApplication, emp_type = emp_type, comments = comments )

@app.route('/cv/<emp_id>')
def cv(emp_id):
	update_employee_cv_url = '/updateCV/' + str(emp_id)
	return render_template('register.html' , name='success', name1 = 'employee', emp_id = emp_id, 
			update_employee_cv_url = update_employee_cv_url, error = None)

@app.route('/updateCV/<emp_id>', methods = ['GET', 'POST'])
def updateCV(emp_id):
	error = False
	if request.method == 'POST':
		try:
			about_faculty = request.form['about_faculty']
			research_interests = request.form['research_interests']
			publications = request.form['publications']
			grants = request.form['grants']
			awards = request.form['awards']
			teaching_experience = request.form['teaching_experience']

			mongo_db.updateCV(emp_id, about_faculty, research_interests, publications, grants, awards, teaching_experience)

		except Exception as e:
			error = True
			print(e)
	if not error:
		return render_template('show_info.html', message = "Your CV has been Successfully Updated")
	else:
		return render_template('show_info.html', message = "Could Not Update. See Terminal for more details")

@app.route('/registerDepartment', methods = ['GET', 'POST'])
def registerDepartment():
	error = False
	if request.method == 'POST':
		try: 
			department = request.form['dept_name']
			postgres_db.insertDepartment(name = department)
		except Exception as e:
			error = True
			print(e)
	if not error:
		return render_template('show_info.html', message = "Department Registration Successful")
	else:
		return render_template('show_info.html', message = "Could Not Register. See Terminal for more details")

@app.route('/registerEmployee', methods=['GET', 'POST'])
def registerEmployee():
	error = False
	if request.method == 'POST':
		try:
			first_name = request.form['firstname']
			last_name = request.form['lastname']
			email = request.form['email']
			password = request.form['password']
			start_date = request.form['start_date']
			end_date = request.form['end_date']
			dept = request.form['department']
			username = first_name + '_' + start_date

			postgres_db.insertEmployee(username, first_name, last_name, email, password, start_date, end_date, dept = department_dict[dept])
		except Exception as e:
			error = True
			print(e)
	if not error:
		return render_template('show_info.html', message = "Employee Registration Successful")
	else:
		return render_template('show_info.html', message = "Could Not Register. See Terminal for more details")

@app.route('/update_hod', methods = ['GET', 'POST'])
def update_hod():
	error = False
	if request.method == 'POST':
		try: 
			department =  request.form['department']
			employee_id = request.form['id']
			result = postgres_db.getLoginDetails(id = employee_id)
			if(result == []):
				return render_template('show_info.html' , message = "Enter a valid Employee ID")
			if result[8] == department_dict[department] :
				postgres_db.update_hod_table(department_dict[department], employee_id)
			else: 
				return render_template('show_info.html' , message = "Employee should be employee of the same Department !!")
		except Exception as e:
			error = True
			print(e)
	if not error:
		return render_template('show_info.html' , message = "HOD was successfully updated.")
	else:
		return render_template('show_info.html' , message = "Could Not Update. See Terminal for more details")

@app.route('/update_dean', methods = ['GET', 'POST'])
def update_dean():
	error = False
	if request.method == 'POST':
		try: 
			department = request.form['section']
			employee_id = request.form['id']

			result = postgres_db.getLoginDetails(id = employee_id)
			if(result == []):
				return render_template('show_info.html' , message = "Enter a valid Employee ID")
			
			postgres_db.update_dean_table(department_dict[department], employee_id)
			# postgres_db.update_dean_table(department, employee_id)

		except Exception as e:
			error = True
			print(e)
	if not error:
		return render_template('show_info.html' , message = "CC_Faculty was successfully updated.")
	else:
		return render_template('show_info.html' , message = "Could Not Update. See Terminal for more details")

@app.route('/update_director', methods = ['GET', 'POST'])
def update_director():
	error = False
	if request.method == 'POST':
		try:  
			employee_id = request.form['id'] 
			result = postgres_db.getLoginDetails(id = employee_id)
			if(result == []):
				return render_template('show_info.html' , message = "Enter a valid Employee ID")
			postgres_db.update_director_table(employee_id)

		except Exception as e:
			error = True
			print(e)
	if not error:
		return render_template('show_info.html' , message = "Director Post was successfully updated.")
	else:
		return render_template('show_info.html' , message = "Could Not Update. See Terminal for more details")

@app.route('/apply_leave', methods = ['GET', 'POST'])
def apply_leave():
    error = False
    try:
        if request.method == 'POST':
            iid = request.form['id']
            if iid == 'add_comment':
                emp_id = request.form['emp_id']
                app_no = request.form['app_no']
                comment = request.form['add_comment']
                mongo_db.insertComment(int(app_no), comment, comment_by='employee')
                postgres_db.updateLeaveStatus(emp_id, 3)
                return render_template('show_info.html', message = '''Your Leave Application has been put again for review .''')
            
            emp_id = request.form['id']
            start_date = request.form['start_date']
            days = request.form['days']	
            comment = request.form['comment']
            emp_id =int(emp_id)

            emp_details = postgres_db.getEmployee(emp_id)
            this_year_remaining_leaves = emp_details[9]
            next_year_remaining_leaves = emp_details[10]
            ##apply database action
            emp_type = postgres_db.getEmployeeType(emp_id)
            print('Employee Type: {}'.format(emp_type))
            final_review_by = mongo_db.getRoute(emp_type)
            print('Final Review By: {}'.format(final_review_by))
            
            if emp_type == 'faculty':
                postgres_db.applyForLeave(emp_id, start_date, days, final_review_by, emp_type)
            if emp_type == 'hod':
                postgres_db.applyForLeave(emp_id, start_date, days, final_review_by, emp_type, hod_state=-1, dean_state= 0)
            if emp_type == 'dean':
                postgres_db.applyForLeave(emp_id, start_date, days, final_review_by, emp_type, hod_state=-1,
                        dean_state = -1, director_state= 0)
            
            # status = 10 to get Application_no
            application_no = postgres_db.updateLeaveStatus(emp_id, 10)
            mongo_db.insertComment(application_no, comment)

            days = int(days)

            if this_year_remaining_leaves < days :
                borrow=(days - this_year_remaining_leaves)

                if next_year_remaining_leaves >= borrow  :
                    url = '/borrow_leave/' + str(emp_id) + '/' + str(borrow)
                    return render_template('faculty.html',section='borrow',url_for_borrow = url,borrow=borrow)
                else: 
                    return render_template('show_info.html', message = "Could Not apply for leave. Leave limit exceeded !!")    

    except Exception as e:
        error = True
        print(e)
    if not error:
        return render_template('show_info.html', message = '''Your Leave Application has been put for review by the concerned authorities. View its status on your profile page.''')
    else:
        return render_template('show_info.html', message = "Could Not apply for leave. See Terminal for more details")


@app.route('/borrow_leave/<emp_id>/<days>', methods = ['GET', 'POST'])
def borrow_leave(emp_id,days):
    error = False
    if request.method == 'POST':
        try:
            status = request.form['status']  
            application = postgres_db.updateLeaveStatus(emp_id,10)  #status= 10
            
            if status == "yes": 
                postgres_db.setBorrow(application,days,1)
                return render_template('show_info.html', message = "Leave and Borrow Leave Applications submitted")
            else: 
                postgres_db.setBorrow(application,days,0)
                return render_template('show_info.html', message = "Leave ap-plication cancelled.")
        except Exception as e:
            error = True
            print(e)

@app.route('/update_max_leave', methods = ['GET', 'POST'])
def update_max_leave():
	error = False
	if request.method == 'POST':
		try: 
			year = request.form['year'] 
			emp_id = request.form['emp_id'] 
			days = request.form['days']  
			postgres_db.update_max_leave(year,emp_id,days)

		except Exception as e:
			error = True
			print(e)
	if not error:
		return render_template('show_info.html', message = " Leave Limit Update Successful")
	else:
		return render_template('show_info.html', message = "Could Not Register. See Terminal for more details")

