from flask import Flask, render_template, request, redirect, url_for, flash, Response
import pymysql
import re
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)




@app.route('/')
def index():
    return "This is my webapp"



application = app  # EB requires 'application' variable

if __name__ == '__main__':
    application.run(debug=True)

