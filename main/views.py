
import re
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify, Flask, current_app, g, send_file
from flask_login import login_required, current_user
from flask_login.utils import login_fresh
from sqlalchemy.sql.expression import null
from werkzeug.wrappers import Request
from .models import Announcement, Instructor, Module, User, Message, Course, StudentCourses, Organization, UserOrganizations, Assignment, File
from flask_sqlalchemy import SQLAlchemy 
from sqlalchemy.sql import text
from .__init__ import app, db
from main import models
from io import BytesIO

#engine = create_engine('sqlite:///db.sqlite')
views = Blueprint('views', __name__)





#This can be a sample for of data that is in class course, we could query a table where user.id in enrolledID
course = [
    {
        'id' : 100,
        'name' : 'C100 - Intro to Computer Science',
        'teacherId' : 500,
        'enrolledId' : [1000, 1001, 1002, 1003, 1004, 1005]

    } , 
    {
        'id' : 101,
        'name' : 'C101 - Intro to Biology',
        'teacherId' : 501,
        'enrolledId' : [1006, 1007, 1008, 1009, 1010, 1011]

    } , 
    {
        'id' : 101,
        'name' : 'C101 - Intro to Biology',
        'teacherId' : 501,
        'enrolledId' : [1006, 1007, 1008, 1009, 1010, 1011]

    }, 
    {
        'id' : 101,
        'name' : 'C101 - Intro to Biology',
        'teacherId' : 501,
        'enrolledId' : [1006, 1007, 1008, 1009, 1010, 1011]

    }, 
    {
        'id' : 101,
        'name' : 'C101 - Intro to Biology',
        'teacherId' : 501,
        'enrolledId' : [1006, 1007, 1008, 1009, 1010, 1011]
    }
]
# Adding Course Events to DB


@views.route('/')
def index():
    return render_template('index.html')

@views.route('/database')
def userData():

    query = User.query.filter(User.email == session['email']).first()
    data = { 'id' : query.id, 'name' : query.name, 'email' : query.email}
    
    return render_template('database.html', data=data)




@views.route('/profile')
@login_required
def profile():
    #if user is admin query Organization table rather than UserOrganizations 
    query = User.query.filter(User.email == session['email']).first()
    currentUser = { 'id' : query.id, 'name' : query.name, 'email' : query.email, 'userType' : query.userType}

    if query.userType == 'Admin':
        userO = Organization.query.filter(currentUser['id'] == Organization.adminId)
        #organizationList = []
        organizationNames = []
        for o in userO :

            organizationNames.append(o.name)
      
    else:
        userO = UserOrganizations.query.filter(currentUser['id'] == UserOrganizations.userId)
        organizationList = []

        for o in userO :
            organizationList.append(o.organization)

        organizationNames = []
        for name in organizationList :
            organizationNames.append(name.name)

    return render_template('profile.html', current=currentUser, organizationNames=organizationNames)

@views.route('/courses')
@login_required
def courses():

    coursesDict = []
    current = User.query.filter(User.email == session['email']).first()
    if current.userType == 'Instructor' :
        intructorCourses = Course.query.filter(Course.instructorId == current.id)
        coursesDict = []

        for course in intructorCourses :
            currentCorse = {
                'id' : course.id,
                'name' : course.name,
                'teacherId' : course.instructorId,
            }
            enrolledStudents = []

            for s in course.students :
                enrolledStudents.append(s.studentId)
            currentCorse['enrolledId'] = enrolledStudents
            coursesDict.append(currentCorse)


    elif current.userType == 'Student' :
        studentCourses = StudentCourses.query.filter(StudentCourses.studentId == current.id)
        # TODO FINISH STUDENT COURSE LIST IMPLENTATION

        coursesDict = []

        for s in studentCourses :
            currentCorse = {
                'id' : s.course.id,
                'name' : s.course.name,
                'teacherId' : s.course.instructorId,
            }
            coursesDict.append(currentCorse)

    return render_template('courses.html', course=coursesDict)

