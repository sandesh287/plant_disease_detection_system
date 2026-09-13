from django.shortcuts import render, redirect
from django.contrib import messages
from werkzeug.security import generate_password_hash, check_password_hash
from .db import get_db
from .predict import predict, is_plant_image
import os
from django.conf import settings
import uuid
from django import forms
from .models import *
from django.core.exceptions import ValidationError
from bson import ObjectId
from django.core.files.storage import FileSystemStorage
from gridfs import GridFS
from django.http import HttpResponse
from .forms import ProfileUpdateForm

db = get_db()

def home(request):
    plant_data = db.plant_info
    plants = plant_data.find()
    return render(request, 'home.html', {'plants': plants})

def about(request):
    return render(request, 'about.html')

# Backend: Signup view
def signup(request):
    if request.method == "POST":
        full_name = request.POST.get("name")
        email = request.POST.get("email")
        password = request.POST.get("password1")
        confirm_password = request.POST.get("password2")
        phone = request.POST.get("phone")
        gender = request.POST.get("gender")
        location = request.POST.get("address")

        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return render(request, 'signup.html')

        hashed_password = generate_password_hash(password)
        
        if db.user.find_one({'email': email}):
            messages.error(request, "Email already exists!")
            return render(request, 'signup.html')
        
        db.user.insert_one({
            'full_name': full_name,
            'email': email,
            'password': hashed_password,
            'phone': phone,
            'role': 'user',
            'gender': gender,
            'location': location,
        })
        
        messages.success(request, "Signup successful! Please log in.")
        return redirect('login')

    return render(request, 'signup.html')

# Backend: Login View
def login(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        db = get_db()
        user = db.user.find_one({"email": email})
        
        if user and check_password_hash(user["password"], password):
            auth_token = str(uuid.uuid4())
            db.user.update_one({"email": email}, {"$set": {"auth_token": auth_token}})

            response = redirect('test')
            response.set_cookie('auth_token', auth_token)

            if user.get('role') == 'admin':
                response = redirect('admin')
                response.set_cookie('auth_token', auth_token)
                
            return response
        else:
            messages.error(request, "Invalid credentials")
            return render(request, "login.html")
    else:
        return render(request, "login.html")

# Backend: Logout View
def logout(request):
    response = redirect('login')
    response.delete_cookie('auth_token')
    messages.success(request, "Logged out successfully!")
    return response

ALLOWED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png']

def handle_uploaded_file(f):
    file_extension = os.path.splitext(f.name)[1].lower()
    if file_extension not in ALLOWED_IMAGE_FORMATS:
        raise ValidationError(f"Unsupported file format. Please upload an image in {','.join(ALLOWED_IMAGE_FORMATS)} format.")

    upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)

    storage = FileSystemStorage(location=upload_dir, base_url=f"{settings.MEDIA_URL}uploads/")
    saved_name = storage.save(f.name, f)
    file_path = storage.path(saved_name)
    file_url = storage.url(saved_name)
    return file_path, file_url

# Backend: Main Detection and Validation View
def test(request):
    is_authenticated = request.COOKIES.get('auth_token') is not None
    error = None
    
    if request.method == "POST":
        if "image" in request.FILES:
            uploaded_image = request.FILES["image"]

            try:
                file_path, uploaded_image_url = handle_uploaded_file(uploaded_image)

                # Backend Validation Step: Check if uploaded file is actually a plant
                if not is_plant_image(file_path):
                    raise ValidationError("The uploaded image is not recognized as a plant or leaf. Please upload a clear plant image.")

                # Proceed to Disease Detection
                predicted_class = predict(file_path)

                if predicted_class.lower() == "healthy":
                    disease_info = db["disease_data"].find_one({"disease_name": "Healthy"})
                else:
                    disease_info = db["disease_data"].find_one({"disease_name": predicted_class})

                if not disease_info:
                    partial_info = {"disease_name": predicted_class, "description": "No detailed information available for this disease."}
                    full_info = None
                else:
                    partial_info = {
                        "disease_name": disease_info.get("disease_name", "Unknown disease"),
                        "description": disease_info.get("description", "Description not available."),
                    }
                    full_info = {
                        "disease_name": disease_info.get("disease_name", "Unknown disease"),
                        "description": disease_info.get("description", "Description not available."),
                        "prevention": disease_info.get("prevention", "Prevention information not available."),
                        "treatment": disease_info.get("treatment", "Treatment information not available."),
                    }

                return render(request, "test.html", {
                    "predicted_class": predicted_class,
                    "partial_info": partial_info,
                    "full_info": full_info if is_authenticated else None,
                    "is_authenticated": is_authenticated,
                    "error": error,
                    "uploaded_image_url": uploaded_image_url,
                })

            except ValidationError as e:
                error = e.message if isinstance(e.message, str) else e.message[0]
                return render(request, "test.html", {"error": error, "is_authenticated": is_authenticated})
            
            except Exception as e:
                error = f"An unexpected error occurred: {str(e)}"
                return render(request, "test.html", {"error": error, "is_authenticated": is_authenticated})

    return render(request, "test.html", {"is_authenticated": is_authenticated})

# Backend: Profile Views
def profile(request):
    if not request.mongo_user:
        return redirect('login')

    db = get_db()
    user_data = db.user.find_one({"_id": ObjectId(request.mongo_user['_id'])})

    if user_data:
        full_name = user_data.get("full_name", "")
        email = user_data.get("email", "")
        phone = user_data.get("phone", "")
        gender = user_data.get("gender", "")
        location = user_data.get("location", "")
    else:
        full_name = email = phone = gender = location = ""

    profile_data = db.profile_details.find_one({"user_id": ObjectId(request.mongo_user['_id'])})

    return render(request, 'profile.html', {
        'user_data': user_data,
        'profile_data': profile_data,
        'full_name': full_name,
        'email': email,
        'phone': phone,
        'gender': gender,
        'location': location
    })

def update_profile(request):
    if not request.mongo_user:
        return redirect('login')

    db = get_db()
    fs = GridFS(db)
    user_data = db.user.find_one({"_id": request.mongo_user['_id']})
    profile_data = db.profile_details.find_one({"user_id": request.mongo_user['_id']})

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES)
        if form.is_valid():
            updated_data = form.cleaned_data
            
            if 'profile_picture' in request.FILES:
                profile_picture = request.FILES['profile_picture']
                file_id = fs.put(profile_picture)
                updated_data['profile_picture'] = file_id

            if profile_data:
                db.profile_details.update_one(
                    {"user_id": request.mongo_user['_id']},
                    {"$set": updated_data}
                )
            else:
                updated_data['user_id'] = request.mongo_user['_id']
                db.profile_details.insert_one(updated_data)

            return redirect('user_profile')
    else:
        initial_data = {
            'bio': profile_data.get('bio', '') if profile_data else '',
            'profile_picture': profile_data.get('profile_picture', '') if profile_data else ''
        }
        form = ProfileUpdateForm(initial=initial_data)

    return render(request, 'update_profile.html', {'form': form, 'user_data': user_data})

def view_image(request, file_id):
    db = get_db()
    fs = GridFS(db)
    file = fs.get(ObjectId(file_id))
    response = HttpResponse(file.read(), content_type='image/jpeg')
    response['Content-Disposition'] = f'inline; filename="{file.filename}"'
    return response