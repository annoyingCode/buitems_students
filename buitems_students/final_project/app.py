from flaskext.mysql import MySQL
from helpers import login_required, edit_upload_image, register_upload_image, validate_email, validate_password
from flask import Flask, flash, get_flashed_messages, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import pymysql

# This folder contains the images' path
UPLOAD_FOLDER = "static/images"

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Setting the image upload path for updating profile picture
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"

# Configure MySQL
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'root'
app.config['MYSQL_DATABASE_DB'] = 'buitems'
app.config['MYSQL_CURSORCLASS'] = pymysql.cursors.DictCursor

Session(app)

mysql = MySQL()
mysql.init_app(app)

# Configure CS50 Library to use SQLite database
# db = SQL("sqlite:///buitems.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET", "POST"])
@login_required
def index():

    # Connect to the database
    conn = mysql.connect()
    cursor = conn.cursor()

    # If student's data found and validated, fetch information
    cursor.execute(
        "SELECT * FROM students WHERE CMSID = %s", session["cms_id"])
    student = cursor.fetchall()

    # Fetch currently logged in student's interests
    sql = '''SELECT i.InterestName
             FROM interests i
             JOIN student_interests si ON si.InterestID = i.InterestID
             JOIN students s ON s.CMSID = si.CMSID
             WHERE s.CMSID = %s'''

    cursor.execute(sql, session["cms_id"])
    std_interests = cursor.fetchall()

    # Close the connection
    conn.close()

    # PhotoPath for profile picture
    student[0]["PhotoPath"] = str(student[0]["PhotoPath"])
    return render_template("index.html", student=student, std_interests=std_interests)


@login_required
@app.route("/find", methods=["GET", "POST"])
def find():
    '''HERE'''
    conn = mysql.connect()
    cursor = conn.cursor()

    cms_id = session["cms_id"]

    # Get other students' records on the basis of mutual interests
    sql = '''
        SELECT s.CMSID, s.FirstName, Program, Email,
        GROUP_CONCAT(i.InterestName SEPARATOR ", ") AS Interests, count(i.InterestName) AS Number
        FROM students s
        JOIN student_interests si ON si.CMSID = s.CMSID
        JOIN interests i ON i.InterestID = si.InterestID
        WHERE i.InterestName IN (SELECT i.InterestName
        						 FROM interests i
                                 JOIN student_interests si ON i.InterestID = si.InterestID
                                 JOIN students s ON si.CMSID = s.CMSID
                                 WHERE s.CMSID = %s)
        AND s.CMSID <> %s
        GROUP BY s.CMSID
        ORDER BY Number DESC;'''

    cursor.execute(sql, (cms_id, cms_id))
    students = cursor.fetchall()

    conn.close()

    # If any student not found on the basis of mutual interests
    if (not students):
        flash("No student found with mutual interests.")
        return render_template("friends.html")

    return render_template("friends.html", students=students)


@login_required
@app.route("/profile", methods=["POST"])
def profile():
    ''' Friends suggestion profile '''
    if request.method == "POST":

        # Connect to the database
        conn = mysql.connect()
        cursor = conn.cursor()

        # Get other student's data
        cms_id = request.form.get("cmsid")
        cursor.execute("SELECT * FROM students WHERE CMSID = %s", cms_id)
        student = cursor.fetchall()

        # Fetch the student's interests
        sql = '''SELECT i.InterestName
                FROM interests i
                JOIN student_interests si ON si.InterestID = i.InterestID
                JOIN students s ON s.CMSID = si.CMSID
                WHERE s.CMSID = %s'''
        cursor.execute(sql, cms_id)
        std_interests = cursor.fetchall()

        conn.close()

        return render_template("profile.html", student=student, std_interests=std_interests)


