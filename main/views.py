
import re
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify, Flask, current_app, g, send_file
from flask_login import login_required, current_user
from flask_login.utils import login_fresh
from sqlalchemy.sql.expression import null
from werkzeug.wrappers import Request
from .models import Announcement, AssignmentGrades, Instructor, Module, User, Message, Course, StudentCourses, Organization, UserOrganizations, Assignment, File
from flask_sqlalchemy import SQLAlchemy 
from sqlalchemy.sql import text, and_, or_
from .__init__ import app, db
from main import models
from io import BytesIO
import datetime

#engine = create_engine('sqlite:///db.sqlite')
views = Blueprint('views', __name__)




#This can be a sample for of data that is in class course, we could query a table where user.id in enrolledID

# Adding Course Events to DB


@views.route('/')
def index():
    return render_template('index.html')

@views.route('/index')
@login_required
def MainP():
    #This is our main page for calander and general organization


    return render_template('index.html', name=current_user.name)



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


 
@views.route('/userProfile', methods=['GET', 'POST'])
@login_required
def user_profile_post():

    if request.method == 'POST':
        rerouteName = request.form['profile']
        return redirect(url_for('views.user_profile', rerouteName=rerouteName))

@views.route('/userProfile/<rerouteName>')
@login_required
def user_profile(rerouteName):
    #if user is admin query Organization table rather than UserOrganizations 
    query = User.query.filter(User.id == int(rerouteName)).first()
    currentUser = { 'id' : query.id, 'name' : query.name, 'email' : query.email, 'userType' : query.userType}

    if query.userType == 'Admin':
        userO = Organization.query.filter(currentUser['id'] == Organization.adminId)
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

    return render_template('userProfile.html', current=currentUser, organizationNames=organizationNames)

   

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
                'desc' : course.description
            }
            enrolledStudents = []

            for s in course.students :
                studentUsers = User.query.filter(User.id == s.studentId).first()
                enrolledStudents.append(studentUsers.name)
            currentCorse['enrolledId'] = enrolledStudents
            coursesDict.append(currentCorse)
        return render_template('coursesInstructor.html', course=coursesDict)

    elif current.userType == 'Student' :
        studentCourses = StudentCourses.query.filter(StudentCourses.studentId == current.id)
        

        coursesDict = []

        for course in studentCourses:
            currentCourse = Course.query.filter(Course.id == course.courseId).first()
        
            currentCorse = {
                'id' : currentCourse.id,
                'name' : currentCourse.name,
                'teacherId' : currentCourse.instructorId,
                'desc' : currentCourse.description
            }
            coursesDict.append(currentCorse)

        return render_template('courses.html', course=coursesDict)

@views.route('/courses', methods=['GET', 'POST'])
@login_required
def courses_post():

    if request.method == 'POST':
        rerouteName = request.form['courseReroute']
        return redirect(url_for('views.coursePage', rerouteName=rerouteName))


@views.route('/coursePage/<rerouteName>', methods=['GET'])
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
    points = request.form.get('points')
    points = int(points) 
    course = Course.query.filter(Course.id == session['rerouteName']).first()
    var = request.files['file']

    newFile = File(name=var.filename, data=var.read(), userId=current.id)
    if newFile.name != '':
        db.session.add(newFile)
        db.session.commit()

    
    if(course.instructorId == current.id):
        moduleId = Module.query.filter(Module.name == moduleName).first()
        new_assignment = Assignment(name=assignmentName, description=description, courseId=course.id, dueDate=dueDate, moduleId=moduleId.id, fileLoc=newFile.id, points=points)
        db.session.add(new_assignment)
        db.session.commit()
    else :
        flash('Sorry but you are not in the Instructor of this' + str(course.name))
        return redirect(url_for('views.new_assignment'))


    return redirect(url_for('views.coursePage', rerouteName=course.id))