@views.route('/courses', methods=['GET', 'POST'])
@login_required
def courses_post():

    if request.method == 'POST':
        rerouteName = request.form['courseReroute']
        return redirect(url_for('views.coursePage', rerouteName=rerouteName))


@views.route('/coursePage/<rerouteName>')
@login_required
def coursePage(rerouteName):
    session['rerouteName'] = rerouteName

    current = User.query.filter(User.email == session['email']).first()
    courseQuery = Course.query.filter(Course.id == int(rerouteName)).first()
    teacherQuery = User.query.filter(User.id == courseQuery.instructorId).first()
    courseAnnouncements = Announcement.query.filter(courseQuery.name == Announcement.name)

    courseInfo = {'courseId' : rerouteName, 'courseNumber' : courseQuery.name, 'instructorName' : teacherQuery.name, 'org' : courseQuery.organization, 
    'courseDescription' : courseQuery.description, 'intstructorEmail' : teacherQuery.email}

    announcementList = []
    countA = (Announcement.query.filter(courseQuery.name == Announcement.name).count()) - 1 
    lengthA = countA
    if lengthA > 3 :
        while countA > (lengthA - 3) :
            announ = courseAnnouncements[countA]
            time = str(announ.dateTime)
            time = time[0:16]
            currentAnnoun = {'courseName' : announ.name, 'subjectLine' : announ.subject, 'announcement' : announ.description, 'time' : time}
            announcementList.append(currentAnnoun)
            countA -= 1
    else :
        for announ in courseAnnouncements :
            time = str(announ.dateTime)
            time = time[0:16]
            currentAnnoun = {'courseName' : announ.name, 'subjectLine' : announ.subject, 'announcement' : announ.description, 'time' : time}
            announcementList.append(currentAnnoun)


    courseInfo['announcements'] = announcementList

    courseModuels = Module.query.filter(courseQuery.id == Module.courseId)
    moduleList = []
    
    countM = (Module.query.filter(courseQuery.id == Module.courseId)).count() - 1 
    lengthM = countM
    if lengthM > 3 :
        while countM > (lengthM - 3) :
            mod = courseModuels[countM]
            currentMod= {'moduleName' : mod.name, 'mDesc' : mod.description, 'mId' : mod.id}
            moduleList.append(currentMod)
            countM -= 1
        courseInfo['modules'] = moduleList
    else :
        for m in courseModuels :
            currentMod= {'moduleName' : m.name, 'mDesc' : m.description, 'mId' : m.id}
            moduleList.append(currentMod)
        courseInfo['modules'] = moduleList

    courseAssignment = Assignment.query.filter(courseQuery.id == Assignment.courseId)
    assignmentList = []
    countAs = (Assignment.query.filter(courseQuery.id == Assignment.courseId)).count() - 1 
    lengthAs = countAs
    if lengthAs > 3 :
        while countAs > (lengthAs - 3) :
            a = courseAssignment[countAs]
            currentAs= {'name' : a.name, 'desc' : a.description, 'dueDate' : a.dueDate, 'id' : a.id}
            assignmentList.append(currentAs)
            countAs -= 1
        courseInfo['assignments'] = assignmentList
    else :
        for a in courseAssignment :
            currentAs= {'name' : a.name, 'desc' : a.description, 'dueDate' : a.dueDate, 'id' : a.id}
            assignmentList.append(currentAs)
        courseInfo['assignments'] = assignmentList

    if current.id == courseQuery.instructorId :
        return render_template('coursePageInstructor.html', courseInfo=courseInfo)
    else : 
        return render_template('coursePage.html', courseInfo=courseInfo)

@views.route('/courseAddition')
def course_addition() :

    current = User.query.filter(User.email == session['email']).first()
    if current.userType == 'Admin' or current.userType == 'Instructor' :

        organizationS = UserOrganizations.query.filter(UserOrganizations.userId == current.id)
        oList = []
        for o in organizationS : 
            orgs = Organization.query.filter(Organization.id == o.organizationId).first()
            oList.append(orgs.name)


        return render_template('courseAddition.html', organizationS = oList)
    else :
        return redirect(url_for('views.profile'))

