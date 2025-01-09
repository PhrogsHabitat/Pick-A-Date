from flask import Flask, render_template, request, redirect, url_for, session, jsonify, request
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import json
import secrets  # For generating random confirmation codes
import stripe
from stripe.error import SignatureVerificationError
import server
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from google_sheets import find_empty
from google_sheets import change_row
import google_sheets
from google_sheets import signin
from google_sheets import get_cell_value
from werkzeug.utils import secure_filename
import re  # Ensure re is imported

from itsdangerous import URLSafeTimedSerializer



import random
import string

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for sessions
stripe.api_key = 'sk_test_51QJ3wRCpRmcr6sEEJUBCs4vLrPYjMvugUeTfVvmMjZAIMW1MenvZyGWxQccsui3sJB8FTeWfaoeFFcd28qmJzqM700WPzokPVL'
s = URLSafeTimedSerializer(app.secret_key)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

global loggedIn 
loggedIn = False
users = {}  # This should be replaced with a database in a real application

@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)

YOUR_DOMAIN = 'http://127.0.0.1:5000'

class User(UserMixin):
    def __init__(self, id, username, email, profile_picture=None):
        self.id = id
        self.username = username
        self.email = email
        self.profile_picture = profile_picture

    def get_id(self):
        return self.id





# JSON data file
DATA_FILE = "data.json"

sillyFellaAutoLogin = True

global redeem_check 
redeem_check = False

# Define the upload folder and allowed extensions
UPLOAD_FOLDER = 'static/profile_pictures'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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

def send_email(to, subject, body):
    sender_email = "phrogshabitat2009@gmail.com"  
    app_password = "uktv uinw huiq edfk"  

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, app_password)
        server.sendmail(sender_email, to, msg.as_string())
    print("Email sent successfully!")

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/calendar", methods=["GET", "POST"])
def calendar():
    data = load_data()
    
    if current_user.is_authenticated:
        user_email = current_user.email  # Fetch current user's email
        user_signed_in = google_sheets.get_cell_value(user_email, "IsSignedIn")
        user_has_token = google_sheets.get_cell_value(user_email, "HasToken")
        token_type = google_sheets.get_cell_value(user_email, "TokenType")
        cal_title = google_sheets.get_cell_value(user_email, "CAL-Title") or "My Calendar"
        
        # Retrieve customizations from Google Sheets or set defaults
        customizations = {
            "text_color": google_sheets.get_cell_value(user_email, "CAL-TextColor") or "#000000",
            "border_color": google_sheets.get_cell_value(user_email, "CAL-BorderColor") or "#0078d4",
            "font_style": google_sheets.get_cell_value(user_email, "CAL-FontStyle") or "Arial",
            "box_size": google_sheets.get_cell_value(user_email, "CAL-BoxSize") or "100",
            "title_text": cal_title,
            "icon": google_sheets.get_cell_value(user_email, "CAL-Icon")
        }

        if request.method == "POST":
            # Handle calendar title update
            new_title = request.form.get("calendar_title")
            if new_title:
                google_sheets.set_cell_value(user_email, "CAL-Title", new_title)
                customizations["title_text"] = new_title
                return render_template(
                    "calendar.html", 
                    data=data, 
                    user_signed_in=user_signed_in, 
                    user_has_token=user_has_token, 
                    token_type=token_type, 
                    cal_title=new_title, 
                    customizations=customizations
                )

        print(f"user_signed_in: {user_signed_in}, user_has_token: {user_has_token}, token_type: {token_type}, cal_title: {cal_title}, customizations: {customizations}")  # Debug
    else:
        user_signed_in = "False"
        user_has_token = "False"
        token_type = ""
        cal_title = "My Calendar"
        customizations = {}

    if request.method == "POST":
        # Handle date selection for checkout
        selected_dates = request.form.getlist("selected_dates[]")
        return redirect(url_for("checkout", dates=",".join(selected_dates)))

    return render_template(
        "calendar.html", 
        data=data, 
        user_signed_in=user_signed_in, 
        user_has_token=user_has_token, 
        token_type=token_type, 
        cal_title=cal_title, 
        customizations=customizations
    )


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