@views.route('/assignmentPageSubmit', methods=['POST'])
def assignmentPageSubmit_post():
    current = User.query.filter(User.email == session['email']).first()
    assignmentId = session['assignmentId']
    assignment = Assignment.query.filter(Assignment.id == assignmentId).first()

    try :
        studentFile = File.query.filter(and_(File.userId == current.id, File.assignmentId == assignment.id)).first()

        local_object = db.session.merge(studentFile)
        db.session.delete(local_object)
        db.session.commit()
        var = request.files['file']
        newFile = File(name=var.filename, data=var.read(), userId=current.id, assignmentId=assignment.id)
        if newFile.name != '':
            db.session.add(newFile)
            db.session.commit()
        return redirect(url_for('views.assignmentSpecPage'))

        
    except :
        var = request.files['file']
        newFile = File(name=var.filename, data=var.read(), userId=current.id, assignmentId=assignment.id)
        if newFile.name != '':
            db.session.add(newFile)
            db.session.commit()
        return redirect(url_for('views.assignmentSpecPage'))

@views.route('/assignmentPage', methods=['POST'])
def assignmentSpecPage_post():

    if request.method == 'POST' :
        assignmentId = session['assignmentId']
        assignment = Assignment.query.filter(Assignment.id == assignmentId).first()
        fileData = File.query.filter(File.id == assignment.fileLoc).first()
        return send_file(BytesIO(fileData.data), attachment_filename=fileData.name, as_attachment=True)
    

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
            "cName" : course.name,
            "points" : assignment.points
    }
    try :
        fileData = File.query.filter(File.id == assignment.fileLoc).first()
        aDict["fileName"] = fileData.name
    except :
        aDict["fileName"] = None

    

    if current.id == course.instructorId :
        return render_template('assignmentsPageInstructor.html',id=assignmentId, aDict=aDict)
    else : 

        submittedFile = File.query.filter(and_(current.id == File.userId, assignment.id == File.assignmentId)).first()

        if submittedFile is not None :
            subCheck = True
            aDict["subName"] = submittedFile.name
        else :
            subCheck = False
        aDict["subCheck"] = subCheck
        try :
            gradedAssignment = AssignmentGrades.query.filter(and_(AssignmentGrades.assignmentId == assignment.id, AssignmentGrades.studentId == current.id)).first()
            aDict["grade"] = gradedAssignment.grade
        except :
            aDict["grade"] = None
        

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


@views.route('/assignmentGrade', methods=['POST'])
def assignment_grade_post(): 
    assignmentId = session['assignmentId']
    assignment = Assignment.query.filter(Assignment.id == assignmentId).first()
    studentId = request.form['gradeSubmit']
    student = User.query.filter(User.id == studentId).first()
    points = request.form.get('assignmentGrade')
    points = int(points)

    if points > assignment.points :
        flash('Sorry but that is too many points!')
        return redirect(url_for('views.assignment_submissions'))

    try :

        assignmentGrade = AssignmentGrades.query.filter(and_(AssignmentGrades.assignmentId == assignment.id, AssignmentGrades.studentId == student.id)).first()
        local_object = db.session.merge(assignmentGrade)
        db.session.delete(local_object)
        db.session.commit()

        new_grade = AssignmentGrades(assignmentId = assignment.id , studentId=student.id, grade=points)
        db.session.add(new_grade)
        db.session.commit()
        
    except :
        new_grade = AssignmentGrades(assignmentId = assignment.id , studentId=student.id, grade=points)
        db.session.add(new_grade)
        db.session.commit()

        
        
        
        

    return redirect(url_for('views.assignment_submissions'))

@views.route('/assignmentSubmissions', methods=['POST'])
def assignment_submissions_post(): 

    if request.method == 'POST' :
        assignmentId = session['assignmentId']
        assignment = Assignment.query.filter(Assignment.id == assignmentId).first()
        studentId = request.form['submissionDownload']
        fileData = File.query.filter(File.id == studentId).first()
        return send_file(BytesIO(fileData.data), attachment_filename=fileData.name, as_attachment=True)