@views.route('/courseAddition', methods=['POST'])
@login_required
def courses_addition_post():

    current = User.query.filter(User.email == session['email']).first()
    course = request.form.get('course')
    semester = request.form.get('semester')
    organizationName = request.form.get('organization')
    description = request.form.get('description')
    instructorId = current.id
     
    new_course = Course(name=course, instructorId=instructorId, description=description, semester=semester, organization=organizationName)
    db.session.add(new_course)
    db.session.commit()
           

    return redirect(url_for('views.courses'))



@views.route('/announcements')
def announcement_page():

    classId = session['rerouteName']

    current = User.query.filter(User.email == session['email']).first()
    course = Course.query.filter(Course.id == session['rerouteName']).first()
    courseQuery = Course.query.filter(Course.id == int(classId)).first()
    teacherQuery = User.query.filter(User.id == courseQuery.instructorId).first()
    courseAnnouncements = Announcement.query.filter(courseQuery.name == Announcement.name)

    courseInfo = {'courseId' : classId, 'courseNumber' : courseQuery.name, 'instructorName' : teacherQuery.name, 'org' : courseQuery.organization, 
    'courseDescription' : courseQuery.description, 'intstructorEmail' : teacherQuery.email, 'courseName' : course.name}

    announcementList = []
    for announ in courseAnnouncements :
        time = str(announ.dateTime)
        time = time[0:16]
        currentAnnoun = {'courseName' : announ.name, 'subjectLine' : announ.subject, 'announcement' : announ.description, 'time' : time}
        announcementList.append(currentAnnoun)

    if current.id == courseQuery.instructorId :
        return render_template('announcmentInsructor.html', announcementList=announcementList, courseInfo=courseInfo)
    else : 
        return render_template('announcments.html', announcementList=announcementList, courseInfo=courseInfo)

@views.route('/newAnnouncement')       
def new_announcment() :
           
    course = Course.query.filter(Course.id == session['rerouteName']).first()
    courseName = course.name   
    return render_template('newAnnouncement.html', courseName=courseName)

@views.route('/newAnnouncement', methods=['POST'])
def new_announcment_post():

    current = User.query.filter(User.email == session['email']).first()
    courseName = session['rerouteName']
    subjectLine = request.form.get('subjectLine')
    announcement = request.form.get('Announcement')
    
    try :
        course = Course.query.filter(Course.id == courseName).first()

        if(course.instructorId == current.id):
            new_announcment = Announcement(name=course.name, description=announcement, subject=subjectLine, courseId=course.id)
            db.session.add(new_announcment)
            db.session.commit()
        else :
            flash('Sorry but you are not in the Instructor of this' + str(course.name))
            return redirect(url_for('views.new_announcment'))

    except :
        flash('Course Not Found! Try Again!')
        return redirect(url_for('views.new_announcment'))


    return redirect(url_for('views.coursePage', rerouteName=course.id))

@views.route('/newAssignment')
def new_assignment() :
    course = Course.query.filter(Course.id == session['rerouteName']).first()
    modules = Module.query.filter(Module.courseId == course.id)
    moduleNames = []
    for m in modules :
        moduleNames.append(m.name)

    
    
    return render_template('newAssignment.html', courseName = course.name, moduleNames=moduleNames)

@views.route('/newAssignment', methods=['POST'])
def new_assignment_post():

    current = User.query.filter(User.email == session['email']).first()
    assignmentName = request.form.get('assignmentName')
    description = request.form.get('description')
    dueDate = request.form.get('dueDate')
    moduleName = request.form.get('modlueSelection')
    course = Course.query.filter(Course.id == session['rerouteName']).first()
    var = request.files['file']

    newFile = File(name=var.filename, data=var.read(), userId=current.id)
    if newFile.name != '':
        db.session.add(newFile)
        db.session.commit()

    
    if(course.instructorId == current.id):
        moduleId = Module.query.filter(Module.name == moduleName).first()
        new_assignment = Assignment(name=assignmentName, description=description, courseId=course.id, dueDate=dueDate, moduleId=moduleId.id, fileLoc=newFile.id)
        db.session.add(new_assignment)
        db.session.commit()
    else :
        flash('Sorry but you are not in the Instructor of this' + str(course.name))
        return redirect(url_for('views.new_assignment'))


    return redirect(url_for('views.coursePage', rerouteName=course.id))

