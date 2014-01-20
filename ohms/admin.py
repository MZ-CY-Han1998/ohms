"""
OHMS: Online Homework Management System
"""

import os
from flask import Flask, request, render_template, make_response
import json
from utils import NewEncoder
from datetime import datetime, timedelta

from base import session
from objects import User, Homework, Question, QuestionResponse, GradingPermission
from queries import get_user, get_grading_tasks_for_response, question_grade_query, get_long_answer_qs
#from assign_grading_tasks import selective_peer_grading
from tabulate_grades import tabulate_grades as _tabulate_grades
import options

import smtplib


# Configuration based on deploy target
app = Flask(__name__)
app.debug = (options.target != "prod")
sunet = os.environ.get("WEBAUTH_USER")
if not sunet:
    raise Exception("You are no longer logged in. Please refresh the page.")
try:
    user = get_user(sunet)
    assert(user.type == "admin")
except:
    raise Exception("You are not authorized to view thie page.")

treatments = {
    0: [1,1,1,0,0,1,1,0,0],
    1: [1,0,0,1,1,0,0,1,1],
    2: [1,1,1,0,0,0,0,1,1],
    3: [1,0,0,1,1,1,1,0,0]
    }


@app.route("/")
def index():
    return render_template("admin/index.html", options=options, user=user)


@app.route("/assign_tasks/<int:hw_id>", methods=['POST'])
def assign_tasks(hw_id):
    selective_peer_grading(hw_id, request.args.get("due_date"))


@app.route("/tabulate_grades/<int:hw_id>", methods=['POST'])
def tabulate_grades(hw_id):
    for q in get_long_answer_qs(hw_id):
        _tabulate_grades(q.id)


@app.route("/reminder_email/<int:hw_id>", methods=['POST'])
def reminder_email(hw_id):

    smtpObj = smtplib.SMTP('localhost')
    sender = 'stats60-aut1314-staff@lists.stanford.edu'
    recipients = []

    homework = session.query(Homework).get(hw_id)

    for question in homework.questions:
        entries = session.query(GradingPermission).filter_by(question_id=question.id).filter_by(permissions=0).all()
        for entry in entries:
            name = session.query(User).get(entry.sunet).name
            email = "%s@stanford.edu" % entry.sunet
            if email not in recipients:
                message = r'''From: Stats 60 Staff <stats60-aut1314-staff@lists.stanford.edu>
To: %s <%s>
Subject: %s Peer Grading Incomplete

Dear %s,

%s

Best,
Stats 60 Staff
''' % (name, email, homework.name, name, request.form.get('message'))
                smtpObj.sendmail(sender, [email], message)                
                recipients.append(email)

    return "Successfully sent email to:<br/>" + "<br/>".join(recipients)


@app.route("/view_responses", methods=['POST', 'GET'])
def view_responses():

    q_id = request.args.get('q')
    groups = request.form.getlist('group')

    users = session.query(User).filter(User.group.in_(groups)).all()

    import random
    random.seed(q_id)
    random.shuffle(users)

    user_responses = []
    for u in users:
        responses = session.query(QuestionResponse).\
                   filter_by(sunet = u.sunet).\
                   filter_by(question_id = q_id).\
                   all()
        if responses:
            user_responses.append( (u, responses[-1]) )
        
    return render_template("admin/view_responses.html", user_responses=user_responses, options=options, user=user, groups=groups)

    
@app.route("/update_response/<int:response_id>", methods=['POST'])
def update_response(response_id):
    from objects import QuestionResponse
    response = session.query(QuestionResponse).get(response_id)
    response.sample = 1
    score = request.form['score']
    response.score = int(score) if score else None
    response.comments = request.form['comments']
    session.commit()
    return r'''
Successfully updated response %d! 
<script type="text/javascript">window.close();</script>
''' % response.id


@app.route("/rate", methods=['GET'])
def view_peer_comments():

    out = {}
    question_response_id = request.args.get("id")

    grading_tasks = get_grading_tasks_for_response(question_response_id)
    question_grades = []
    
    for task in grading_tasks:
        submissions = question_grade_query(task.id).all()
        if submissions:
            question_grades.append(submissions[-1])

    return render_template("admin/view_comments.html",
                           question_grades=question_grades,
                           options=options)


@app.route("/update_question", methods=['POST'])
def update_question():
    q_id = request.form['q_id']
    xml_new = request.form['xml']
    import elementtree.ElementTree as ET
    question = Question.from_xml(ET.fromstring(xml_new))
    return json.dumps({
        "xml": question.xml,
        "html": question.to_html(),
    })


@app.errorhandler(Exception)
def handle_exceptions(error):
    return make_response(error.message, 403)
