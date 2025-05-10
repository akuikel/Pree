from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, LeaseAgreement

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

from django import forms
from django.contrib.auth.forms import UserCreationForm
from datetime import date
from .models import CustomUser

class SignupForm(UserCreationForm):
    phone_number = forms.CharField(
        max_length=15,
        required=True,
        help_text="Enter your phone number.",
        error_messages={
            'required': 'Please provide your phone number.',
            'max_length': 'Phone number cannot exceed 15 characters.',
        }
    )
    address = forms.CharField(
        required=True,
        help_text="Enter your address.",
        error_messages={
            'required': 'Please provide your address.',
        }
    )
    company_name = forms.CharField(
        max_length=255,
        required=False,
        help_text="If you're a property owner, enter your company name.",
    )
    date_of_birth = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text="Enter your date of birth.",
        error_messages={
            'required': 'Please provide your date of birth.',
        }
    )
    user_type = forms.ChoiceField(
        choices=CustomUser.USER_TYPE_CHOICES,
        required=True,
        help_text="Select your user type.",
        error_messages={
            'required': 'Please select your user type.',
        }
    )

    class Meta:
        model = CustomUser
        fields = [
            'username',
            'email',
            'password1',
            'password2',
            'phone_number',
            'address',
            'company_name',
            'date_of_birth',
            'user_type'
        ]

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number.replace("+", "").isdigit():
            raise forms.ValidationError("Phone number must contain only digits and '+' for international format.")
        if len(phone_number) < 10:
            raise forms.ValidationError("Phone number must have at least 10 digits.")
        return phone_number

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 18:
                raise forms.ValidationError("You must be at least 18 years old to register.")
        return dob



from django import forms

class LoginForm(forms.Form):
    email = forms.EmailField(max_length=254)
    password = forms.CharField(widget=forms.PasswordInput)


from django import forms
from django.contrib.auth import authenticate

class EmailAuthenticationForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        if email and password:
            self.user = authenticate(email=email, password=password)
            if not self.user:
                raise forms.ValidationError("Invalid email or password")
        return self.cleaned_data

    def get_user(self):
        return self.user


# forms.py
from django import forms

class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(label="Enter your email", widget=forms.EmailInput(attrs={'class': 'form-control'}))


from django import forms
from .models import MaintenanceRequest

class MaintenanceRequestForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRequest
        fields = ['subject', 'description', 'priority', 'attachment']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Water leak in bathroom'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe the issue in detail...'
            }),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'attachment': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(MaintenanceRequestForm, self).__init__(*args, **kwargs)
        self.fields['attachment'].required = False
        
    def clean_attachment(self):
        attachment = self.cleaned_data.get('attachment')
        if attachment:
            # Get the file extension
            ext = attachment.name.split('.')[-1].lower()
            valid_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp']
            
            if ext not in valid_extensions:
                raise forms.ValidationError("Only image files are allowed (jpg, jpeg, png, gif, etc.).")
            
            # Check file size (limit to 5MB)
            if attachment.size > 5 * 1024 * 1024:  # 5MB in bytes
                raise forms.ValidationError("The image file size should not exceed 5MB.")
                
        return attachment


class LeaseAgreementForm(forms.ModelForm):
    class Meta:
        model = LeaseAgreement
        fields = ['user', 'text_message', 'file_message', 'verification_doc']

# Create a new file: user/forms.py (add this to your existing forms.py)

from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your last name'
            }),
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make email field required
        self.fields['email'].required = True