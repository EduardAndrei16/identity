from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings

class OktaAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the user is authenticated or accessing a public path
        public_paths = [
            reverse('login'),
            '/oauth2/callback/',
            '/api/auth/callback',
            '/admin/login/',
            '/static/',
            '/accounts/login/',  # Make sure this is included
        ]
        
        # Allow access to public paths
        path = request.path
        if any(path.startswith(public_path) for public_path in public_paths):
            return self.get_response(request)
            
        # If not authenticated and not accessing a public path, redirect to login
        if not request.user.is_authenticated:
            return redirect('login')
            
        return self.get_response(request)