def load_user_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_user_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email'].lower()
        password = request.form['password']
        user_id = str(len(users) + 1)
        user = User(user_id, username, email)
        users[user_id] = user
        
        change_row(1, find_empty(1), username, password, email)
        
        # Save user data to JSON file
        user_data = load_user_data()
        user_data[user_id] = {
            'username': username,
            'email': email,
            'profile_picture': None
        }
        save_user_data(user_data)
        
        google_sheets.preload_google_sheets()

        
        login_user(user)  # Log in the user
        return redirect(url_for('calendar'))
    return render_template('signup.html')

@app.route('/grab_token', methods=['GET', 'POST'])
def payForToken():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        user_id = str(len(users) + 1)
        users[user_id] = User(user_id, username, email)
        
        change_row(1,find_empty(1),username,password,email)
        
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/have_token', methods=['GET', 'POST'])
def useToken():
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
        
        username = get_cell_value(email, "Username")
        passwordPresent = get_cell_value(email, "Password")
        
        if username and passwordPresent == password:
            user_id = str(len(users) + 1)
            
            # Load profile picture based on username
            profile_picture = f"{username}.jpg"
            
            user = User(user_id, username, email, profile_picture=profile_picture)
            users[user_id] = user
            
            signin(email, password)
            login_user(user)  # Log in the user
            
            session['user_email'] = email
            
            return redirect(url_for('calendar'))
    
    return render_template('login.html', sillyFellaAutoLogin=sillyFellaAutoLogin)


    

@app.route('/profile')
@login_required
def profile():
    profile_picture = current_user.profile_picture or 'default.jpg'
    return render_template(
        'profile.html',
        profile_picture=url_for('static', filename=f'profile_pictures/{profile_picture}')
    )




@app.route('/tokenGET')
@login_required
def tokenGET():
    if current_user.is_authenticated:
        if session.get('payment_success'):
            google_sheets.set_cell_value(current_user.email, "PAYUP", "PAIDUP")
        else:
            google_sheets.set_cell_value(current_user.email, "PAYUP", "NOTPAIDUP")
        return render_template('tokenGET.html')
    return redirect(url_for('login'))


@app.route('/logout', methods=['POST'])
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/my_calendar')
@login_required
def my_calendar():
    # Example data dictionary
    data = {
        'total_raised': 1000  # Replace with actual data retrieval logic
    }
    return render_template('my_calendar.html', user=current_user, data=data)

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

YOUR_DOMAIN = 'http://127.0.0.1:5000'

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    Eris = "True"
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

@app.route('/create-payment-link', methods=['POST'])
def create_payment_link():
    tokens = request.form.get('tokens')
    subtokens = request.form.get('subtokens')
    email = current_user.email
    HasPAIDUP = get_cell_value(email, "PAYUP")
    
    tokens = int(tokens)
    subtokens = int(subtokens)

    if HasPAIDUP == "PAIDUP":
        return render_template('tokenGET.html', tokens=tokens, subtokens=subtokens, user_id=current_user.id)
    


    if tokens is None or subtokens is None:
        return "Tokens or Subtokens not provided", 400
    
    
    
    
    
    try:
        payment_link = stripe.PaymentLink.create(
            line_items=[
                {
                    'price': 'price_1QQfi6CpRmcr6sEEz18vGzJ9',  # Replace with your actual price ID
                    'quantity': tokens + subtokens,
                },
            ],
            after_completion={
                'type': 'redirect',
                'redirect': {
                    'url': YOUR_DOMAIN + '/tokenGET',
                },
            },
            metadata={
                'user_id': current_user.id,  # Pass the user ID
                'tokens': tokens,  # Pass the number of tokens to issue
                'subtokens': subtokens  # Pass the number of subtokens to issue
            }
        )
        session['payment_success'] = True
        session['tokens'] = tokens
        session['subtokens'] = subtokens
    except Exception as e:
        return str(e)
    return redirect(payment_link.url, code=303)