@views.route('/assignmentPage', methods=['POST'])
def assignmentSpecPage_post():

    

    if request.method == 'POST' and request.form['fileDownload']:
        assignmentId = session['assignmentId']
        assignment = Assignment.query.filter(Assignment.id == assignmentId).first()
        fileData = File.query.filter(File.id == assignment.fileLoc).first()
        return send_file(BytesIO(fileData.data), attachment_filename=fileData.name, as_attachment=True)

    elif request.method == 'POST' and request.form['subDownload']:
        current = User.query.filter(User.email == session['email']).first()
        assignmentId = session['assignmentId']
        assignment = Assignment.query.filter(Assignment.id == assignmentId).first()
        fileData = File.query.filter(File.userId == current.id and File.assignmentId == assignment.id).first()
        return send_file(BytesIO(fileData.data), attachment_filename=fileData.name, as_attachment=True)
    
    
    current = User.query.filter(User.email == session['email']).first()
    assignmentId = session['assignmentId']
    assignment = Assignment.query.filter(Assignment.id == assignmentId).first()
    
    var = request.files['file']
    newFile = File(name=var.filename, data=var.read(), userId=current.id, assignmentId=assignment.id)
    if newFile.name != '':
        db.session.add(newFile)
        db.session.commit()
        
    return redirect(url_for('views.assignmentSpecPage'))
    

@views.route('/assignmentPage')
def assignmentSpecPage():

    assignmentId = session['assignmentId']
    assignment = Assignment.query.filter(Assignment.id == assignmentId).first()
    course = Course.query.filter(Course.id == assignment.courseId).first()
    current = User.query.filter(User.email == session['email']).first()
    #send_file(BytesIO(fileData.data), attachment_filename=fileData.name, as_attachment=True)

  
    aDict = {
            "name" : assignment.name,
            "desc" : assignment.description,
            "dueDate" : assignment.dueDate,
            "fileLoc" : assignment.fileLoc,
            "aId" : assignment.id,
            "cName" : course.name
    }
    try :
        fileData = File.query.filter(File.id == assignment.fileLoc).first()
        aDict["fileName"] = fileData.name
    except :
        aDict["fileName"] = None

    

    if current.id == course.instructorId :
        return render_template('assignmentsPageInstructor.html',id=assignmentId, aDict=aDict)
    else : 

        submittedFile = File.query.filter(current.id == File.userId and assignment.id == File.assignmentId).first()

        if submittedFile is not None :
            subCheck = True
            aDict["subName"] = submittedFile.name
        else :
            subCheck = False

        aDict["subCheck"] = subCheck
        

        return render_template('assignmentsPage.html', id=assignmentId, aDict=aDict)


    

@views.route('/assignments', methods=['POST'])
def assignment_page_post():

    if request.method == 'POST':
        aId = request.form['aId']
        session['assignmentId'] = aId
        return redirect(url_for('views.assignmentSpecPage'))

@views.route('/assignments')
def assignment_page():
    course = Course.query.filter(Course.id == session['rerouteName']).first()
    assignments = Assignment.query.filter(Assignment.courseId == course.id)
    

    aList = []

    for assign in assignments :
        aDict = {
            "name" : assign.name,
            "desc" : assign.description,
            "dueDate" : assign.dueDate,
            "aId" : assign.id
        }

        aList.append(aDict)


    return render_template('assignments.html', courseName = course.name, aList = aList)

