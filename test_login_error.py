#!/usr/bin/env python
"""Test script to reproduce login/Firebase session error."""
import os
import sys
import django
import json
from django.test import Client
from django.urls import reverse

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hazu.settings')
django.setup()

# Add testserver to ALLOWED_HOSTS for testing
from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

# Initialize test client
client = Client(enforce_csrf_checks=True)

print("=" * 70)
print("TEST 1: Firebase Session with Invalid Token (no CSRF)")
print("=" * 70)

# Test 1: POST invalid token without CSRF token
response = client.post('/auth/firebase-session/', 
    data=json.dumps({'id_token': 'invalid_token_123'}),
    content_type='application/json'
)
print(f"Status: {response.status_code}")
print(f"Content-Type: {response.get('Content-Type')}")
print(f"Body: {response.content.decode()}")
print()

print("=" * 70)
print("TEST 2: Firebase Session with Invalid Token (with CSRF)")
print("=" * 70)

# Get CSRF token first
csrf_response = client.get('/auth/signin/')
csrf_token = csrf_response.cookies.get('csrftoken')
if csrf_token:
    csrf_token = csrf_token.value
    print(f"CSRF Token obtained: {csrf_token[:20]}...")
else:
    print("WARNING: No CSRF token found")
    csrf_token = ""

# Test 2: POST invalid token WITH CSRF token
headers = {
    'X-CSRFToken': csrf_token,
    'Content-Type': 'application/json'
}

response = client.post('/auth/firebase-session/', 
    data=json.dumps({'id_token': 'invalid_token_456'}),
    content_type='application/json',
    HTTP_X_CSRFTOKEN=csrf_token
)
print(f"Status: {response.status_code}")
print(f"Content-Type: {response.get('Content-Type')}")
print(f"Body: {response.content.decode()}")
print()

print("=" * 70)
print("TEST 3: Firebase Session with Empty Token")
print("=" * 70)

# Test 3: POST with empty/missing token
response = client.post('/auth/firebase-session/', 
    data=json.dumps({}),
    content_type='application/json',
    HTTP_X_CSRFTOKEN=csrf_token
)
print(f"Status: {response.status_code}")
print(f"Content-Type: {response.get('Content-Type')}")
print(f"Body: {response.content.decode()}")
print()

print("=" * 70)
print("TEST 4: Firebase Session with Malformed JSON")
print("=" * 70)

# Test 4: Malformed JSON
response = client.post('/auth/firebase-session/', 
    data='not valid json',
    content_type='application/json',
    HTTP_X_CSRFTOKEN=csrf_token
)
print(f"Status: {response.status_code}")
print(f"Content-Type: {response.get('Content-Type')}")
print(f"Body: {response.content.decode()}")
print()

print("=" * 70)
print("DONE")
print("=" * 70)