@login_required
@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():

    # Connect to the database
    conn = mysql.connect()
    cursor = conn.cursor()

    # Getting the currently logged in student's record to show on edit page
    # Student cannot edit important information like CMS, Program
    # This variable will also be used for comparison like for email updation
    cursor.execute(
        "SELECT * FROM students WHERE CMSID = %s", (session["cms_id"]))
    student = cursor.fetchall()

    # Getting the student's interests from the database to display them
    # as checked on edit page
    sql = '''
        SELECT GROUP_CONCAT(i.InterestName, ", ") AS Interests
        FROM interests i
        JOIN student_interests si ON i.InterestID=si.InterestID
        JOIN students s ON si.CMSID=s.CMSID
        WHERE s.CMSID=%s'''

    cursor.execute(sql, session["cms_id"])
    std_interests = cursor.fetchall()

    # After editing profile
    if request.method == "POST":

        email = request.form.get("email")

        # If the user changed email, then update it
        if (email != student[0]['Email']):
            sql = '''UPDATE students
                    SET Email = %s
                    WHERE CMSID = %s;'''
            cursor.execute(sql, email, session["cms_id"])

        # Getting the interests to show on edit page if image is of not allowed extension
        # or user de-selected all interests
        sql = '''
                SELECT InterestName, InterestID
                FROM interests;'''
        cursor.execute(sql)
        interests = cursor.fetchall()

        # if the user has changed profile picture
        image = request.files["picture"]
        if (image.filename):
            if (not edit_upload_image(image, cursor, app)):
                flash(
                    "Make sure that your image is of allowed extensions ('png', 'jpg', 'jpeg')")
                return render_template("edit.html", interests=interests, student=student, std_interests=std_interests)

        # Get Twitter and LinkedIn links data
        social_media = request.form.getlist("social-media")

        # getting the Twitter and LinkedIn links of current user
        # from the database to check if they are needed to be removed
        sql = '''
                SELECT Twitter, LinkedIn FROM students
                WHERE CMSID = %s;
                '''
        cursor.execute(sql, session['cms_id'])
        std_social_media = cursor.fetchall()

        # if Twitter and LinkedIn links are also entered
        if (social_media):
            if (social_media[0]):  # Twitter
                sql = '''
                    UPDATE `students`
                    SET Twitter = %s
                    WHERE CMSID = %s'''
                cursor.execute(sql, (social_media[0], session["cms_id"]))

            elif (std_social_media[0]['Twitter'] != social_media[0]):

                sql = '''
                    UPDATE `students`
                    SET Twitter = %s
                    WHERE CMSID = %s'''
                cursor.execute(sql, (None, session["cms_id"]))

            if (social_media[1]):  # LinkedIn
                sql = '''
                    UPDATE `students`
                    SET LinkedIn = %s
                    WHERE CMSID = %s'''
                cursor.execute(sql, (social_media[1], session["cms_id"]))

            elif (std_social_media[0]['LinkedIn'] != social_media[1]):

                sql = '''
                    UPDATE `students`
                    SET LinkedIn = %s
                    WHERE CMSID = %s'''
                cursor.execute(sql, (None, session["cms_id"]))

        # Interest ID will be returned (foreign key)
        interests = request.form.getlist("interest")

        # If user did not select any interest
        if (not interests):
            flash("Please select at least one interest!")
            return render_template("edit.html", interests=interests, student=student, std_interests=std_interests)

        # Converting the selected interests to integer to store them in database
        interests = [int(item) for item in interests]

        # sorting to compare with "int_id" list
        interests.sort()

        sql = '''SELECT InterestID
                 FROM student_interests
                 WHERE CMSID = %s;'''
        cursor.execute(sql, session["cms_id"])
        already_interests = cursor.fetchall()

        # Creating a temporary list to store the interest IDs (values)
        # to check if existing interests exists after the query
        # execution.
        int_id = []
        for id in already_interests:
            int_id.append(id["InterestID"])

        # If any interest's id is not matched
        # either student has removed interests or added more
        if (int_id != interests):

            # Inserting student's ID and interests ID in
            # junction table (many to many relationship)
            sql = '''INSERT INTO `student_interests` (`CMSID`, `InterestID`) VALUES (%s, %s)'''
            for interest in interests:
                if interest not in int_id:
                    cursor.execute(sql, (session["cms_id"], interest))

            # Deleting the interest if the user has de-selected any
            for del_int in int_id:
                if del_int not in interests:
                    sql = '''DELETE FROM `student_interests`
                            WHERE CMSID=%s AND InterestID=%s'''
                    cursor.execute(sql, (session["cms_id"], del_int))

        conn.commit()
        conn.close()

        return redirect("/")

    else:
        # Getting the interests from interests table
        # to display them in edit page to select from them
        sql = '''SELECT InterestName, InterestID
                 FROM interests;'''
        cursor.execute(sql)
        interests = cursor.fetchall()

        # conn.close()

        return render_template("edit.html", interests=interests, student=student, std_interests=std_interests)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    get_flashed_messages()

    # Forget any user_id
    session.clear()

    # Connect to the database
    conn = mysql.connect()
    cursor = conn.cursor()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Getting the CMS ID to check if it is in range (5 digits)
        cms_id = request.form.get("cmsid")
        if (not cms_id.isnumeric() or not len(cms_id) == 5):
            flash("Make sure to enter CMS ID in 5 digits!")
            return redirect("/")

        # Get student's password (hash) from database for validation
        password = request.form.get("password")

        cursor.execute(
            "SELECT CMSID, Hash FROM students WHERE CMSID = %s", cms_id)
        student = cursor.fetchall()

        # If student not found in the university database
        if not student:
            flash("Sorry, your CMS ID could not be found in the university database.")
            return redirect("/")

        # If password does not match
        if not check_password_hash(student[0]["Hash"], password):
            flash("Invalid Password!")
            return redirect("/")

        # Remember which user has logged in
        session["cms_id"] = student[0]["CMSID"]

        conn.close()

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:

        conn.close()

        return render_template("login.html")


