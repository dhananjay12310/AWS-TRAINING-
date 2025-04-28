from flask import Flask, render_template, request, redirect, url_for, flash, Response
import pymysql
import re
import os
import boto3
import json
from botocore.exceptions import ClientError

app = Flask(__name__)
app.secret_key = os.urandom(24)

# AWS Secrets Manager client to fetch credentials
secrets_client = boto3.client('secretsmanager', region_name='us-east-1')

# S3 and DB Configuration constants (these will be fetched from Secrets Manager)
S3_BUCKET = "dj-static-assets"
S3_REGION = "us-east-1"
S3_KEY = "school_header.jpg"
s3_client = boto3.client('s3', region_name=S3_REGION)

def get_secret(secret_name):
    """ Fetch secrets from AWS Secrets Manager """
    try:
        # Fetch the secret
        response = secrets_client.get_secret_value(SecretId=secret_name)
        
        # Secret is in either 'SecretString' or 'SecretBinary' (for this example we expect 'SecretString')
        secret = response['SecretString']
        return json.loads(secret)
    except ClientError as e:
        raise Exception(f"Error retrieving secret: {e}")

# Fetch MySQL and S3 credentials from AWS Secrets Manager
db_secrets = get_secret('database-1-credentials')  # Replace 'my-db-credentials' with your secret name
aws_secrets = get_secret('s3access-user-credentials')  # Replace 'my-aws-credentials' with your secret name

# Set up MySQL and AWS S3 credentials from Secrets Manager
app.config['MYSQL_HOST'] = db_secrets['MYSQL_HOST']
app.config['MYSQL_USER'] = db_secrets['MYSQL_USER']
app.config['MYSQL_PASSWORD'] = db_secrets['MYSQL_PASSWORD']
app.config['MYSQL_DB'] = db_secrets['MYSQL_DB']

# Set S3 credentials from Secrets Manager
S3_ACCESS_KEY = aws_secrets['AWS_ACCESS_KEY']
S3_SECRET_KEY = aws_secrets['AWS_SECRET_KEY']

# Initialize S3 client with credentials from Secrets Manager
s3_client = boto3.client(
    's3',
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    region_name=S3_REGION
)

# Function to get MySQL connection
def get_connection():
    return pymysql.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        db=app.config['MYSQL_DB']
    )

@app.route('/')
def index():
    conn = get_connection()
    cursor = conn.cursor()
    ################################################################	
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students_table (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            age INT NOT NULL,
            email VARCHAR(255) NOT NULL
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM students_table")
    count = cursor.fetchone()[0]

    if count == 0:
        cursor.executemany("""
            INSERT INTO students_table (name, age, email)
            VALUES (%s, %s, %s)
        """, [
            ('Dhananjay Gupta', 24, 'dhananjay12310@gmail.com'),
            ('Neetu Kumari', 26, 'nitugupta901@gmail.com')
        ])
        conn.commit()
    #######################################################################	
    cursor.execute("SELECT * FROM students_table")
    students = cursor.fetchall()
    conn.close()
    
    # Image URL from S3
    image_url = url_for('serve_s3_image')
    
    return render_template('index.html', students=students, image_url=image_url)
    #return "This is my webapp with CICD pipeline"

@app.route('/s3-image')
def serve_s3_image():
    # Retrieve the image from private S3 bucket
    s3_object = s3_client.get_object(Bucket=S3_BUCKET, Key=S3_KEY)
    image_data = s3_object['Body'].read()
    return Response(image_data, content_type='image/jpeg')

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        email = request.form['email']

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash("Invalid email address", "danger")
            return render_template("add_student.html", name=name, age=age, email=email)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO students_table (name, age, email) VALUES (%s, %s, %s)", (name, age, email))
        conn.commit()
        conn.close()
        flash("Student added successfully!", "success")
        return redirect(url_for('index'))
    
    return render_template("add_student.html")


application = app  # EB requires 'application' variable

if __name__ == '__main__':
    application.run(debug=True)

