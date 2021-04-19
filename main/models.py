from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
import datetime


#Flask Migration
#flask db revision 
#flask db stamp head
#flask db migrate
#flask db upgrade


class User(UserMixin, db.Model):

    __tablename__ = 'User'

    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    sentMessages = db.relationship('Message', back_populates='sender', foreign_keys='Message.senderId')
    recievedMessages = db.relationship('Message', back_populates='recipient', foreign_keys='Message.recipientId')
    
    organizations = db.relationship('UserOrganizations', back_populates='user', foreign_keys='UserOrganizations.userId') #each user has a relationship with 'UserOrganizations' table

    userType = db.Column(db.String(100)) #holds user selection for desired role (Admin/Student/Instructor)
    hasAccess = db.Column(db.Boolean) #indicates if a user has access to the service t/f

    __mapper_args__ = { 
        "polymorphic_identity": "User",
        "polymorphic_on": userType
    }
    
    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    def __repr__(self):
        return f"User('{self.name}','{self.email}', '{self.hasAccess}')"


# organization 
# id, name, type, list_of_users
class Organization(UserMixin, db.Model): #admin creates organization

    __tablename__ = 'Organization'

    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    name = db.Column(db.String(1000))
    adminId = db.Column(db.Integer, db.ForeignKey('Admin.id'), nullable=False) # foreign key that ties admin to an organization (admin can only create/delete organizations)
    users =  db.relationship('UserOrganizations', back_populates='organization') #every user

    def __repr__(self):
        return f"Organization('{self.name}')"

class UserOrganizations(UserMixin, db.Model): #admin then adds users to organization

    __tablename__ = 'UserOrganizations'

    organizationId =  db.Column(db.Integer, db.ForeignKey('Organization.id', ondelete='cascade'), primary_key=True)
    organization = db.relationship('Organization', foreign_keys=organizationId)
    userId = db.Column(db.Integer, db.ForeignKey('User.id', ondelete='set null'), primary_key=True)
    user =  db.relationship('User', foreign_keys=userId)

    def __repr__(self):
        return f"UserOrganizations('{self.organizationId}', '{self.userId}')"


    

class Admin(User):

    __tablename__ = 'Admin'

    id = db.Column(db.ForeignKey('User.id'), primary_key=True) # primary keys are required by SQLAlchemy
    adminOrganizations = db.relationship('Organization', backref='Admin', lazy=True)
    
    __mapper_args__ = {"polymorphic_identity": "Admin"}

    # def set_password(self, password):
    #     self.password = generate_password_hash(password)

    def __repr__(self):
        return f"Admin('{self.name}','{self.email}')"
        
class Instructor(User):

    __tablename__ = 'Instructor'


    id = db.Column(db.ForeignKey('User.id'), primary_key=True) # primary keys are required by SQLAlchemy
    inststructorCourses = db.relationship('Course', backref='Instructor', lazy=True)


    # def set_password(self, password):
    #     self.password = generate_password_hash(password)

    __mapper_args__ = {"polymorphic_identity": "Instructor"}



#     def __repr__(self):
#         return f"Instructor('{self.name}','{self.email}')"

class Student(User):

    __tablename__ = 'Student'

    id = db.Column(db.ForeignKey('User.id'), primary_key=True) # primary keys are required by SQLAlchemy
    #email = db.Column(db.String(100), unique=True)
    #password = db.Column(db.String(100))
    #student_name = db.Column(db.String(1000))
    #studentCourses = db.relationship('StudentCourses', backref='Student', lazy=True) #all courses that a student belongs to
    #messages = db.relationship('Message', backref='Student', lazy=True) #specifies 1:M relationship between user and message tables
    #organizations = db.relationship('Organization', backref='Student', lazy=True)
    studentCourses = db.relationship('StudentCourses', back_populates='student', foreign_keys='StudentCourses.studentId')
    # def set_password(self, password):
    #     self.password = generate_password_hash(password)

    __mapper_args__ = {"polymorphic_identity": "Student"}

    def __repr__(self):
        return f"Student('{self.name}','{self.email}')"        


