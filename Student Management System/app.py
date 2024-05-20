
from flask import Flask, render_template, redirect, url_for, request
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import pymysql

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'UniversityDB'

db = pymysql.connect(
    host=app.config['MYSQL_HOST'],
    user=app.config['MYSQL_USER'],
    password=app.config['MYSQL_PASSWORD'],
    db=app.config['MYSQL_DB'],
    cursorclass=pymysql.cursors.DictCursor
)

selected_courses = {}

login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(UserMixin):
    def __init__(self, user_id, name, role):
        self.id = user_id
        self.name = name
        self.role = role


@login_manager.user_loader
def load_user(people_id):
    with db.cursor() as cursor:
        cursor.execute(
            "select * from (people, credentials) where people.id = %s and people.id=credentials.people_id", (people_id,))
        user_data = cursor.fetchone()
        if user_data:
            return User(user_id=user_data['id'], name=user_data['name'], role=user_data['people_role'])
    return None

# Routes


@app.route('/')
@login_required
def dashboard():
    if current_user.role == 'admin':

        with db.cursor() as cursor:
            cursor.execute("select count(*) as a from Student")
            student_data = cursor.fetchone()

            cursor.execute("select count(*) as b from Faculty")
            faculty_data = cursor.fetchone()
        return render_template('admin/admin_dashboard.html', data1=student_data, data2=faculty_data)

    elif current_user.role == 'student':
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM semester_cycle")
            semester = cursor.fetchone()
            current_sem = semester['Semester']
        with db.cursor() as cursor:
            cursor.execute("select * from People where id=%s",
                           (current_user.id,))
            user_data = cursor.fetchone()
            user_info = [current_user.name, current_user.id]
            cursor.execute(
                "Select * from Takes inner join Timing on Takes.course_code=Timing.course_code and Takes.course_section=Timing.course_section and takes.Student_id= %s and takes.semester =%s", (current_user.id, current_sem))
            user_data1 = cursor.fetchall()
        return render_template('student/student_dashboard.html', user_data=user_data, user_data1=user_data1, user_info=user_info)

    elif current_user.role == 'faculty':
        return "Faculty View"
    else:
        return "Wait for Admin Approval"


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        print(email, password)
        with db.cursor() as cursor:
            cursor.execute(
                "select * from (people, credentials) where people.id = credentials.people_id AND people_email = %s AND people_password = %s", (email, password))
            user_data = cursor.fetchone()
            if user_data:
                user = User(
                    user_id=user_data['id'], name=user_data['name'], role=user_data['people_role'])
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                return "Login Failed"
    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        student_id = request.form['student_id']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        role = 'student'

        if password != confirm_password:
            return "Password and Confirm Password do not match"

        else:
            with db.cursor() as cursor:
                cursor.execute("insert into Credentials (people_id, people_email, people_password, people_role) VALUES (%s, %s, %s, %s)",
                               (student_id, email, password, role))
                db.commit()

            return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/student/table')
@login_required
def admin_student_view():
    if current_user.role == 'admin':
        with db.cursor() as cursor:
            cursor.execute(
                "select * from (people, student) where people.id = student.people_id")
            user_data = cursor.fetchall()
        return render_template('admin/admin_student_view.html', student=user_data)
    else:
        return "Admin View Only"


@app.route('/student/details', methods=['GET', 'POST'])
@login_required
def admin_student_details():
    if current_user.role == 'admin':
        if request.method == 'POST':
            student_id = request.form['student_id']
            with db.cursor() as cursor:
                cursor.execute(
                    "select * from (people, student) where people.id = student.people_id and people.id = %s", (student_id,))
                student_data = cursor.fetchone()
                cursor.execute(
                    "select qualification_type, educational_institute, passing_year, cgpa, medium from (people, qualifications) where people.id = qualifications.people_id and people.id = %s", (student_id,))
                qualifications = cursor.fetchall()
            # return student_data
            return render_template('admin/admin_student/details.html', student_data=student_data, qualifications=qualifications)
        return render_template('admin/admin_student/details.html', student_data=None)
    else:
        return "Admin View Only"