@login_required
@ app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@login_required
@ app.route("/change_password", methods=["GET", "POST"])
def change_password():
    """ Change user's password """

    # Connect to the database
    conn = mysql.connect()
    cursor = conn.cursor()

    if request.method == "POST":

        # Store the inputs from the form
        current = request.form.get("current")
        new_pass = request.form.get("password")
        confirm_new_pass = request.form.get("confirmation")

        # Get old password
        cursor.execute(
            "SELECT hash FROM students WHERE CMSID = %s", session["cms_id"])
        old_password = cursor.fetchall()

        # Get old password's hash
        old_password = old_password[0]["hash"]

        # Check if hash of the password and password match
        if check_password_hash(old_password, current):

            # Check if new password is confirmed
            if new_pass == confirm_new_pass:

                # Generate new password's hash
                new_pass = generate_password_hash(
                    new_pass, method='pbkdf2:sha256', salt_length=8)

                # Update the hash(password) of the student
                cursor.execute("UPDATE students SET Hash = %s WHERE CMSID = %s",
                               (new_pass, session["cms_id"]))
                conn.commit()
                conn.close()

                flash("Password Changed!")
                return redirect("/edit_profile")

            else:

                conn.close()

                flash("Passwords does not match.")
                return render_template("edit.html", message="Please try again.")

        else:

            conn.close()

            flash("Invalid current password.")
            return render_template("edit.html", message="Please try again.")

    else:

        conn.close()

        return render_template("edit.html", message="Change Password")