class Message(UserMixin, db.Model):

    __tablename__ = 'Message'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    message = db.Column(db.String(100), nullable=False) #actual message
    #sender = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) #foreign key from user to link to message table
    senderId = db.Column(db.Integer, db.ForeignKey('User.id', ondelete='cascade'))
    sender = db.relationship('User', foreign_keys=senderId)
    recipientId = db.Column(db.Integer, db.ForeignKey('User.id', ondelete='set null'))
    recipient =  db.relationship('User', foreign_keys=recipientId)
    dateTime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow) #time message was received 
    isRead = db.Column(db.Boolean, default=False) #indicates if a message has been read

    def __repr__(self):
        return f"Message('{self.message}', '{self.dateTime}', '{self.isRead}')"



class Course(UserMixin, db.Model):

    __tablename__ = 'Course'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000))
    instructorId = db.Column(db.Integer, db.ForeignKey('Instructor.id'), nullable=False) #foreign key from user to link to message table
    students =  db.relationship('StudentCourses', back_populates='course')
    description = db.Column(db.String(10000))
    semester = db.Column(db.String(100))
    organization = db.Column(db.String(100))
    modules = db.relationship('Module', backref='Course', lazy=True)
    

    def __repr__(self):
        return f"Course('{self.name}')"


class StudentCourses(UserMixin, db.Model):

    __tablename__ = 'StudentCourses'

    courseId =  db.Column(db.Integer, db.ForeignKey('Course.id', ondelete='cascade'), primary_key=True)
    course = db.relationship('Course', foreign_keys=courseId)
    studentId = db.Column(db.Integer, db.ForeignKey('Student.id', ondelete='set null'), primary_key=True)
    student =  db.relationship('Student', foreign_keys=studentId)
    grade = db.Column(db.Integer)


    def __repr__(self):
        return f"StudentCourses('{self.name}')"

class Module(UserMixin, db.Model):

    __tablename__ = 'Module'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000)) #Module 1, 2, etc
    courseId = db.Column(db.Integer, db.ForeignKey('Course.id'), nullable=False) #foreign key from user to link to message table
    description = db.Column(db.String(1000))
    #files = db.relationship('File', backref='Module', lazy=True)
    fileLoc = db.Column(db.Integer)
    assignments = db.relationship('Assignment', backref='Module', lazy=True)


    def __repr__(self):
        return f"Module('{self.name}')"

class Assignment(UserMixin, db.Model):

    __tablename__ = 'Assignment'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000))
    courseId = db.Column(db.Integer, db.ForeignKey('Course.id'), nullable=False)
    description = db.Column(db.String(1000))
    moduleId = db.Column(db.Integer, db.ForeignKey('Module.id'), nullable=False)
    #files = db.relationship('File', backref='Assignment', lazy=True)
    dueDate = db.Column(db.String(1000))
    fileLoc = db.Column(db.Integer)
    

    def __repr__(self):
        return f"Assignment('{self.name}')"

class AssignmentGrades(UserMixin, db.Model):

    __tablename__ = 'AssignmentGrades'

    assignmentId =  db.Column(db.Integer, db.ForeignKey('Assignment.id', ondelete='cascade'), primary_key=True)
    assignment = db.relationship('Assignment', foreign_keys=assignmentId)
    studentId = db.Column(db.Integer, db.ForeignKey('Student.id', ondelete='set null'), primary_key=True)
    student =  db.relationship('Student', foreign_keys=studentId)
    #fileLoc = db.relationship('File', foreign_keys=studentId)
    fileLoc = db.Column(db.Integer)
    grade = db.Column(db.Integer) 
    
    def __repr__(self):
        return f"AssignmentGrades('{self.studentId}')"


class Announcement(db.Model):

    __tablename__ = 'Announcement'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000))
    description = db.Column(db.String(1000))
    subject = db.Column(db.String(1000))
    dateTime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow())
    courseId = db.Column(db.Integer, db.ForeignKey('Course.id'), nullable=False) 


    def __repr__(self):
        return f"Announcement('{self.name}', '{self.description}')"  

class File(UserMixin, db.Model):

    __tablename__ = 'File'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000))
    fileType = db.Column(db.String(100))
    data = db.Column(db.LargeBinary)
    userId = db.Column(db.Integer)
    # assignmentId = db.Column(db.Integer, db.ForeignKey('Assignment.id'))
    # moduleId = db.Column(db.Integer, db.ForeignKey('Module.id'))

    def __repr__(self):
        return f"File('{self.name}', '{self.fileType}')"  


## file upload commands
# var = request.files['fileName']

#newFile = File(name=var.filename, data=file.read())
#db.session.add(newFile)
#db.session.commit()

## read file command