@views.route('/modulePage', methods=['POST'])
def moduleSpecPage_post():

    if request.method == 'POST' and request.form['fileDownload']:
        mId = session['moduleId']
        mod = Module.query.filter(Module.id == mId).first()
        fileData = File.query.filter(File.id == mod.fileLoc).first()
        return send_file(BytesIO(fileData.data), attachment_filename=fileData.name, as_attachment=True)

@views.route('/modulePage')
def modulesSpecPage():
    mId = session['moduleId']
    m = Module.query.filter(Module.id == mId).first()
    assignments = Assignment.query.filter(Assignment.moduleId == m.id)
    course = Course.query.filter(Course.id == m.courseId).first()
    current = User.query.filter(User.email == session['email']).first()
    
    


    
    mDict= {'name' : m.name, 'desc' : m.description, 'id' : m.id, 'cName' : course.name, "fileLoc" : m.fileLoc}
    aList = []
    for a in assignments :
        aList.append(a)
        mDict["aList"] = aList
    
    try :
        fileData = File.query.filter(File.id == m.fileLoc).first()
        mDict["fileName"] = fileData.name
    except :
        mDict["fileName"] = None

    if current.id == course.instructorId :
        return render_template('modulePageInstructor.html', courseName = course.name, mDict = mDict)
    else : 
        return render_template('modulePage.html', courseName = course.name, mDict = mDict)

    

@views.route('/modules', methods=['POST'])
def modules_page_post():

    if request.method == 'POST' and request.form['mId'] :
    
        mId = request.form['mId']
        session['moduleId'] = mId
        return redirect(url_for('views.modulesSpecPage'))

@views.route('/modules')
def modules_page():
    course = Course.query.filter(Course.id == session['rerouteName']).first()
    models = Module.query.filter(Module.courseId == course.id)
    

    mList = []

    for m in models :
        mDict= {'name' : m.name, 'desc' : m.description, 'id' : m.id}
        aList = []
        assignments = Assignment.query.filter(Assignment.moduleId == m.id)
        for a in assignments :
            aList.append(a)
            mDict["aList"] = aList
        mList.append(mDict)


    return render_template('modules.html', courseName = course.name, mList = mList)

@views.route('/newModule')
def new_module() :
    course = Course.query.filter(Course.id == session['rerouteName']).first()
    
    
    return render_template('newModule.html', courseName = course.name)

@views.route('/newModule', methods=['POST'])
def new_module_post():

    current = User.query.filter(User.email == session['email']).first()
    moduleName = request.form.get('moduleName')
    course = Course.query.filter(Course.id == session['rerouteName']).first()
    description = request.form.get('description')
    var = request.files['file']
    newFile = File(name=var.filename, data=var.read(), userId=current.id)
    if newFile.name != '':
        db.session.add(newFile)
        db.session.commit()

    
    if(course.instructorId == current.id):
        new_module = Module(name=moduleName, courseId=course.id, description=description, fileLoc=newFile.id)
        db.session.add(new_module)
        db.session.commit()
    else :
        flash('Sorry but you are not in the Instructor of this' + str(course.name))
        return redirect(url_for('views.new_module'))


    return redirect(url_for('views.coursePage', rerouteName=course.id))
    




@views.route('/courseStudentAddition', methods=['POST'])
@login_required
def courses_student_addition_post():

    try :
        courseId = session['rerouteName'] 
        course = Course.query.filter(Course.id == courseId).first()
        studentEmail = request.form.get('studentEmail')
        student = User.query.filter(User.email == studentEmail).first()

        new_student = StudentCourses(courseId=course.id, studentId=student.id)
        db.session.add(new_student)
        db.session.commit()

    except :
        flash('No User with this Email Adress! Please try again!')
        return redirect(url_for('views.course_student_addition'))
    
    return redirect(url_for('views.courses'))

@views.route('/courseStudentAddition')
def course_student_addition() :

    courseId = session['rerouteName'] 
    course = Course.query.filter(Course.id == courseId).first()


    current = User.query.filter(User.email == session['email']).first()
    if current.userType == 'Admin' or current.userType == 'Instructor' :
        return render_template('courseStudentAddition.html', courseName = course.name)
    else :
        return redirect(url_for('views.profile'))

