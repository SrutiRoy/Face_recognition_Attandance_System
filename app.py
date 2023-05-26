import cv2
import numpy as np
import face_recognition
import os
import csv
from datetime import datetime
from flask import Flask, flash, request, redirect, url_for, render_template, Response, session
from werkzeug.utils import secure_filename
import mysql.connector

UPLOAD_FOLDER = r'C:\Users\sruti\test\IMAGE_FILES'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


app = Flask(__name__)
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Set database credentials
db_host = "localhost"
db_user = "root"
db_password = "admin"
db_name = "login_db"

# Create database connection
conn = mysql.connector.connect(
    host=db_host,
    user=db_user,
    password=db_password,
    database=db_name
)

# Create cursor object
cursor = conn.cursor()

@app.route("/")
def index1():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    # Get user input from form
    username = request.form["username"]
    password = request.form["password"]

    # Prepare SQL statement to select user from database
    sql = "SELECT * FROM users WHERE username = %s AND password = %s"
    values = (username, password)
    cursor.execute(sql, values)
    user = cursor.fetchone()

    # Check if user was found in database
    if user:
        # Save user information to session
        session["username"] = user[1]

        # Redirect to success page
        return redirect("/up")
    else:
        # Display error message
        return render_template("login.html", error="Invalid username or password")

@app.route('/up')
def upload_file():
    return render_template('upload.html')



@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/register", methods=["POST"])
def register_submit():
    # Get user input from form
    username = request.form["username"]
    password = request.form["password"]

    # Prepare MySQL query to insert user into database
    cursor = conn.cursor()
    query = "INSERT INTO users (username, password) VALUES (%s, %s)"
    params = (username, password)
    cursor.execute(query, params)
    conn.commit()

    # Save user information to session
    session["username"] = username

    # Redirect to success page
    return redirect("/up")



@app.route('/view')
def view():
    csv_data = []

    with open('attendence.csv', 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        next(csv_reader)  # Skip header row
        

        for row in csv_reader:
            csv_data.append(row)
    current_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('viewattandance.html', csv_data=csv_data,current_date=current_date)



@app.route('/success', methods=['GET', 'POST'])
def success():
    if 'file' not in request.files:
        # flash('No file part')
        return render_template('upload.html')
    file = request.files['file']
    if file.filename == '':
        # flash('No image selected for uploading')
        return render_template('upload.html')
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        # print('upload_image filename: ' + filename)
        # flash('Image successfully uploaded and displayed below')
        return render_template('upload.html')
    else:
        # flash('Allowed image types are -> png, jpg, jpeg, gif')
        return render_template('upload.html')
    
@app.route('/index')
def index():
    """Video streaming home page."""
    return render_template('index.html')

def gen():
    IMAGE_FILES = []
    filename = []
    dir_path = r'C:\Users\sruti\test\IMAGE_FILES'

    for imagess in os.listdir(dir_path):
        img_path = os.path.join(dir_path, imagess)
        img_path = face_recognition.load_image_file(img_path)  # reading image and append to list
        IMAGE_FILES.append(img_path)
        filename.append(imagess.split(".", 1)[0])

    def encoding_img(IMAGE_FILES):
        encodeList = []
        for img in IMAGE_FILES:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            encode = face_recognition.face_encodings(img)[0]
            encodeList.append(encode)
        return encodeList

    def takeAttendence(name):
        with open('attendence.csv', 'r+') as f:
            mypeople_list = f.readlines()
            nameList = []
            for line in mypeople_list:
                entry = line.split(',')
                nameList.append(entry[0])
            if name not in nameList:
                now = datetime.now()
                datestring = now.strftime('%H:%M:%S')
                Timestamp= datetime.now()
                f.writelines(f'\n{name},{datestring},{Timestamp}')

    encodeListknown = encoding_img(IMAGE_FILES)
    # print(len('sucesses'))

    cap = cv2.VideoCapture(0)

    while True:
        success, img = cap.read()
        imgc = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        # converting image to RGB from BGR
        imgc = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        fasescurrent = face_recognition.face_locations(imgc)
        encode_fasescurrent = face_recognition.face_encodings(imgc, fasescurrent)

        # faceloc- one by one it grab one face location from fasescurrent
        # than encodeFace grab encoding from encode_fasescurrent
        # we want them all in same loop so we are using zip
        for encodeFace, faceloc in zip(encode_fasescurrent, fasescurrent):
            matches_face = face_recognition.compare_faces(encodeListknown, encodeFace)
            face_distence = face_recognition.face_distance(encodeListknown, encodeFace)
            # print(face_distence)
            # finding minimum distence index that will return best match
            matchindex = np.argmin(face_distence)

            if matches_face[matchindex]:
                name = filename[matchindex].upper()
                # print(name)
                y1, x2, y2, x1 = faceloc
                # multiply locations by 4 because we above we reduced our webcam input image by 0.25
                # y1,x2,y2,x1 = y1*4,x2*4,y2*4,x1*4
                cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 0), 2)
                cv2.rectangle(img, (x1, y2 - 35), (x2, y2), (255, 0, 0), 2, cv2.FILLED)
                cv2.putText(img, name, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                takeAttendence(name)  # taking name for attendence function above

        # cv2.imshow("campare", img)
        # cv2.waitKey(0)
        frame = cv2.imencode('.jpg', img)[1].tobytes()
        yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        key = cv2.waitKey(20)
        if key == 27:
            break


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')






if __name__ == "__main__":
    app.run(debug=True)