@app.route('/student/add', methods=['GET', 'POST'])
@login_required
def admin_student_add():
    if current_user.role == 'admin':
        if request.method == "POST":
            print(request.form)
            with db.cursor() as cursor:
                cursor.execute(
                    "insert into People (id, name, university_email, department, nationality, phone_number, gender, current_address, date_of_birth) values (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (request.form["id"], request.form["name"], request.form["university_email"], request.form["department"], request.form["nationality"], request.form["phone_number"], request.form["gender"], request.form["current_address"], request.form["date_of_birth"]))
                cursor.execute(
                    "insert into Student (people_id) values (%s)", (request.form["id"], ))
                cursor.execute(
                    "insert into Qualifications (people_id, qualification_type, educational_institute, passing_year, cgpa, medium) values (%s, %s, %s, %s, %s, %s)", (request.form["id"], request.form["qualification_type1"], request.form["educational_institute1"], request.form["passing_year1"], request.form["cgpa1"], request.form["medium1"]))
                cursor.execute(
                    "insert into Qualifications (people_id, qualification_type, educational_institute, passing_year, cgpa, medium) values (%s, %s, %s, %s, %s, %s)", (request.form["id"], request.form["qualification_type2"], request.form["educational_institute2"], request.form["passing_year2"], request.form["cgpa2"], request.form["medium2"]))
                db.commit()
            return redirect(url_for('admin_student_view'))
        return render_template('admin/admin_student/add.html')
    else:
        return "Admin View Only"


@app.route('/student/remove', methods=["GET", "POST"])
@login_required
def admin_student_remove():
    if current_user.role == 'admin':
        if request.method == 'POST':
            student_id = request.form['student_id']
            with db.cursor() as cursor:
                cursor.execute(
                    "delete from People where id = %s", (student_id,))
                db.commit()
            return redirect(url_for('admin_student_view'))
        return render_template('admin/admin_student/remove.html')

    else:
        return "Admin View Only"


@app.route('/student/update', methods=['GET', 'POST'])
@login_required
def admin_student_update():
    if current_user.role == 'admin':
        if request.method == 'POST':
            # return (request.form)
            if request.form['action'] == 'details':
                student_id = request.form['student_id']
                with db.cursor() as cursor:
                    cursor.execute(
                        "select * from (people, student) where people.id = student.people_id and people.id = %s", (student_id,))
                    student_data = cursor.fetchone()
                    cursor.execute(
                        "select qualification_type, educational_institute, passing_year, cgpa, medium from (people, qualifications) where people.id = qualifications.people_id and people.id = %s", (student_id,))
                    qualifications = cursor.fetchall()
                # return qualifications
                return render_template('admin/admin_student/update.html', student_data=student_data, qualifications=qualifications)

            if request.form['action'] == 'update':
                # return request.form
                with db.cursor() as cursor:
                    sql = "update People set name=%s, university_email=%s, department=%s, nationality=%s, phone_number=%s, gender=%s, current_address=%s, date_of_birth=%s where id=%s"
                    cursor.execute(sql, (
                        request.form['name'],
                        request.form['university_email'],
                        request.form['department'],
                        request.form['nationality'],
                        request.form['phone_number'],
                        request.form['gender'],
                        request.form['current_address'],
                        request.form['date_of_birth'],
                        request.form['id']
                    ))

                    sql = "delete from Qualifications where people_id = %s"
                    cursor.execute(sql, (request.form['id'],))

                    cursor.execute(
                        "insert into Qualifications (people_id, qualification_type, educational_institute, passing_year, cgpa, medium) values (%s, %s, %s, %s, %s, %s)", (request.form["id"], request.form["qualification_type1"], request.form["educational_institute1"], request.form["passing_year1"], request.form["cgpa1"], request.form["medium1"]))
                    cursor.execute(
                        "insert into Qualifications (people_id, qualification_type, educational_institute, passing_year, cgpa, medium) values (%s, %s, %s, %s, %s, %s)", (request.form["id"], request.form["qualification_type2"], request.form["educational_institute2"], request.form["passing_year2"], request.form["cgpa2"], request.form["medium2"]))
                    db.commit()

                return redirect(url_for('admin_student_view'))
        return render_template('admin/admin_student/update.html', student_data=None)
    else:
        return "Admin View Only"


# ADMIN_FACULTY

@app.route('/faculty/table')
@login_required
def admin_faculty_view():
    if current_user.role == 'admin':
        with db.cursor() as cursor:
            cursor.execute(
                "select * from (people, faculty) where people.id = faculty.people_id")
            user_data = cursor.fetchall()
        return render_template('admin/admin_faculty_view.html', faculty=user_data)
    else:
        return "Admin View Only"


@app.route('/faculty/details', methods=['GET', 'POST'])
@login_required
def admin_faculty_details():
    if current_user.role == 'admin':
        if request.method == 'POST':
            faculty_id = request.form['faculty_id']
            with db.cursor() as cursor:
                cursor.execute(
                    "select * from (people, faculty) where people.id = faculty.people_id and people.id = %s", (faculty_id,))
                faculty_data = cursor.fetchone()
                cursor.execute(
                    "select qualification_type, educational_institute, passing_year, cgpa, medium from (people, qualifications) where people.id = qualifications.people_id and people.id = %s", (faculty_id,))
                qualifications = cursor.fetchall()
            # return faculty_data
            return render_template('admin/admin_faculty/details.html', faculty_data=faculty_data, qualifications=qualifications)
        return render_template('admin/admin_faculty/details.html', faculty_data=None)
    else:
        return "Admin View Only"


@app.route('/faculty/add', methods=['GET', 'POST'])
@login_required
def admin_faculty_add():
    if current_user.role == 'admin':
        if request.method == "POST":
            print(request.form)
            # return request.form
            with db.cursor() as cursor:
                cursor.execute(
                    "insert into People (id, name, university_email, department, nationality, phone_number, gender, current_address, date_of_birth) values (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (request.form["id"], request.form["name"], request.form["university_email"], request.form["department"], request.form["nationality"], request.form["phone_number"], request.form["gender"], request.form["current_address"], request.form["date_of_birth"]))
                cursor.execute(
                    "insert into Faculty (people_id, faculty_initials, room_number) values (%s, %s, %s)", (request.form["id"], request.form["faculty_initials"], request.form["room_number"]))
                cursor.execute(
                    "insert into Qualifications (people_id, qualification_type, educational_institute, passing_year, cgpa, medium) values (%s, %s, %s, %s, %s, %s)", (request.form["id"], request.form["qualification_type1"], request.form["educational_institute1"], request.form["passing_year1"], request.form["cgpa1"], request.form["medium1"]))
                cursor.execute(
                    "insert into Qualifications (people_id, qualification_type, educational_institute, passing_year, cgpa, medium) values (%s, %s, %s, %s, %s, %s)", (request.form["id"], request.form["qualification_type2"], request.form["educational_institute2"], request.form["passing_year2"], request.form["cgpa2"], request.form["medium2"]))
                db.commit()
            return redirect(url_for('admin_faculty_view'))
        return render_template('admin/admin_faculty/add.html')
    else:
        return "Admin View Only"


@app.route('/faculty/remove', methods=["GET", "POST"])
@login_required
def admin_faculty_remove():
    if current_user.role == 'admin':
        if request.method == 'POST':
            faculty_id = request.form['faculty_id']
            with db.cursor() as cursor:
                cursor.execute(
                    "delete from People where id = %s", (faculty_id,))
                db.commit()
            return redirect(url_for('admin_faculty_view'))
        return render_template('admin/admin_faculty/remove.html')

    else:
        return "Admin View Only"


@app.route('/faculty/update', methods=['GET', 'POST'])
@login_required
def admin_faculty_update():
    if current_user.role == 'admin':
        if request.method == 'POST':
            # return (request.form)
            if request.form['action'] == 'details':
                faculty_id = request.form['faculty_id']
                with db.cursor() as cursor:
                    cursor.execute(
                        "select * from (people, faculty) where people.id = faculty.people_id and people.id = %s", (faculty_id,))
                    faculty_data = cursor.fetchone()
                    cursor.execute(
                        "select qualification_type, educational_institute, passing_year, cgpa, medium from (people, qualifications) where people.id = qualifications.people_id and people.id = %s", (faculty_id,))
                    qualifications = cursor.fetchall()
                # return qualifications
                return render_template('admin/admin_faculty/update.html', faculty_data=faculty_data, qualifications=qualifications)

            if request.form['action'] == 'update':
                # return request.form
                with db.cursor() as cursor:
                    sql = "update People set name=%s, university_email=%s, department=%s, nationality=%s, phone_number=%s, gender=%s, current_address=%s, date_of_birth=%s where id=%s"
                    cursor.execute(sql, (
                        request.form['name'],
                        request.form['university_email'],
                        request.form['department'],
                        request.form['nationality'],
                        request.form['phone_number'],
                        request.form['gender'],
                        request.form['current_address'],
                        request.form['date_of_birth'],
                        request.form['id']
                    ))

                    sql = "delete from Qualifications where people_id = %s"
                    cursor.execute(sql, (request.form['id'],))

                    cursor.execute(
                        "insert into Qualifications (people_id, qualification_type, educational_institute, passing_year, cgpa, medium) values (%s, %s, %s, %s, %s, %s)", (request.form["id"], request.form["qualification_type1"], request.form["educational_institute1"], request.form["passing_year1"], request.form["cgpa1"], request.form["medium1"]))
                    cursor.execute(
                        "insert into Qualifications (people_id, qualification_type, educational_institute, passing_year, cgpa, medium) values (%s, %s, %s, %s, %s, %s)", (request.form["id"], request.form["qualification_type2"], request.form["educational_institute2"], request.form["passing_year2"], request.form["cgpa2"], request.form["medium2"]))
                    db.commit()

                return redirect(url_for('admin_faculty_view'))
        return render_template('admin/admin_faculty/update.html', faculty_data=None)
    else:
        return "Admin View Only"


@app.route('/course/table')
@login_required
def admin_course_view():
    if current_user.role == 'admin':
        with db.cursor() as cursor:
            cursor.execute(
                "select * from course")
            data = cursor.fetchall()
        # return data
        return render_template('admin/admin_course_view.html', course=data)
    else:
        return "Admin View Only"


@app.route('/course/add', methods=['GET', 'POST'])
@login_required
def admin_course_add():
    if current_user.role == 'admin':
        if request.method == "POST":
            # return request.form
            with db.cursor() as cursor:
                cursor.execute(
                    "insert into Course (course_code, course_section, semester, course_name, seats_vacant, seats_occupied, assigned_faculty) values (%s, %s, %s, %s, %s, %s, %s)",
                    (request.form["course_code"], request.form["course_section"], request.form["semester"], request.form["course_name"], request.form["seats_vacant"], request.form["seats_occupied"], None))
                db.commit()
            return redirect(url_for('admin_course_view'))
        return render_template('admin/admin_course/add.html')
    else:
        return "Admin View Only"


@app.route('/course/remove', methods=["GET", "POST"])
@login_required
def admin_course_remove():
    if current_user.role == 'admin':
        if request.method == 'POST':
            with db.cursor() as cursor:
                cursor.execute(
                    "delete from Course where course_code = %s and course_section=%s and semester=%s", (request.form["course_code"], request.form["course_section"], request.form["semester"]))
                db.commit()
            return redirect(url_for('admin_course_view'))
        return render_template('admin/admin_course/remove.html')

    else:
        return "Admin View Only"


@app.route('/course/update', methods=['GET', 'POST'])
@login_required
def admin_course_update():
    if current_user.role == 'admin':
        if request.method == 'POST':
            # return (request.form)
            if request.form['action'] == 'details':
                with db.cursor() as cursor:
                    cursor.execute(
                        "select * from course where course_code = %s and course_section=%s and semester=%s", (request.form["course_code"], request.form["course_section"], request.form["semester"]))
                    course_data = cursor.fetchone()

                return render_template('admin/admin_course/update.html', course_data=course_data)

            if request.form['action'] == 'update':
                # return request.form
                with db.cursor() as cursor:
                    sql = "update Course set course_name=%s where course_code=%s and course_section=%s and semester=%s"
                    cursor.execute(sql, (
                        request.form['course_name'],
                        request.form['course_code'],
                        request.form['course_section'],
                        request.form['semester']))

                    db.commit()

                return redirect(url_for('admin_course_view'))
        return render_template('admin/admin_course/update.html', course_data=None)
    else:
        return "Admin View Only"


@app.route('/assign', methods=['GET', 'POST'])
@login_required
def admin_assign():
    if current_user.role == 'admin':
        if request.method == 'POST':
            with db.cursor() as cursor:
                cursor.execute("update Course set assigned_faculty = %s where course_code = %s and course_section = %s and semester = %s",
                               (request.form["faculty_id"], request.form["course_code"], request.form["course_section"], request.form["semester"]))
                db.commit()
            return redirect(url_for('admin_course_view'))
    return render_template('admin/admin_assign.html')


@app.route('/approve')
@login_required
def admin_approve():
    if current_user.role == 'admin':
        with db.cursor() as cursor:
            cursor.execute(
                " SELECT * FROM (user, student) WHERE user.id = student.id AND user.role = 'unapproved' ")
            user_data = cursor.fetchall()
        return render_template('admin/admin_approve.html', student=user_data)
    else:
        return "Admin View Only"


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/advising', methods=['GET', 'POST'])
@login_required
def advising():
    user_info = [current_user.name, current_user.id]
    if request.method == 'POST':
        course_code = request.form.get('course_code')
        course_name = request.form.get('course_name')
        course_section = request.form.get('course_section')
        semester = request.form.get('semester')
        if course_code not in selected_courses.keys():
            selected_courses[course_code] = [
                course_code, course_name, course_section, semester]
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM semester_cycle")
        semester = cursor.fetchone()
        current_sem = semester['Semester']
        # return current_sem
    with db.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM course where semester = %s", (current_sem))
        course_data = cursor.fetchall()
        # return course_data

    return render_template('student/advising.html', user_info=user_info, course_data=course_data, selected_courses=selected_courses)


@app.route('/submit_courses', methods=['POST'])
@login_required
def submit_courses():
    user_info = [current_user.name, current_user.id]
    if request.method == 'POST':
        for v in selected_courses.values():
            with db.cursor() as cursor:
                cursor.execute("INSERT INTO takes (Student_id, course_code, course_section, semester, cgpa) VALUES (%s, %s, %s, %s, NULL);", (
                    current_user.id, v[0], v[2], v[3]))
                cursor.execute(
                    "Update course set seats_occupied = seats_occupied + 1 where course_code = %s and course_section = %s and semester= %s", (v[0], v[2], v[3]))
                cursor.execute(
                    "Update course set seats_vacant = seats_vacant - 1 where course_code = %s and course_section = %s and semester= %s", (v[0], v[2], v[3]))
                db.commit()

        selected_courses.clear()

    return redirect(url_for('advising'))


@app.route('/remove_course', methods=['POST'])
@login_required
def remove_course():
    if request.method == 'POST':
        course_code = request.form['course_code']
        del selected_courses[course_code]
    return redirect(url_for('advising'))


@app.route('/admin_advising', methods=['POST', 'GET'])
@login_required
def admin_advising():
    with db.cursor() as cursor:
        cursor.execute("select * from takes order by student_id asc;")
        student_takedata = cursor.fetchall()
    return render_template('admin/admin_advising.html', student_takedata=student_takedata)


@app.route('/admin_advising/remove', methods=['POST', 'GET'])
@login_required
def admin_advising_remove():
    if request.method == 'POST':
        student_id = request.form['student_id']
        course_code = request.form['course_code']
        course_section = request.form['course_section']
        semester = request.form['semester']
        with db.cursor() as cursor:
            cursor.execute("delete from takes where Student_id = %s and course_code = %s and course_section = %s and semester = %s;",
                           (student_id, course_code, course_section, semester))
            cursor.execute("Update course set seats_occupied = seats_occupied - 1 where course_code = %s and course_section = %s and semester = %s;",
                           (course_code, course_section, semester))
            cursor.execute("Update course set seats_vacant = seats_vacant + 1 where course_code = %s and course_section = %s and semester = %s;",
                           (course_code, course_section, semester))
            db.commit()
        return redirect(url_for('admin_advising'))
    return redirect(url_for('admin_advising'))


@app.route('/admin_course_seat', methods=['POST', 'GET'])
@login_required
def admin_course_seat():
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM semester_cycle")
        semester = cursor.fetchone()
        current_sem = semester['Semester']
    with db.cursor() as cursor:
        cursor.execute(
            "select takes.course_code, takes.semester, count(*) as total_students from takes where takes.semester = %s group by takes.course_code;", (current_sem, ))
        course_data3 = cursor.fetchall()
    return render_template('admin/admin_course_seat.html', course_data3=course_data3)


@app.route('/admin_reset', methods=['GET', 'POST'])
@login_required
def admin_reset():
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM semester_cycle")
        semester = cursor.fetchone()
        current_sem = semester['Semester']
    if request.method == 'POST':
        new_sem = request.form['new_sem'] + str(request.form['year'])
        if current_sem != new_sem:
            with db.cursor() as cursor:
                cursor.execute("select * from course;")
                course_data = cursor.fetchall()
                for i in course_data:
                    cursor.execute('insert into Course (course_code, course_section, semester, course_name, seats_vacant, seats_occupied, assigned_faculty) values (%s, %s, %s, %s, 40, 0, NULL)', (
                        i["course_code"], i["course_section"], new_sem, i["course_name"]))
                db.commit()
                cursor.execute("select * FROM course")
                data = cursor.fetchall()
            with db.cursor() as cursor:
                cursor.execute(
                    f"update semester_cycle SET semester = '{new_sem}' WHERE semester = '{current_sem}';")
                db.commit()
            return render_template('admin/admin_reset.html', data=data, current_sem=new_sem)
    return render_template('admin/admin_reset.html', current_sem=current_sem)


if __name__ == '__main__':
    app.run(debug=True)
