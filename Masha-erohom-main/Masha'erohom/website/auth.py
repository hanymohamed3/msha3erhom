from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db   ##means from __init__.py import db
from flask_login import login_user, login_required, logout_user, current_user
import hashlib

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user:
            hashed_password = hashlib.sha512(password.encode('utf-8')).hexdigest()

            if user.password==hashed_password:
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html", user=current_user)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        firstName = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
            return render_template("register.html", user=user, email=email, firstName=firstName)
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
            return render_template("register.html", user=user, email=email, firstName=firstName)
        elif len(firstName) < 2:
            flash('First name must be greater than 1 character.', category='error')
            return render_template("register.html", user=user, email=email, firstName=firstName)
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
            return render_template("register.html", user=user, email=email, firstName=firstName)
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
            return render_template("register.html", user=user, email=email, firstName=firstName)
        else:
            password_hash = hashlib.sha512(password1.encode('utf-8')).hexdigest()
            new_user = User(email=email, first_name=firstName, password=password_hash)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            return redirect(url_for('views.home'))

    return render_template("register.html", user=current_user)
