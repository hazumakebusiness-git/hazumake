from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import SiteSettings
from .models import SiteSettings, ContactMessage  # add ContactMessage here

def contact(request):
    settings_obj = SiteSettings.get()
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        
        # Simple validation
        if not all([name, email, subject, message]):
            messages.error(request, 'All fields are required.')
            return redirect('contact')
        
        try:
            send_mail(
                subject=f"[Hazumake Contact] {subject} — from {name}",
                message=f"Name: {name}\nEmail: {email}\nMessage:\n{message}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=['hazumakebusiness@gmail.com'],
                fail_silently=False,
            )
            ContactMessage.objects.create(
                name=name,
                email=email,
                subject=subject,
                message=message,
            )
            messages.success(request, "Message sent! We'll get back to you soon.")
        except Exception as e:
            messages.error(request, "Failed to send. Please try reaching us directly.")
        
        return redirect('contact')
    
    return render(request, 'core/contact.html', {
        'settings': settings_obj,
    })
