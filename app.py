from flask import Flask, render_template, request, redirect, url_for, session
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import json
import secrets  # For generating random confirmation codes
import stripe
import server
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from google_sheets import find_empty
from google_sheets import change_row

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for sessions
server.api_key = 'sk_test_51QJ3wRCpRmcr6sEEJUBCs4vLrPYjMvugUeTfVvmMjZAIMW1MenvZyGWxQccsui3sJB8FTeWfaoeFFcd28qmJzqM700WPzokPVL'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

users = {}  # This should be replaced with a database in a real application

@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)

YOUR_DOMAIN = 'http://127.0.0.1:5000'

class User(UserMixin):
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

    def get_id(self):
        return self.id



# JSON data file
DATA_FILE = "data.json"

# Ensure the data.json file exists with necessary keys
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"total_raised": 0}, f)

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Function to send email using Gmail SMTP
def send_email(to_email, subject, content):
    sender_email = "phrogshabitat2009@gmail.com"  
    app_password = "uktv uinw huiq edfk"  

    # Check if the email is None or empty
    #if not to_email:
        # raise ValueError("No email provided")
    
    # Set up the MIME
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject

    # Attach the email content
    msg.attach(MIMEText(content, 'html'))

    try:
        # Connect to Gmail's SMTP server
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, to_email, msg.as_string())
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/calendar", methods=["GET", "POST"])
def calendar():
    data = load_data()
    if request.method == "POST":
        selected_dates = request.form.getlist("selected_dates[]")
        return redirect(url_for("checkout", dates=",".join(selected_dates)))
    return render_template("calendar.html", data=data)

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    selected_dates = []
    total_cost = 0

    # Handle GET request (show checkout page with selected dates)
    if request.method == "GET":
        selected_dates = request.args.get("dates", "").split(",")
        selected_dates = [date.strip() for date in selected_dates if date.strip()]

        total_cost = sum(int(date.split('-')[2]) for date in selected_dates)
        return render_template("checkout.html", selected_dates=selected_dates, total_cost=total_cost)

    # Handle POST request (form submission)
    elif request.method == "POST":
        # Get the selected dates from the form data (hidden input)
        selected_dates = request.form.get("selected_dates", "").split(",")
        selected_dates = [date.strip() for date in selected_dates if date.strip()]

        # Calculate total cost
        total_cost = sum(int(date.split('-')[2]) for date in selected_dates)
        
        # Extract form data
        name = request.form.get("name", "")
        email = request.form.get("email", "")
        card_number = request.form.get("card_number", "")
        expiration_date = request.form.get("expiration_date", "")
        cvv = request.form.get("cvv", "")
        location = request.form.get("location", "")

        # Ensure email is not None
        if email is None or email == "":
            return "Email is required", 400

        # Generate a unique confirmation code
        confirmation_code = secrets.token_hex(3)  # Generate a 6-character hex code
        session['confirmation_code'] = confirmation_code  # Store it in session for validation

        # Store the user's info temporarily in the session
        session['user_info'] = {
            'name': name,
            'email': email,
            'card_number': card_number,
            'location': location
        }

        # Send the confirmation email
        confirmation_email_content = f"Your confirmation code: {confirmation_code}"
        send_email(email, "Please Confirm Your Order", confirmation_email_content)

        # Redirect to the confirmation page
        return render_template("enter_confirmation_code.html", email=email, total_cost=total_cost)


@app.route("/confirm", methods=["POST"])
def confirm():
    # Get the entered confirmation code
    entered_code = request.form.get("confirmation_code", "")
    
    # Retrieve the generated code from the session
    if entered_code == session.get('confirmation_code'):
        # Confirmation code is correct, proceed to success page with user details
        user_info = session.get('user_info')
        return render_template(
            "success.html",
            name=user_info.get('name'),
            email=user_info.get('email'),
            card_number=user_info.get('card_number'),
            location=user_info.get('location'),
            total_cost=session.get('total_cost')
            
        )
        
        
    else:
        # Invalid confirmation code, prompt the user to try again
        return "Invalid confirmation code. Please try again.", 400


@app.route("/thank_you")
def thank_you():
    return render_template("thank_you.html")

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        user_id = str(len(users) + 1)
        users[user_id] = User(user_id, username, email)
        
        change_row(1,find_empty(1),username,password,email)
        
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = next((u for u in users.values() if u.email == email), None)
        if user:
            current_user = login_user(user)
            return redirect(url_for('my_calendar'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/my_calendar')
@login_required
def my_calendar():
    return render_template('my_calendar.html', user=current_user)

@app.route('/purchase', methods=['GET', 'POST'])
@login_required
def purchase():
    if request.method == 'POST':
        # Handle Stripe payment
        pass
    return render_template('purchase.html')

if __name__ == "__main__":
    app.run(debug=True)

# Set your secret key. Remember to switch to your live secret key in production.
# See your keys here: https://dashboard.stripe.com/apikeys



if __name__ == '__main__':
    app.run(port=4242)
    
#_______________________________________

YOUR_DOMAIN = 'http://localhost:4242'

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    # Provide the exact Price ID (for example, pr_1234) of the product you want to sell
                    'price': '{{PRICE_ID}}',
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=YOUR_DOMAIN + '/success.html',
            cancel_url=YOUR_DOMAIN + '/cancel.html',
        )
    except Exception as e:
        return str(e)

    return redirect(checkout_session.url, code=303)