from flask import redirect, session
from functools import wraps
from werkzeug.utils import secure_filename

import os
import re
import email_validator

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("cms_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def allowed_file(filename):
    # this function check if the image
    # contains any of the allowed extensions
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def edit_rename_file(filename):
    # this function changes the filename (image) to the student's
    # CMS ID for efficient data searching

    # storing the string that is to be changed (replaced)
    name_to_change = filename.rsplit('.', 1)[0]

    # replacing the old string with the student's CMD ID from session
    filename = filename.replace(name_to_change, str(session['cms_id']))
    return filename


def register_rename_file(filename, cms):
    # this function changes the filename (image) to the student's
    # CMS ID for efficient data searching

    # storing the string that is to be changed (replaced)
    name_to_change = filename.rsplit('.', 1)[0]

    # replacing the old string with the student's CMD ID from register form
    filename = filename.replace(name_to_change, str(cms))
    return filename


def edit_upload_image(image, cursor, app):
    # this function ensures that if image is uploaded and is of allowed extension,
    # removing the old image, renaming the image name with the CMD ID
    # then upload it

    if allowed_file(image.filename):

        # get the old profile picture's path to remove it
        # to avoid having multiple formats of same student's
        # profile picture
        sql = '''
            SELECT SUBSTRING(PhotoPath, 15) AS PhotoPath
            FROM students
            WHERE CMSID = %s;'''
        cursor.execute(sql, session["cms_id"])
        old_filename = cursor.fetchall()
        old_filename = old_filename[0]["PhotoPath"]

        # if there is a row returned incase there is
        # a profile picture of the student (not the placeholder avatar), then delete it
        if old_filename and "placeholder" not in old_filename:
            old_filename = os.path.join(
                app.config['UPLOAD_FOLDER'], old_filename).replace("\\", "/")
            os.remove(old_filename)

        else:

            old_filename = os.path.join(
                app.config['UPLOAD_FOLDER'], old_filename).replace("\\", "/")

        filename = edit_rename_file(image.filename)
        filename = secure_filename(filename)

        # save the profile picture in the server
        # after replacing the default string
        # with the student's CMD ID for quick searching
        old_filename = old_filename.replace(
            old_filename.rsplit('/', 1)[1], filename)
        updated_filename = old_filename
        image.save(updated_filename)

        # store the photo's path
        # in the PhotoPath attribute of database
        sql = '''UPDATE `students`
                 SET PhotoPath = %s
                 WHERE CMSID = %s'''
        cursor.execute(sql, (updated_filename, session["cms_id"]))
        return True

    # Return if image is of not allowed extension
    else:
        return False


def register_upload_image(image, cms, cursor, app):
    # this function ensures that if image is uploaded and is of allowed extension,
    # removing the old image, renaming the image name with the CMD ID
    # then upload it

    if allowed_file(image.filename):

        filename = register_rename_file(image.filename, cms)
        update_filename = "students/" + filename
        update_filename = os.path.join(
            app.config['UPLOAD_FOLDER'], update_filename).replace("\\", "/")

        # save the profile picture in the server
        # after replacing the default string
        # with the student's CMD ID for quick searching
        image.save(update_filename)

        # store the photo's path
        # in the PhotoPath attribute of database
        sql = '''UPDATE `students`
                 SET PhotoPath = %s
                 WHERE CMSID = %s'''
        cursor.execute(sql, (update_filename, cms))

        return True

    # Return if image is of not allowed extension
    else:
        return False

def validate_email(email):
    # Use the email_validator library to check if the email is valid
    try:
        email_validator.validate_email(email)
        return True

    except email_validator.EmailNotValidError:
        return False

def validate_password(password):
    # This function validates password by checking for certain requirements
    '''
        (?=.*[a-z]): This is a positive lookahead assertion that checks if the string contains at least one lowercase letter.
        (?=.*[A-Z]): This is a positive lookahead assertion that checks if the string contains at least one uppercase letter.
        (?=.*\d): This is a positive lookahead assertion that checks if the string contains at least one digit.
        (?=.*[!#\$%&]): This is a positive lookahead assertion that checks if the string contains at least one of the characters in the set !#\$%&.
        [A-Za-z\d!#\$%&]: This character set matches any uppercase or lowercase letter, digit, or the characters !#\$%&.
        {8,}: This specifies that the preceding character set must occur at least 8 times.
    '''
    if not password:
        return False
    if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!#$%&])[A-Za-z\d!#$%&]{8,}$', password):
        return False
    return True