@app.route('/customize_tokens', methods=['POST'])
@login_required
def customize_tokens():
    tokens = session.get('tokens')
    subtokens = session.get('subtokens')
    
    if tokens is None or subtokens is None:
        return "Tokens or Subtokens not provided", 400
    
    tokens = int(tokens)
    subtokens = int(subtokens)
    
    try:
        # Generate tokens and subtokens based on user input
        user_token = generate_token()
        extra_tokens = [generate_token() for _ in range(tokens - 1)]
        all_tokens = [user_token] + extra_tokens
        
        all_subtokens = []
        for i in range(tokens):
            subtoken_count = int(request.form.get(f'subtoken_{i}', 0))
            all_subtokens.extend([generate_subtoken(all_tokens[i]) for _ in range(subtoken_count)])
        
        # Save tokens and subtokens to Google Sheets
        user_email = current_user.email
        google_sheets.set_cell_value(user_email, "Token", user_token)
        google_sheets.set_cell_value(user_email, "Xtra", ','.join(extra_tokens + all_subtokens))
        google_sheets.set_cell_value(user_email, "HasToken", "TRUE")
        
        return redirect(url_for('calendar'))
    except Exception as e:
        return str(e), 500
    
    
def generate_token():
    return "DOM-"+(''.join((random.choices(string.ascii_uppercase + string.digits, k=12))))

def generate_subtoken(parent_token):
    return "SUB-"+''.join(parent_token[4:7] + ''.join(random.choices(string.ascii_uppercase + string.digits, k=9)))



@app.route('/verify-email/<token>', methods=['GET'])
def verify_email(token):
    try:
        data = s.loads(token, salt='email-verify', max_age=3600)
        session['verified_email'] = data['email']
        session['verified_token'] = data['token']
        return redirect(url_for('redeem_token'))
    except Exception as e:
        return str(e), 400
    
@app.route('/send-verification-email', methods=['POST'])
def send_verification_email():
    """Sends a verification email to the owner of the token."""
    owner_email = request.json.get('email')
    token = request.json.get('token')

    try:
        verification_link = generate_verification_link(owner_email, token)
        email_body = f"""
        <p>You have a token redemption request:</p>
        <p>Token: {token}</p>
        <p>Please click the link below to confirm:</p>
        <a href="{verification_link}">Verify Token Redemption</a>
        """
        send_email(owner_email, "Token Redemption Request", email_body)
        return jsonify(success=True)
    except Exception as e:
        print(f"Failed to send email: {e}")
        return jsonify(success=False)

    
    
def generate_verification_link(email, token):
    """Generates a secure verification link."""
    token_data = s.dumps({'email': email, 'token': token}, salt='email-verify')
    return url_for('redeem_token', token=token_data, _external=True)

@app.route('/verify-token', methods=['POST'])
def verify_token():
    """Verifies if a token exists and starts the redemption process."""
    token = request.json.get('token')
    google_sheets.preload_google_sheets()

    for email, data in google_sheets.cache.items():
        if token == data.get('Token') or token in data.get('Xtra', '').split(','):
            session['redeemer_email'] = current_user.email
            session['owner_email'] = email
            session['verified_token'] = token

            return jsonify(success=True, token=token, email=email)
    return jsonify(success=False)

@app.route('/redeem-token', methods=['GET', 'POST'])
@login_required
def redeem_token():
    """Handles the redemption process after the owner approves."""
    if request.method == 'POST':
        redeemer_email = session.get('redeemer_email')
        token = session.get('verified_token')
        owner_email = session.get('owner_email')

        if redeemer_email and token and owner_email:
            # Update the redeemer's Google Sheets data
            google_sheets.set_cell_value(redeemer_email, "Token", token)
            google_sheets.set_cell_value(redeemer_email, "HasToken", "TRUE")
            
            # Remove the token from the owner's "Xtra" list
            xtra_tokens = google_sheets.get_cell_value(owner_email, "Xtra").split(',')
            xtra_tokens.remove(token)
            google_sheets.set_cell_value(owner_email, "Xtra", ','.join(xtra_tokens))

            # Refresh Google Sheets data
            google_sheets.preload_google_sheets()

            # Notify the redeemer of the successful process
            session['redemption_approved'] = True
            return jsonify(success=True)
        return jsonify(success=False)
    else:
        redeemer_email = session.get('redeemer_email')
        return render_template('redeem_token.html', redeemer_email=redeemer_email)
    