@views.route('/assignmentSubmissions')
def assignment_submissions(): 

    assignmentId = session['assignmentId']
    assignment = Assignment.query.filter(Assignment.id == assignmentId).first()
    course = Course.query.filter(Course.id == assignment.courseId).first()
    current = User.query.filter(User.email == session['email']).first()

  
    aDict = {
            "name" : assignment.name,
            "desc" : assignment.description,
            "dueDate" : assignment.dueDate,
            "fileLoc" : assignment.fileLoc,
            "aId" : assignment.id,
            "cName" : course.name,
            "points" : assignment.points
    }

    students = StudentCourses.query.filter(course.id == StudentCourses.courseId)
    studentIds = []
    for s in students :
        studentFile = File.query.filter(File.userId == s.studentId)
        for file in studentFile :
            if file.assignmentId == assignment.id :
                studentIds.append(s.studentId)

    aDict['sId'] = studentIds


    submissionList = []
    for id in studentIds :
        studentUser = User.query.filter(User.id == id).first()
        studentFile = File.query.filter(and_(File.userId == id,File.assignmentId == assignment.id)).first()
        

        tempDict = {
            "sId" : id,
            "studentName" : studentUser.name,
            "fileName" : studentFile.name,
            "fileId" : studentFile.id
        }
        submissionList.append(tempDict)
        try :
            assignmentGrade = AssignmentGrades.query.filter(and_(AssignmentGrades.assignmentId == assignment.id, AssignmentGrades.studentId == id)).first()
            tempDict['grade'] = assignmentGrade.grade
        except :
            tempDict['grade'] = None

    if current.id == course.instructorId :
        return render_template('assignmentSubmissions.html',id=assignmentId, aDict=aDict, submissionList=submissionList)
    else : 

        return render_template('assignmentsPage.html', id=assignmentId, aDict=aDict)



@views.route('/deleteAssignment')
def delete_assignment():
    assignmentId = session['assignmentId']
    assignment = Assignment.query.filter(assignmentId == Assignment.id).first()
    assignmentName = assignment.name

    return render_template('deleteAssignment.html', assignmentName=assignmentName)


@views.route('/deleteAssignment', methods=['POST'])
def delete_assigment_post():

    if request.method == 'POST':
        
        assignmentId = session['assignmentId']
        inputName = request.form.get('name')
        assignment = Assignment.query.filter(assignmentId == Assignment.id).first()
        if assignment.name == inputName :

            grades = AssignmentGrades.query.filter(assignment.id == AssignmentGrades.assignmentId)
            for j in grades:
                local_object = db.session.merge(j)
                db.session.delete(local_object)
                db.session.commit()

            local_object = db.session.merge(assignment)
            db.session.delete(local_object)
            db.session.commit()

            return redirect(url_for('views.assignment_page'))
        else :
            flash('Sorry the course name inputed did not match given course, please check spelling')
            return redirect(url_for('views.delete_assignment'))
        

@views.route('/deleteCourse')
def delete_course():
    rerouteName = session['rerouteName']
    course = Course.query.filter(Course.id == rerouteName).first()
    courseName = course.name

    return render_template('deleteCourse.html', courseName=courseName)