@ app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Connect to the database
    conn = mysql.connect()
    cursor = conn.cursor()

    # Getting the programs name to show them for the students
    # to select their respective enrolled program
    sql = '''SELECT * FROM programs ORDER BY ProgramID;'''
    cursor.execute(sql)
    programs = cursor.fetchall()

    # Getting the interests from interests table
    # to display them in edit page to select from them
    sql = '''SELECT InterestName, InterestID
             FROM interests;'''
    cursor.execute(sql)
    database_interests = cursor.fetchall()

    if request.method == "POST":

        # Get all the data from form to insert in the database
        data = request.form

        # This list stores those input fields' name
        # which are not filled by the user
        data_check_not = []

        # This dictionary stores the data with their keys
        # to send back to the form if user has not entered any important field.
        # This will save user's time in filling the form
        data_check = {}

        # Storing the keys in 'data_check_not' and keys: values in 'data_check'
        for i in data:
            if not data[i] and i != 'social-media':
                data_check_not.append(i)
            else:
                data_check[i] = data[i]

        # If any of the inputs are not entered by the user
        if (len(data_check_not) > 0):
            flash("Please check that you filled the form correctly.")
            return render_template("register.html", data_check_not=True, data_check=data_check, interests_not=database_interests, programs=programs)

        # Form is completely filled, now store the data in variables
        image = request.files["picture"]
        first_name = data['fname']
        last_name = data['lname']
        cms_id = data['cmsid']
        program = data['program']
        email = data['email']
        password = data['password']
        confirmation = data['cpassword']
        social_media = request.form.getlist("social-media")
        form_interests = request.form.getlist("interest")

        # Start validating form from here

        # Getting the CMS ID to check if it is in range (5 digits) - CMSID validation
        if (not cms_id.isnumeric() or not len(cms_id) == 5):
            flash("Make sure to enter CMS ID in 5 digits!")
            return render_template("register.html", data_check=data_check, interests_not=database_interests, programs=programs)

        # Check if record with the provided CMSID already exists in database - CMSID validation
        cms_id = int(cms_id)
        sql = '''
            SELECT CMSID FROM students WHERE CMSID = %s;'''
        cursor.execute(sql, cms_id)
        check_record = cursor.fetchall()

        # Check if the other student's record with
        # entered CMS ID already exists - CMSID validation
        if (check_record):
            flash("This CMS ID already exists in the univeristy database!")
            return redirect("/")

        # If the email is not valid
        if (not validate_email(email)):
            flash("The entered email address is not valid!")
            return render_template("register.html", data_check=data_check, interests_not=database_interests, programs=programs)

        # If the password is not valid i.e. it did not met all the
        # requirement of the password - Password validation
        if not validate_password(password):
            flash("Invalid Password!")
            return render_template("register.html", data_check_not=True, data_check=data_check, interests_not=database_interests, programs=programs)

        # Password validation
        if (password != confirmation):
            flash("Passwords does not match!")
            return render_template("register.html", data_check_not=True, data_check=data_check, interests_not=database_interests, programs=programs)

        # If user did not select any interest
        if (not form_interests):
            flash("Please select at least one interest!")
            return render_template("register.html", data_check=data_check, interests_not=database_interests, programs=programs)

        # FORM VALIDATOION END

        # INSERTION PROCESS OF DATA IN DATABASE STARTS FROM HERE

        # Generating a HASH for password
        password = generate_password_hash(
            password, method='pbkdf2:sha256', salt_length=8)

        # Insert the registration details of user in database
        sql = '''
            INSERT INTO students (CMSID, LastName, FirstName, Email, Program, Hash)
            VALUES (%s, %s, %s, %s, %s, %s);'''

        cursor.execute(sql, (cms_id, last_name, first_name,
                       email, program, password))

        # Insert the student's cms_id and interest_id in the
        # junction table
        sql = '''
            INSERT INTO student_interests (CMSID, InterestID) VALUES (%s, %s);'''

        for interest in form_interests:
            interest = int(interest)
            cursor.execute(sql, (cms_id, interest))

        # If Twitter and LinkedIn links are also entered
        if (social_media):
            if (social_media[0]):  # Twitter
                sql = '''
                    UPDATE `students`
                    SET Twitter = %s
                    WHERE CMSID = %s'''
                cursor.execute(sql, (social_media[0], cms_id))

            if (social_media[1]):  # LinkedIn
                sql = '''
                    UPDATE `students`
                    SET LinkedIn = %s
                    WHERE CMSID = %s'''
                cursor.execute(sql, (social_media[1], cms_id))

        # If the user has uploaded profile picture
        # Writing this code at the end of the function ensures that image will only be validated
        # after evey other data is validated and stored in the database to avoid image
        # uploading errors
        if (image.filename):
            if (not register_upload_image(image, cms_id, cursor, app)):
                flash(
                    "Make sure that your image is of allowed extension ('png', 'jpg', 'jpeg')")
                return render_template("register.html", data_check=data_check, interests_not=database_interests, programs=programs)

        # Update the database
        conn.commit()
        conn.close()

        flash("Successfully Registered!")
        return redirect("/")

    else:

        conn.close()

        return render_template("register.html", interests=database_interests, programs=programs)