@views.route('/index')
@login_required
def MainP():
    #This is our main page for calander and general organization
    return render_template('index.html', name=current_user.name)

@views.route('/messages')
@login_required
def messages():
    
    email = session['email']
    currentQuery = User.query.filter(User.email == session['email']).first()
    currentName = currentQuery.name
    currentId = currentQuery.id
    currentEmail = currentQuery.email
    messageQuery = Message.query.filter(Message.recipientId == currentId).all()
    sentQuery = Message.query.filter(Message.senderId == currentId).all()


    if messageQuery is not None : 
        messageList = []
        for i in messageQuery :
            newMessage = {'id' : i.id, 'messageText' : i.message ,'senderId'  : i.senderId, 'recipientId': i.recipientId, 'date' : " ", 'isRead': i.isRead }
            
            senderQuery = User.query.filter(User.id == i.senderId).first()
            senderName = senderQuery.name
            senderEmail = senderQuery.email
            newMessage['name'] = senderName
            newMessage['recipient'] = currentEmail
            newMessage['sender'] = senderEmail
            messageList.append(newMessage)
        
        sentList = []
        for i in sentQuery :
            newMessage = {'id' : i.id, 'messageText' : i.message ,'senderId'  : i.senderId, 'recipientId': i.recipientId, 'date' : "  ", 'isRead': i.isRead }
            
            recipientQuery = User.query.filter(User.id == i.recipientId).first()
            recipientName = recipientQuery.name
            recipientEmail = recipientQuery.email
            newMessage['name'] = recipientName
            newMessage['recipient'] = recipientEmail
            newMessage['sender'] = currentEmail
            sentList.append(newMessage)
    


        return render_template('messages.html', message=messageList, sent=sentList, email=email, currentName=currentName)
    else :
        return render_template('messagesNone.html')

@views.route('/sendMessage')
@login_required
def sendMessage() :
    return render_template("sendMessage.html")

@views.route('/sendMessage', methods=['POST'])
def message_post():

    query = User.query.filter(User.email == session['email']).first()
    currentUser = { 'id' : query.id, 'name' : query.name, 'email' : query.email, 'userType' : query.userType}

    newMessage = request.form.get('message')
    senderId = query.id

    recipientEmail = request.form.get('email')
    try :
        recipientQuery = User.query.filter(User.email == recipientEmail).first()
        recipientId = recipientQuery.id
    
        new_message = Message(message=newMessage, senderId=senderId, recipientId=recipientId)
        db.session.add(new_message)
        db.session.commit()
    except :
        flash('No User in Organization with this Email Adress! Please try again!')
        return redirect(url_for('views.sendMessage'))


    return redirect(url_for('views.messages'))

#organization back-end implementation
@views.route('/organizations') #organizations page lists all organizations associated with the admin 
@login_required
def organizations(): 
    current = User.query.filter(User.email == session['email']).first() #get current user (admin)
    if current.userType == 'Admin':
        adminId = current.id
        organizations = Organization.query.filter(Organization.adminId==adminId) #locate all organizations associated with admin
        
        return render_template('organizations.html', organizations=organizations) #returns organizations list to organizations page
    
    else:
        return redirect(url_for('views.profile')) #if user is not an admin, they are redirected to the profile page 

@views.route('/organizations', methods=['GET', 'POST'])
@login_required
def organization_post():

    if request.method == 'POST':
        rerouteName = request.form['orgPageReroute']
        return redirect(url_for('views.organizationPage', rerouteName=rerouteName))
        