@views.route('/deleteCourse', methods=['POST'])
def delete_course_post():

    if request.method == 'POST':
        rerouteName = session['rerouteName']
        inputName = request.form['courseName']
        course = Course.query.filter(Course.id == rerouteName).first()
        if course.name == inputName :

            course = Course.query.filter(Course.id == rerouteName).first()
            studentCourse = StudentCourses.query.filter(StudentCourses.courseId == course.id)
            courseAnnouncements = Announcement.query.filter(course.id == Announcement.courseId)
            courseAssignment = Assignment.query.filter(course.id == Assignment.courseId)
            courseModuels = Module.query.filter(course.id == Module.courseId)

            for i in studentCourse:
                local_object = db.session.merge(i)
                db.session.delete(local_object)
                db.session.commit()
            for i in courseAnnouncements:
                local_object = db.session.merge(i)
                db.session.delete(local_object)
                db.session.commit()
            for i in courseAssignment:

                grades = AssignmentGrades.query.filter(i.id == AssignmentGrades.assignmentId)
                for j in grades:
                    local_object = db.session.merge(j)
                    db.session.delete(local_object)
                    db.session.commit()

                local_object = db.session.merge(i)
                db.session.delete(local_object)
                db.session.commit()
            for i in courseModuels:
                local_object = db.session.merge(i)
                db.session.delete(local_object)
                db.session.commit()
                
            local_object = db.session.merge(course)
            db.session.delete(local_object)
            db.session.commit() 

            return redirect(url_for('views.courses'))
        else :
            flash('Sorry the course name inputed did not match given course, please check spelling')
            return redirect(url_for('views.delete_course'))

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
            date = str(i.dateTime)
            date = date[:16]
            newMessage = {'id' : i.id, 'messageText' : i.message ,'senderId'  : i.senderId, 'recipientId': i.recipientId, 'date' : date, 'isRead': i.isRead }
            
            senderQuery = User.query.filter(User.id == i.senderId).first()
            senderName = senderQuery.name
            senderEmail = senderQuery.email
            newMessage['name'] = senderName
            newMessage['recipient'] = currentEmail
            newMessage['sender'] = senderEmail
            messageList.append(newMessage)
        
        sentList = []
        for i in sentQuery :
            date = str(i.dateTime)
            date = date[:16]
            newMessage = {'id' : i.id, 'messageText' : i.message ,'senderId'  : i.senderId, 'recipientId': i.recipientId, 'date' :  date, 'isRead': i.isRead }
            
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
            local_object = db.session.merge(i)
            db.session.delete(local_object)
            db.session.commit() 
        local_object = db.session.merge(org)
        db.session.delete(local_object)
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
            local_object = db.session.merge(delUser)
            db.session.delete(local_object)
            db.session.commit() 
            return redirect(url_for('views.organizationPage', rerouteName=orgId))
        else:    
            flash('An error occurred. Please try again')
            return redirect(url_for('views.organization_user_edit'))   




#return render_template('organizationPage.html')
@views.route('/calendar-events')
@login_required
def calendar_events():
    current = User.query.filter(User.email == session['email']).first()

    assignmentList = []
    announList=[]
    if current.userType == "Instructor" :
        courseI = Course.query.filter(Course.instructorId == current.id)
        assignmentList = []
        announList=[]
        for c in courseI :
            announ =  Announcement.query.filter(c.id == Announcement.courseId)
            for ann in announ :
                announList.append(ann)
           


            assignment = Assignment.query.filter(Assignment.courseId == c.id)
            for a in assignment :
                assignmentList.append(a)


    if current.userType == "Student" :
        courseS = StudentCourses.query.filter(StudentCourses.studentId == current.id)
        assignmentList = []
        announList=[]
        for c in courseS :
            course = c.course
            announ =  Announcement.query.filter(course.id == Announcement.courseId)
            for ann in announ :
                announList.append(ann)
           

            assignment = Assignment.query.filter(Assignment.courseId == course.id)
            for a in assignment :
                assignmentList.append(a)

    announDict = []
    for announ in announList :
        currentAnnoun = {'courseName' : announ.name, 'subjectLine' : announ.subject, 'announcement' : announ.description, 'time' : str(announ.dateTime.date())}
        announDict.append(currentAnnoun)
    
    assDict = []
    for a in assignmentList :
        currentAs= {'name' : a.name, 'desc' : a.description, 'dueDate' : a.dueDate, 'id' : a.id}
        assDict.append(currentAs)

    oneWeekList = {}
    day0 = datetime.date.today()
    oneWeekList[day0] = []
    day1 = day0 + datetime.timedelta(days=1)
    oneWeekList[day1] = []
    day2 = day1 + datetime.timedelta(days=1)
    oneWeekList[day2] = []
    day3 = day2 + datetime.timedelta(days=1)
    oneWeekList[day3] = []
    day4 = day3 + datetime.timedelta(days=1)
    oneWeekList[day4] = []
    day5 = day4 + datetime.timedelta(days=1)
    oneWeekList[day5] = []
    day6 = day5 + datetime.timedelta(days=1)
    oneWeekList[day6] = []

    #dt.strptime("10/12/13", "%m/%d/%y")

    for day in oneWeekList :
        tempDayL = []
        for announ in announDict :
            if announ['time'] == str(day) :
                tempDayL.append(announ)

        oneWeekList.get(day).append(tempDayL)
    



    
    
    return render_template('calendar.html', weeksTime = oneWeekList, announDict = announDict, assDict = assDict, announList=announList)
    




