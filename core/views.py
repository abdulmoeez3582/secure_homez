from django.shortcuts import render, HttpResponse, redirect
from .models import *
from .forms import *
import RPi.GPIO as GPIO
import time
import face_recognition
import cv2
import numpy as np
import RPi.GPIO as GPIO
# import winsound
from django.db.models import Q
from playsound import playsound
from django.core.mail import send_mail
import os
import time
import datetime


last_face = 'no_face'
current_path = os.path.dirname(__file__)
sound_folder = os.path.join(current_path, 'sound/')
face_list_file = os.path.join(current_path, 'face_list.txt')
sound = os.path.join(sound_folder, 'beep.wav')

def login(request):
    return render(request, 'core/login.html')
def login_admin(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        login = MainUser.loginByUsername(username)
        if login:
            chk = check_password(password,login.password)
            if chk:
                request.session['customerName'] = login.first_name + ' ' + login.last_name
                return redirect('/profiles')
            else:
                return redirect('/login')
        else:
            return redirect('/')
def logout(request):
    del request.session['customerName']
    return redirect('/')

def register(request):
    if request.method == "POST":
        fname = request.POST.get('fname')
        lname = request.POST.get('lname')
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        cpassword = request.POST.get('cpassword')
        if password == cpassword:
            encpass = make_password(cpassword)
            get_Register = MainUser(first_name=fname,last_name=lname,email=email,user_name=username,password=encpass)
            get_Register.register()
            redirect('/login')
        else:
            return render(request, 'core/register.html')

    return render(request,'core/register.html')


def index(request):
    render(request,'core/login.html')
    scanned = LastFace.objects.all().order_by('date').reverse()
    present = Profile.objects.all()
    context = {
        'scanned': scanned,
        'present': present,
    }
    GPIO.setmode(GPIO.BCM)

    GPIO.setwarnings(False)

    GPIO.setup(23, GPIO.OUT)
    GPIO.setup(24, GPIO.IN)

    while True:
        i = GPIO.input(24)
        if i == 1:
            print("Detection" + str(i))
            print("On")
            return redirect('/scan')
            # Buzzer


        else:
            print("Not Detected" + str(i))


    return render(request, 'core/index.html', context)


def ajax(request):
    last_face = LastFace.objects.last()
    context = {
        'last_face': last_face
    }
    return render(request, 'core/ajax.html', context)


def scan(request):

    global last_face

    known_face_encodings = []
    known_face_names = []

    profiles = Profile.objects.all()
    for profile in profiles:
        person = profile.image
        image_of_person = face_recognition.load_image_file(f'media/{person}')
        person_face_encoding = face_recognition.face_encodings(image_of_person)[0]
        known_face_encodings.append(person_face_encoding)
        known_face_names.append(f'{person}'[:-4])


    video_capture = cv2.VideoCapture(-1)

    face_locations = []
    face_encodings = []
    face_names = []
    process_this_frame = True
    GPIO.setmode(GPIO.BCM)

    GPIO.setwarnings(False)

    GPIO.setup(23, GPIO.OUT)
    GPIO.setup(24, GPIO.IN)
    img_counter=0

    while True:

        ret, frame = video_capture.read()
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = small_frame[:, :, ::-1]

        if process_this_frame:
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(
                rgb_small_frame, face_locations)

            face_names = []
            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(
                    known_face_encodings, face_encoding)
                name = "Unknown"
                if name == "Unknown":
                    print("uknown face detect")
                    GPIO.output(23, GPIO.HIGH)
                    time.sleep(0.3)
                    image_name=f'opencv_frame_{img_counter}'
                    GPIO.output(23, GPIO.LOW)
                    cv2.imwrite("Unknown/"+str(datetime.datetime.now())+'.jpg',frame)
                    print("Screen Shot Taken")
                    img_counter+=1




                    face_distances = face_recognition.face_distance(
                    known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = known_face_names[best_match_index]

                    profile = Profile.objects.get(Q(image__icontains=name))
                    if profile.first_name == True:
                        pass
                    else:
                        profile.first_name = True
                        profile.save()

                        if last_face != name:
                            last_face = LastFace(last_face=name)
                            last_face.save()
                            last_face = name
                            # winsound.PlaySound(sound, winsound.SND_ASYNC)
                        else:
                            pass

                face_names.append(name)

        process_this_frame = not process_this_frame

        for (top, right, bottom, left), name in zip(face_locations, face_names):
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

            cv2.rectangle(frame, (left, bottom - 35),
                          (right, bottom), (0, 0, 255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 6, bottom - 6),
                        font, 0.5, (255, 255, 255), 1)

        cv2.imshow('Video', frame)

        key = cv2.waitKey(1)

        if key == 27:
            break

    video_capture.release()
    cv2.destroyAllWindows()
    return HttpResponse('scaner closed', last_face)


def profiles(request):
    profiles = Profile.objects.all()
    context = {
        'profiles': profiles
    }
    return render(request, 'core/profiles.html', context)


def details(request):
    try:
        last_face = LastFace.objects.last()
        profile = Profile.objects.get(Q(image__icontains=last_face))
    except:
        last_face = None
        profile = None

    context = {
        'profile': profile,
        'last_face': last_face
    }
    return render(request, 'core/details.html', context)


def add_profile(request):
    form = ProfileForm
    if request.method == 'POST':
        firstname = request.POST.get('first_name')
        lastname = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        date = request.POST.get('date')
        relation = request.POST.get('relation')
        image = request.FILES['image']
        if firstname and lastname and email and phone and date and relation and image:
                send_mail(
                    'Member Addition',
                    'This Email Recieve Because you just register over here',
                    'amoeez14@gmail.com',
                    [email],
                    fail_silently=False,
                )
                # subject,from_email,to_email = "Profile ","servermailworks@gmail.com",email
                # html_content = render_to_string("core/sendmail.html", {'firstname': firstname, 'lastname': lastname})
                # text_content = "This is registeration email"
                # emailsend = EmailMultiAlternatives(subject,text_content,from_email,[to_email])
                # emailsend.attach_alternative(html_content, "text/html")
                # emailsend.send()
                save_profile = Profile()
                save_profile.first_name = firstname
                save_profile.last_name = lastname
                save_profile.phone = phone
                save_profile.email = email
                save_profile.date = date
                save_profile.status = relation
                save_profile.image = image
                save_profile.save()
                return redirect('profiles')
        else:
            context = {'form': form, 'error':"Email Already In Use"}
            return render(request, 'core/add_profile.html', context)
    else:
        context={'form':form}
        return render(request,'core/add_profile.html',context)


def edit_profile(request,id):
    profile = Profile.objects.get(id=id)
    form = ProfileForm(instance=profile)
    if request.method == 'POST':
        form = ProfileForm(request.POST,request.FILES,instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profiles')
    context={'form':form}
    return render(request,'core/add_profile.html',context)


def delete_profile(request,id):
    profile = Profile.objects.get(id=id)
    profile.delete()
    return redirect('profiles')


def clear_history(request):
    history = LastFace.objects.all()
    history.delete()
    return redirect('index')


def reset(request):
    profiles = Profile.objects.all()
    for profile in profiles:
        if profile.present == True:
            profile.present = False
            profile.save()
        else:
            pass
    return redirect('index')




