from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from .models import Check, User, Request
from .auth import logout
from . import db
import json
from math import floor
from sqlalchemy.sql import func, and_
from datetime import datetime, date, timedelta
import time
import calendar
views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    job_title = User.query.get(current_user.id).job_title
    if request.method == 'POST': 
        today = date.today()
        existing_check = Check.query.filter(and_(Check.user_id == current_user.id, func.date(Check.date) == today)).first()
        client_ip = request.remote_addr
        
        if 'button1' in request.form:
            if existing_check:
                if existing_check.check_in_time:
                    flash("Already checked in today!", category="error")
                elif existing_check.check_out_time and existing_check.check_in_time is None:
                    flash("You did not check in today and have already checked out!", category="error")
            else:
                new_checkin = Check(user_id=current_user.id, check_in_time = func.current_time(), check_in_ip=client_ip , user=current_user) 
                db.session.add(new_checkin) 
                db.session.commit()
                flash('Checked In! Lets begin today\'s journey', category='success')
            
            
        elif 'button2' in request.form:
            if existing_check:
                client_ip_2 = request.remote_addr
                print("Client IP 2:", client_ip_2)
                if existing_check.check_in_time:
                    existing_check.status = "Present"
                    existing_check.check_out_time = func.current_time()
                    a = datetime.now().time()
                    dt1 = datetime.combine(datetime.min, existing_check.check_in_time)
                    dt2 = datetime.combine(datetime.min, a)
                    existing_check.time_worked = dt2 - dt1
                    existing_check.check_out_ip = client_ip_2
                    db.session.commit()
                    flash("Checked Out! Take it easy and we'll see you on the next business day.", category="success")   
                elif existing_check.check_in_time is None:
                    # No need to update status since he has not checked in and has already checked out, so his status is already 'Miss Punch'
                    existing_check.check_out_time = func.current_time()
                    existing_check.check_out_ip = client_ip_2
                    db.session.commit()
                    flash("Checked out but you didn't check in today!", category="miss punch")   
            else:
                new_checkout = Check(check_out_time=func.current_time() , user_id=current_user.id, check_out_ip=client_ip , user=current_user, status="Miss Punch")  
                db.session.add(new_checkout) 
                db.session.commit()
                flash('Checked out without checking in!', category='miss punch')
        
        elif 'report' in request.form:
            return redirect(url_for('views.report', user_id=current_user.id))
        
        elif 'weekly_report' in request.form:
            return redirect(url_for('views.weekly_report'))
        
        elif 'monthly_report' in request.form:
            return redirect(url_for('views.monthly_report'))
    
    return render_template("home.html", user=current_user, job_title=job_title)

@views.route('/changes', methods=['GET', 'POST'])
@login_required
def makeChanges():
    return render_template('makeChanges.html', user=current_user)

@views.route('/req', methods=['GET', 'POST'])
@login_required
def req():
    if request.method == 'POST': 
        if 'req_button' in request.form:
            try:
                request_date = request.form.get('date')
                date_object = datetime.strptime(request_date, '%Y-%m-%d')
                day_of_week = date_object.strftime('%A')
                
                request_datetime = time.strftime("%Y-%m-%d %H:%M:%S")
                
                r_check_in_time = request.form.get('check-in-time')
                
                r_check_out_time = request.form.get('check-out-time')
                
                r_status='Pending'
                
                new_request = Request(date=request_date, day=day_of_week, request_datetime=request_datetime, r_check_in_time=r_check_in_time if r_check_in_time else None, r_check_out_time=r_check_out_time if r_check_out_time else None, r_status=r_status, user=current_user) 
                db.session.add(new_request) 
                db.session.commit()
                flash('Request sent successfully!', category='success')
                return redirect(url_for('views.req'))
                
            except Exception as e:
                flash('Request failed!', category='error')
                print("An error occurred:", e)
                
        elif 'report' in request.form:
            return redirect(url_for('views.report', user_id=current_user.id))
        
        elif 'weekly_report' in request.form:
            return redirect(url_for('views.weekly_report'))
        
        elif 'monthly_report' in request.form:
            return redirect(url_for('views.monthly_report'))
            
    # username = User.query.get(current_user.id).username
    # requests = Request.query.filter_by(user=username).all()
    
    username = current_user.username
    requests = Request.query.join(User).filter(User.username == username).all()
            
    return render_template('req.html', user=current_user, requests=requests)