@views.route('/organizationPage/<rerouteName>')
@login_required
def organizationPage(rerouteName):

    current = User.query.filter(User.email == session['email']).first()
    session['organization'] =  int(rerouteName)
    orgQuery = Organization.query.filter(Organization.id == int(rerouteName)).first()
    userQuery = UserOrganizations.query.filter(UserOrganizations.organizationId == int(rerouteName))
    users = []
    
    for i in userQuery:
        users.append(i.userId) #get user ids associated with organizations
        print(users)

    userList = []
    for j in range(len(users)):
        query = User.query.filter(User.id == users[j]).first() #find user email and provide it to organization
        name = query.name + ",  " + query.email
        userList.append([query.name, query.email])
    print(userList)
    orgInfo = {'name' : orgQuery.name, 'admin' : current.email, 'users' : userList}

    return render_template('organizationPage.html', orgInfo=orgInfo, rerouteName=rerouteName)

@views.route('/organizationPage', methods=['GET', 'POST'])
@login_required
def organization_page_post():

    if request.method == 'POST':
        org = Organization.query.filter(Organization.id == int(session['organization'])).first()
        
        users = UserOrganizations.query.filter(Organization.id == int(session['organization']))
        for i in users:
            db.session.delete(i)
            db.session.commit()
        db.session.delete(org)
        db.session.commit()


        return redirect(url_for('views.organizations'))

@views.route('/organizationAddition', methods=['POST'])
@login_required
def organization_addition_post():



    current = User.query.filter(User.email == session['email']).first()
    organizationName = request.form.get('organizationName')
    adminId = current.id

    newOrganization = Organization(name=organizationName, adminId=adminId)
    db.session.add(newOrganization)
    db.session.commit()


    return redirect(url_for('views.organizations'))


@views.route('/organizationAddition')
@login_required
def organization_addition() :
    current = User.query.filter(User.email == session['email']).first()
    if current.userType == 'Admin':
        return render_template('organizationAddition.html')
    else :
        return redirect(url_for('views.profile'))


@views.route('/organizationUserAddition')
@login_required
def organization_user_addition() :
    current = User.query.filter(User.email == session['email']).first()
    if current.userType == 'Admin':
        return render_template('organizationUserAddition.html')
    else :
        return redirect(url_for('views.profile'))    

@views.route('/organizationUserAddition', methods=['POST'])
@login_required
def organization_user_addition_post():

    current = User.query.filter(User.email == session['email']).first()
    userName = request.form.get('userName')
    userEmail = request.form.get('userEmail')
    adminId = current.id

    orgId = session.get('organization', None)

    org = Organization.query.filter(orgId == Organization.id).first()
    #orgUsers = UserOrganizations.query.filter(orgId) == organization.id)

    newUser = User.query.filter(User.email == userEmail).first()

    if newUser:
        userId = newUser.id
        addUser = UserOrganizations(organizationId=org.id, userId=userId)
        db.session.add(addUser)
        db.session.commit()
        return redirect(url_for('views.organizationPage', rerouteName=orgId))
    else:    
        flash('User not found. Please enter a valid email address')
        return redirect(url_for('views.organization_user_addition_post'))   
    


@views.route('/organizationUserEdit')
@login_required
def organization_user_edit() :
    current = User.query.filter(User.email == session['email']).first()
    #session['organization'] =  int(rerouteName)
    orgQuery = Organization.query.filter(Organization.id == session['organization']).first()
    userQuery = UserOrganizations.query.filter(UserOrganizations.organizationId == session['organization'])
    users = []
    
    for i in userQuery:
        users.append(i.userId) #get user ids associated with organizations
        print(users)

    userList = []
    for j in range(len(users)):
        query = User.query.filter(User.id == users[j]).first() #find user email and provide it to organization
        #name = query.name + ",  " + query.email
        userList.append([query.name, query.email])
    print(userList)
    orgInfo = {'name' : orgQuery.name, 'admin' : current.email, 'users' : userList}

    return render_template('organizationUserEdit.html', orgInfo=orgInfo)  