@views.route('/search', methods=['GET', 'POST'])
@login_required
def search():

    current = User.query.filter(User.email == session['email']).first()
    keyword = request.form.get('Search')
    keywordId = 0
    #results = []

    courses = {'name' : [], 'id': []}
    messages = {'name' : [], 'email': [], 'message': [], 'id': []} #returns result for users emails
    modules = {'name' : [], 'course' : [], 'id': []}
    announcements = {'name' : [], 'id': []}
    assignments = {'name' : [], 'desc': [], 'points': [], 'id': []}
    profiles = {'name' : [], 'email': [], 'id': []}
    organizations = {'name' : [], 'users' : [], 'id': []}

    #determine user 
    userQuery = User.query.filter(or_(User.name == keyword, User.email == keyword))

    for i in userQuery:
        profiles['name'].append(i.name)
        profiles['email'].append(i.email)
        profiles['id'].append(i.id)

        if i.name == keyword or i.email == keyword: #if a user with the name or email matches the keyword is an instructor, then 
            keywordId = i.id
    

    courseQuery = Course.query.filter(or_(Course.name == keyword, Course.instructorId == keywordId))

    for i in courseQuery:
        courses['name'].append(i.name)
        courses['id'].append(i.id)

    messageQuery = Message.query.filter(Message.recipientId == keywordId)

    for i in messageQuery:
        messageUsers = User.query.filter(User.id == i.recipientId).first() #find user name 
        messages['name'].append(messageUsers.name)
        messages['email'].append(messageUsers.email)
        messages['message'].append(i.message)
        messages['id'].append(i.id)

    moduleQuery = Module.query.filter(Module.name == keyword)

    for i in moduleQuery:

        moduleCourse = Course.query.filter(i.courseId == Course.id).first()

        modules['name'].append(i.name)
        modules['course'].append(moduleCourse.name)
        modules['id'].append(i.id)

    announcementQuery = Announcement.query.filter(Announcement.name == keyword)

    for i in announcementQuery:
        announcements['name'].append(i.name)
        announcements['id'].append(i.id)

    assignmentQuery = Assignment.query.filter(Assignment.name == keyword)

    for i in assignmentQuery:
        assignments['name'].append(i.name)
        assignments['desc'].append(i.description)
        assignments['points'].append(i.points)
        assignments['id'].append(i.id)

    organizationQuery = Organization.query.filter(Organization.name == keyword)

    for i in organizationQuery:
        organizations['name'].append(i.name)
        orgUser = UserOrganizations.query.filter(UserOrganizations.organizationId == i.id)
        for j in orgUser:
            users = User.query.filter(User.id == j.userId).first()
            organizations['users'].append(users.email)

        organizations['id'].append(i.id)    

        #update results list
        # results.append(courses)
        # results.append(messages)
        # results.append(modules)
        # results.append(announcements)
        # results.append(assignments)

    # elif current.userType == 'Instructor':
    #     # courses = {}
    #     # messages = {} #returns result for users email
    #     # modules = {}
    #     # assignments = {}

    # elif current.userType == 'Admin':    
    #     # organizations = {}
    #     # users = {} #users found in organizations


    return render_template('search.html', userType=current.userType, profiles=profiles, courses=courses, messages=messages, modules=modules, announcements=announcements, assignments=assignments, organizations=organizations)