@views.route('/report/<int:user_id>', methods=['GET', 'POST'])
@login_required
def report(user_id):
    user_checkins = Check.query.filter_by(user_id=user_id).order_by(Check.date).all()
    total_worked_time = timedelta()
    
    for i in range(len(user_checkins)):
        if user_checkins[i].check_in_time and user_checkins[i].check_out_time:
            todays_work_time = timedelta(hours=user_checkins[i].time_worked.hour, minutes=user_checkins[i].time_worked.minute, seconds=user_checkins[i].time_worked.second)
            total_worked_time += todays_work_time
            
    total_hours = floor(total_worked_time.total_seconds() // 3600)
    total_minutes = floor(total_worked_time.total_seconds() % 3600 // 60)
    total_seconds = floor(total_worked_time.total_seconds() % 60)
    formatted_total_worked_time = f"{total_hours}:{total_minutes:02}:{total_seconds:02}" 
            
    if request.method == 'POST': 
        if 'report' in request.form:
            return redirect(url_for('views.report', user_id=current_user.id))
        
        elif 'weekly_report' in request.form:
            return redirect(url_for('views.weekly_report'))
        
        elif 'monthly_report' in request.form:
            return redirect(url_for('views.monthly_report'))
    
    return render_template('report.html',user=current_user, user_checkins=user_checkins, total_worked_time=total_worked_time,formatted_total_worked_time=formatted_total_worked_time, enumerate=enumerate)

@views.route('/weekly-report', methods=['GET','POST'])
@login_required
def weekly_report():
    week_offset=int(request.args.get('week',0))
    today = datetime.today()
    start_of_week = today - timedelta(days=today.weekday())  # Start of this week (Monday)
    end_of_week = start_of_week + timedelta(days=6)  # End of this week (Sunday)

    prev_week_offset = week_offset - 1
    next_week_offset = week_offset + 1

    # Query user's check-ins for the current week
    user_checkins = Check.query.filter(
        Check.user_id == current_user.id,
        Check.date.between((start_of_week + timedelta(days=week_offset*7)).date(), (end_of_week + timedelta(days=week_offset*7)).date())
    ).order_by(Check.date).all()

    total_worked_time = timedelta()
    for checkin in user_checkins:
        if checkin.check_in_time and checkin.check_out_time:
            dt1 = datetime.combine(datetime.min, checkin.check_in_time)
            dt2 = datetime.combine(datetime.min, checkin.check_out_time)
            worked_time = dt2 - dt1
            total_worked_time += worked_time
            
    total_hours = floor(total_worked_time.total_seconds() // 3600)
    total_minutes = floor(total_worked_time.total_seconds() % 3600 // 60)
    total_seconds = floor(total_worked_time.total_seconds() % 60)
    formatted_total_worked_time = f"{total_hours}:{total_minutes:02}:{total_seconds:02}" 
            
    if request.method == 'POST': 
        if 'report' in request.form:
            return redirect(url_for('views.report', user_id=current_user.id))
        
        elif 'weekly_report' in request.form:
            return redirect(url_for('views.weekly_report'))
        
        elif 'monthly_report' in request.form:
            return redirect(url_for('views.monthly_report'))

    return render_template('weekly_report.html', user=current_user, user_checkins=user_checkins, 
                           start_of_week=start_of_week + timedelta(days=week_offset*7), 
                           end_of_week=end_of_week + timedelta(days=week_offset*7), 
                           total_worked_time=total_worked_time, week_offset=week_offset,formatted_total_worked_time=formatted_total_worked_time, 
                           prev_week_offset=prev_week_offset, next_week_offset=next_week_offset, 
                           enumerate=enumerate)

@views.route('/monthly-report', methods=['GET', 'POST'])
@login_required
def monthly_report():
    # Get the current month and year
    month_offset = int(request.args.get('month', 0))
    today = date.today()
    target_year = today.year
    target_month = today.month + month_offset

    if target_month > 12:
        target_year += 1
        target_month -= 12
    elif target_month < 1:
        target_year -= 1
        target_month += 12

    start_of_month = date(target_year, target_month, 1)
    days_in_month = calendar.monthrange(target_year, target_month)[1]
    end_of_month = date(target_year, target_month, days_in_month)

    # Query user's check-ins for the current month
    user_checkins = Check.query.filter(
        Check.user_id == current_user.id,
        Check.date.between(start_of_month, end_of_month)
    ).order_by(Check.date).all()

    # Get the check-ins for the current month only
    user_checkins_this_month = [checkin for checkin in user_checkins if checkin.date.month == target_month and checkin.date.year == target_year]

    total_worked_time = timedelta()
    for checkin in user_checkins:
        if checkin.check_in_time and checkin.check_out_time:
            dt1 = datetime.combine(datetime.min, checkin.check_in_time)
            dt2 = datetime.combine(datetime.min, checkin.check_out_time)
            worked_time = dt2 - dt1
            total_worked_time += worked_time

    total_hours = floor(total_worked_time.total_seconds() // 3600)
    total_minutes = floor(total_worked_time.total_seconds() % 3600 // 60)
    total_seconds = floor(total_worked_time.total_seconds() % 60)
    formatted_total_worked_time = f"{total_hours}:{total_minutes:02}:{total_seconds:02}"

    prev_month_offset = month_offset - 1
    next_month_offset = month_offset + 1

    if request.method == 'POST':
        if 'report' in request.form:
            return redirect(url_for('views.report', user_id=current_user.id))
        elif 'weekly_report' in request.form:
            return redirect(url_for('views.weekly_report'))
        elif 'monthly_report' in request.form:
            return redirect(url_for('views.monthly_report'))

    return render_template('monthly_report.html', user=current_user, user_checkins=user_checkins, user_checkins_this_month=user_checkins_this_month, total_worked_time=total_worked_time, start_of_month=start_of_month, month_offset=month_offset, prev_month_offset=prev_month_offset, next_month_offset=next_month_offset, formatted_total_worked_time=formatted_total_worked_time,targer_year=target_year,target_month=target_month, enumerate=enumerate)
    
# @views.route('/calendar-events-detail')
# @login_required
# def calendar_events_detail():
#     user_checkins = Check.query.filter_by(user_id=current_user.id).all()
#     events = []

#     for checkin in user_checkins:
#         if checkin.check_in_time and checkin.check_out_time:
#             event = {
#                 'title': f'Worked: {checkin.time_worked}',
#                 'start': f'{checkin.date}T{checkin.check_in_time}',
#                 'end': f'{checkin.date}T{checkin.check_out_time}',
#                 'status': checkin.status,  # Include status property
#                 # 'backgroundColor': get_status_color(checkin.status),  # Call function to get color
#                 'color': get_status_color(checkin.status),  # Call function to get color
#                 'borderColor': get_status_color(checkin.status),
#                 'check_in_time': checkin.check_in_time.strftime('%H:%M:%S'),
#                 'check_out_time': checkin.check_out_time.strftime('%H:%M:%S'),
#                 'time_worked': str(checkin.time_worked)
#             }
#             events.append(event)

#     return jsonify(events)

# def get_status_color(status):
#     if status == 'Present':
#         return '#28a745'  # Green
#     elif status == 'Absent':
#         return '#dc3545'  # Red
#     elif status == 'Miss Punch':
#         return '#ffc107'  # Yellow
#     else:
#         return '#6c757d'  # Default color (gray or any other color)

@views.route('/fetch-checks')
@login_required
def fetch_checks():
    checks = Check.query.filter_by(user_id=current_user.id).all()
    events = []
    
    for check in checks:
        event = {
            # 'title': f"{check.status}",
            'start': check.date.isoformat(),  # ISO format for FullCalendar
            'status': check.status,
            'check_in_time': check.check_in_time.isoformat() if check.check_in_time else None,
            'check_out_time': check.check_out_time.isoformat() if check.check_out_time else None,
            'backgroundColor': 'transparent',  # Initial transparent; overridden by eventDidMount
            'color' : 'gray',
            # 'border' : None,
            'borderColor': 'transparent'  # No border
        }
        events.append(event)
    
    return jsonify(events)

@views.route('/fetch-details')
@login_required
def fetch_details():
    date_str = request.args.get('date')
    check = Check.query.filter_by(user_id=current_user.id, date=date_str).first()

    if check:
        details = {
            'check_in_time': check.check_in_time.strftime('%H:%M:%S') if check.check_in_time else None,
            'check_out_time': check.check_out_time.strftime('%H:%M:%S') if check.check_out_time else None,
            'time_worked': check.time_worked.strftime('%H:%M:%S') if check.time_worked else None
        }
    else:
        details = {
            'check_in_time': None,
            'check_out_time': None,
            'time_worked': None
        }
    
    return jsonify(details)