@views.route('/organizationUserEdit', methods=['POST'])
@login_required
def organization_user_edit_post():

    current = User.query.filter(User.email == session['email']).first()
    userEmail = request.form.get('userEmail')
    print(userEmail)

    adminId = current.id
    if request.method == 'POST':

        orgId = session.get('organization', None)
        print(orgId)

        org = Organization.query.filter(orgId == Organization.id).first()
        #orgUsers = UserOrganizations.query.filter(orgId) == organization.id)

        newUser = User.query.filter(User.email == userEmail).first()

        if newUser:
            userId = newUser.id
            delUser = UserOrganizations.query.filter_by(organizationId=org.id, userId=userId).first()
            db.session.delete(delUser)
            db.session.commit()
            return redirect(url_for('views.organizationPage', rerouteName=orgId))
        else:    
            flash('An error occurred. Please try again')
            return redirect(url_for('views.organization_user_edit'))   


#organization back-end implementation
""" @views.route('/organizations') #organizations page lists all organizations associated with the admin 
@login_required
def organizations(): 
    current = User.query.filter(User.email == session['email']).first() #get current user (admin)
    if current.userType == 'Admin':
        adminId = current.id
        organizations = Organization.query.filter(adminId==adminId) #locate all organizations associated with admin
        
        return render_template('organizations.html', organizations=organizations) #returns organizations list to organizations page
    
    else:
        return redirect(url_for('views.profile')) #if user is not an admin, they are redirected to the profile page 

@views.route('/organizations', methods=['GET', 'POST'])
@login_required
def organization_post():

    if request.method == 'POST':
        rerouteName = request.form['orgPageReroute']
        return redirect(url_for('views.organizationPage', rerouteName=rerouteName))
        

@views.route('/organizationPage/<rerouteName>')
@login_required
def organizationPage(rerouteName):
    session['organization'] = rerouteName
    current = User.query.filter(User.email == session['email']).first()
    orgQuery = Organization.query.filter(Organization.id == int(rerouteName)).first()
    userQuery = UserOrganizations.query.filter(UserOrganizations.organizationId == int(rerouteName))
    users = []
    
    for i in userQuery:
        users.append(i.userId) #get user ids associated with organizations

    userList = []
    for j in users:
        query = User.quer.filter(User.id == users.j).first() #find user email and provide it to organization
        userList.append(query.email)

    orgInfo = {'name' : orgQuery.name, 'admin' : current.email, 'users' : userList}

    return render_template('organizationPage.html', orgInfo=orgInfo)

@views.route('/organizationAddition', methods=['POST'])
@login_required
def organization_addition_post():



    current = User.query.filter(User.email == session['email']).first()
    organizationName = request.form.get('organizationName')
    adminId = current.id

    newOrganization = Organization(name=organizationName, adminId=adminId)
    db.session.add(newOrganization)
    db.session.commit()


    return redirect(url_for('views.organizations'))


@views.route('/organizationAddition')
@login_required
def organization_addition() :
    current = User.query.filter(User.email == session['email']).first()
    if current.userType == 'Admin':
        return render_template('organizationAddition.html')
    else :
        return redirect(url_for('views.profile'))

@views.route('/organizationUserAddition', methods=['POST'])
@login_required
def organization_user_addition_post(): 
    
    current = User.query.filter(User.email == session['email']).first()
    organizationId = session['organization']
    userEmail = request.form.get('userId')

    return redirect(url_for('views.organizationPage'))
            

@views.route('/organizationUserAddition')
@login_required
def organization_user_addition() :

    current = User.query.filter(User.email == session['email']).first()
    organizationId = session['organization']


    if current.userType == 'Admin':
        return render_template('organizationUserAddition.html')
    else :
        return redirect(url_for('views.profile')) """


#return render_template('organizationPage.html')
@views.route('/calendar-events')
@login_required
def calendar_events():
    #This is a temporary page
    # conn = None
    # cursor = None
    # try :
    #     conn = engine.connect()
    #     cursor = conn.cursor()
    #     cursor.execute("SELECT id, title, url FROM event")
    #     rows = cursor.fetchall()
    #     resp = jsonify({'success' : 1, 'result' : rows})
    #     resp.status_code = 200
    #     return resp

    # except Exception as e :
    #     print(e)
    
    # finally :
    #     cursor.close()
    #     conn.close()


    
    return render_template('calendar.html')
    








