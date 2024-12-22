from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, DateField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange

class PickDateForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=50)])
    date = DateField('Date (YYYY-MM-DD)', validators=[DataRequired()])
    contribution = DecimalField('Contribution Amount ($)', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Submit')