@app.route('/check-approval-status', methods=['POST'])
def check_approval_status():
    """Polls for the approval status of the token redemption."""
    token = request.json.get('token')
    if token and session.get('redemption_approved'):
        return jsonify(approved=True)
    return jsonify(approved=False)



@app.route('/confirm-redemption', methods=['GET', 'POST'])
@login_required
def confirm_redemption():
    if request.method == 'POST':
        redeemer_email = session.get('redeemer_email')
        token = session.get('verified_token')
        owner_email = session.get('owner_email')
        
        # Add logging to debug
        app.logger.debug(f"Redeemer Email: {redeemer_email}, Token: {token}, Owner Email: {owner_email}")
        
        if redeemer_email and token and owner_email:
            google_sheets.set_cell_value(redeemer_email, "Token", token)
            xtra_tokens = google_sheets.get_cell_value(owner_email, "Xtra").split(',')
            xtra_tokens.remove(token)
            google_sheets.set_cell_value(owner_email, "Xtra", ','.join(xtra_tokens))
            google_sheets.preload_google_sheets()
            session['redemption_approved'] = True
            return jsonify(success=True, redirect_url=url_for('calendar'))
        return jsonify(success=False)
    else:
        redeemer_email = session.get('redeemer_email')
        return render_template('redeem_token.html', redemption_approved=session.get('redemption_approved', False))



def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload-profile-picture', methods=['POST'])
@login_required
def upload_profile_picture():
    if 'profile_picture' not in request.files:
        return redirect(url_for('profile'))

    file = request.files['profile_picture']
    if file.filename == '':
        return redirect(url_for('profile'))

    if file and allowed_file(file.filename):
        # Save the file with the username as the filename
        filename = secure_filename(f"{current_user.username}.jpg")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Update the current_user's profile picture
        current_user.profile_picture = filename

        # Update the users dictionary (if necessary for persistence)
        user = users.get(current_user.id)
        if user:
            user.profile_picture = filename

        return redirect(url_for('profile'))

    return redirect(url_for('profile'))


# Calendar Builder Route
@app.route("/customize-calendar", methods=["GET", "POST"])
@login_required
def customize_calendar():
    if current_user.is_authenticated and get_cell_value(current_user.email, "TokenType") == "DOM":
        if request.method == "POST":
            customizations = {
                "title_banner_color": request.form.get("title_banner_color"),
                "title_color": request.form.get("title_color"),
                "separator_color": request.form.get("separator_color"),
                "text_color": request.form.get("text_color"),
                "title_text": request.form.get("title_text"),
                "banner_title_text": request.form.get("banner_title_text"),
                "bio_text": request.form.get("bio_text"),
                "calendar_border_color": request.form.get("calendar_border_color"),
                "background_spacing": request.form.get("background_spacing"),
                "background_blur": request.form.get("background_blur"),
                "background_size": request.form.get("background_size"),
                "icon": None,
                "background_image": None
            }
            icon = request.files.get("icon")
            if icon and allowed_file(icon.filename):
                filename = secure_filename(icon.filename)
                icon.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                customizations["icon"] = filename

            background_image = request.files.get("background_image")
            if background_image and allowed_file(background_image.filename):
                filename = secure_filename(background_image.filename)
                background_image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                customizations["background_image"] = filename

            # Save customizations to Google Sheets
            user_email = current_user.email
            google_sheets.set_cell_value(user_email, "CAL-TitleBannerColor", customizations["title_banner_color"])
            google_sheets.set_cell_value(user_email, "CAL-TitleColor", customizations["title_color"])
            google_sheets.set_cell_value(user_email, "CAL-SeparatorColor", customizations["separator_color"])
            google_sheets.set_cell_value(user_email, "CAL-TextColor", customizations["text_color"])
            google_sheets.set_cell_value(user_email, "CAL-TitleText", customizations["title_text"])
            google_sheets.set_cell_value(user_email, "CAL-BannerTitleText", customizations["banner_title_text"])
            google_sheets.set_cell_value(user_email, "CAL-BioText", customizations["bio_text"])
            google_sheets.set_cell_value(user_email, "CAL-CalendarBorderColor", customizations["calendar_border_color"])
            google_sheets.set_cell_value(user_email, "CAL-BackgroundSpacing", customizations["background_spacing"])
            google_sheets.set_cell_value(user_email, "CAL-BackgroundBlur", customizations["background_blur"])
            google_sheets.set_cell_value(user_email, "CAL-BackgroundSize", customizations["background_size"])
            if customizations["icon"]:
                google_sheets.set_cell_value(user_email, "CAL-Icon", customizations["icon"])
            if customizations["background_image"]:
                google_sheets.set_cell_value(user_email, "CAL-BackgroundImage", customizations["background_image"])

            return redirect(url_for("calendar"))
        return render_template("calendar_builder.html")
    return redirect(url_for("calendar"))

@app.route('/gift_token', methods=['POST'])
@login_required
def gift_token():
    token = request.form['token']
    recipient_email = request.form['email'].lower()

    # Check if the token exists in the current user's Xtras
    xtra_tokens = google_sheets.get_cell_value(current_user.email, "Xtra").split(',')
    if token not in xtra_tokens:
        return "Hey, this token doesn't exist!", 400

    # Update the recipient's Token cell
    google_sheets.set_cell_value(recipient_email, "Token", token)
    google_sheets.set_cell_value(recipient_email, "HasToken", "TRUE")

    # Set the TokenType based on the token prefix
    if token.startswith("DOM-"):
        google_sheets.set_cell_value(recipient_email, "TokenType", "DOM")
    elif token.startswith("SUB-"):
        google_sheets.set_cell_value(recipient_email, "TokenType", "SUB")

    # Remove the token from the current user's Xtras
    xtra_tokens.remove(token)
    google_sheets.set_cell_value(current_user.email, "Xtra", ','.join(xtra_tokens))

    # Re-preload the Google Sheets data
    google_sheets.preload_google_sheets()

    # Get the recipient's username
    recipient_username = google_sheets.get_cell_value(recipient_email, "Username")

    return recipient_username




import logging

@app.route('/create-date-checkout-session', methods=['POST'])
def create_date_checkout_session():
    data = request.json
    dates = data.get('dates', '').split(',')
    total_cost = sum(int(date.split('-')[2]) for date in dates)

    try:
        user_email = current_user.email  # Assuming you pass the user's email as a query parameter
        if not user_email:
            raise ValueError("User email is required")

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Date Donation',
                    },
                    'unit_amount': total_cost * 100,  # Amount in cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=YOUR_DOMAIN + '/payment-success?dates=' + ','.join(dates) + '&email=' + user_email,
            cancel_url=YOUR_DOMAIN + '/cancel.html',
        )
        return jsonify(url=checkout_session.url)
    except Exception as e:
        logging.error(f"Error creating checkout session: {e}")
        return jsonify(error=str(e)), 500
    
@app.route('/get-consumed-dates', methods=['GET'])
def get_consumed_dates():
    user_email = current_user.email  # Assuming you pass the user's email as a query parameter
    consumed_dates = google_sheets.get_cell_value(user_email, "ConsumedDates")
    return consumed_dates

import json

@app.route('/payment-success')
def payment_success():
    dates = request.args.get('dates', '').split(',')  # Extract selected dates
    user_email = current_user.email  # Retrieve the current user's email

    # Fetch current consumed dates from Google Sheets
    current_consumed_dates = google_sheets.get_cell_value(user_email, "ConsumedDates")

    # Initialize or parse existing consumed dates with zero-padded keys
    if not current_consumed_dates:
        consumed_dates = {f"{i:02d}": False for i in range(1, 32)}  # Zero-padded keys
    else:
        consumed_dates = json.loads(current_consumed_dates)
        # Normalize all keys to zero-padded format
        consumed_dates = {f"{int(k):02d}": v for k, v in consumed_dates.items()}

    # Mark selected dates as consumed, ensuring zero-padded day format
    for date in dates:
        day = f"{int(date.split('-')[2]):02d}"  # Normalize to zero-padded day
        consumed_dates[day] = True

    # Convert back to JSON and update the Google Sheets cell
    new_consumed_dates = json.dumps(consumed_dates, indent=4)
    google_sheets.set_cell_value(user_email, "ConsumedDates", new_consumed_dates)

    # Reload the Google Sheets cache
    google_sheets.preload_google_sheets()

    return redirect(url_for('calendar'))

