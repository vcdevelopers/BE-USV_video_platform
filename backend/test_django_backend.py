import os
import sys
import json
import time
import requests

BASE_URL = 'http://127.0.0.1:8000/api'

def run_tests():
    print("====================================================")
    print("STARTING ACCEPTANCE TEST SUITE ON DJANGO BACKEND")
    print("====================================================")

    # 1. Test Public Endpoints
    print("\n[TEST 1] Public Endpoints (languages, site-settings, videos)...")
    res_lang = requests.get(f"{BASE_URL}/languages")
    assert res_lang.status_code == 200, f"Languages failed: {res_lang.status_code}"
    langs = res_lang.json().get('languages', [])
    assert len(langs) > 0, "No languages returned"
    print(f"  [OK] GET /api/languages OK ({len(langs)} languages returned)")

    res_settings = requests.get(f"{BASE_URL}/site-settings")
    assert res_settings.status_code == 200, f"Site settings failed: {res_settings.status_code}"
    settings = res_settings.json().get('settings', {})
    assert 'disclaimer' in settings, "Disclaimer missing in site settings"
    print("  [OK] GET /api/site-settings OK")

    res_videos = requests.get(f"{BASE_URL}/videos?lang=en")
    assert res_videos.status_code == 200, f"Videos list failed: {res_videos.status_code}"
    categories = res_videos.json().get('categories', [])
    assert len(categories) > 0, "No categories returned"
    print(f"  [OK] GET /api/videos?lang=en OK ({len(categories)} categories returned)")

    # 2. Test Admin Login & Authentication
    print("\n[TEST 2] Admin Login & Protection...")
    res_login_bad = requests.post(f"{BASE_URL}/admin/login", json={'email': 'admin@usv.com', 'password': 'wrongpassword'})
    assert res_login_bad.status_code == 401, f"Expected 401 for bad login, got {res_login_bad.status_code}"
    print("  [OK] POST /api/admin/login invalid password correctly blocked (401)")

    res_login = requests.post(f"{BASE_URL}/admin/login", json={'email': 'admin@usv.com', 'password': 'admin123'})
    assert res_login.status_code == 200, f"Login failed: {res_login.status_code} - {res_login.text}"
    login_data = res_login.json()
    token = login_data.get('token')
    assert token, "Token missing in login response"
    print("  [OK] POST /api/admin/login successful, JWT token acquired")

    # Protected routes test without token
    res_unauth = requests.get(f"{BASE_URL}/admin/videos")
    assert res_unauth.status_code == 401, f"Expected 401 for unauthenticated admin access, got {res_unauth.status_code}"
    print("  [OK] Protected route /api/admin/videos correctly blocks unauthenticated requests (401)")

    headers = {'Authorization': f'Bearer {token}'}

    # Test Edit Disclaimer & Site Settings via Admin API
    original_disclaimer = "DISCLAIMER: The exercise guides and wellness recommendations presented in the USV Exercise Portal are designed for practical lifestyle education and patient wellness by USV. They do not substitute professional medical diagnosis, treatment, or clinical advice. Always consult your healthcare provider before undertaking any new physical activity routine."
    test_disclaimer = "TEST DISCLAIMER: Medical advice disclaimer updated by admin."
    res_update_settings = requests.post(f"{BASE_URL}/admin/site-settings", json={'disclaimer': test_disclaimer}, headers=headers)
    assert res_update_settings.status_code == 200, f"Updating site settings failed: {res_update_settings.status_code}"
    # Verify public settings reflects updated disclaimer
    res_public_settings = requests.get(f"{BASE_URL}/site-settings")
    assert res_public_settings.json()['settings']['disclaimer'] == test_disclaimer, "Disclaimer update mismatch"
    # Restore original disclaimer
    requests.post(f"{BASE_URL}/admin/site-settings", json={'disclaimer': original_disclaimer}, headers=headers)
    print("  [OK] POST /api/admin/site-settings PASSED: Medical disclaimer updated & verified via public API")

    # 3. Test Source Trust Boundary on View Events
    print("\n[TEST 3] Source Trust Boundary on View Events...")
    # Spoof source='admin' without auth -> MUST land as 'patient'
    res_event_spoof = requests.post(f"{BASE_URL}/view-events", json={'language': 'en', 'source': 'admin', 'video_id': 14})
    assert res_event_spoof.status_code == 200, f"Event log failed: {res_event_spoof.status_code}"
    logged_spoof = res_event_spoof.json().get('logged', {})
    assert logged_spoof.get('source') == 'patient', f"SECURITY FAILURE: Unauthenticated request landed as source='{logged_spoof.get('source')}' instead of 'patient'!"
    print("  [OK] SECURITY PASSED: Spoofed source='admin' without auth forced to source='patient'")

    # Valid auth source='admin' -> MUST land as 'admin'
    res_event_auth = requests.post(f"{BASE_URL}/view-events", json={'language': 'en', 'source': 'admin', 'video_id': 14}, headers=headers)
    assert res_event_auth.status_code == 200, f"Authenticated event log failed: {res_event_auth.status_code}"
    logged_auth = res_event_auth.json().get('logged', {})
    assert logged_auth.get('source') == 'admin', f"Authenticated request failed to set source='admin', got '{logged_auth.get('source')}'"
    print("  [OK] SECURITY PASSED: Authenticated request correctly accepted source='admin'")

    # 4. Test Update-in-Place Unicity (slot_id, language_code)
    print("\n[TEST 4] Video Upload & Update-in-Place Unicity...")
    upload_payload = {
        'slot_id': '1',
        'category_id': '1',
        'language_code': 'en',
        'target_area': 'Test Legs & Core',
        'video_url_custom': 'http://example.com/test-video.mp4',
        'thumbnail_url_custom': 'http://example.com/test-thumb.jpg',
        'is_active': '1'
    }

    # First upload
    res_up1 = requests.post(f"{BASE_URL}/admin/videos", data=upload_payload, headers=headers)
    assert res_up1.status_code == 200, f"Upload 1 failed: {res_up1.status_code} - {res_up1.text}"
    vid1_id = res_up1.json().get('video_id')
    assert vid1_id, "Video ID missing in upload 1"
    print(f"  [OK] Video uploaded/updated (Video ID: {vid1_id})")

    # Second upload for same slot + language
    upload_payload['target_area'] = 'Updated Legs & Core Target Area'
    res_up2 = requests.post(f"{BASE_URL}/admin/videos", data=upload_payload, headers=headers)
    assert res_up2.status_code == 200, f"Upload 2 failed: {res_up2.status_code} - {res_up2.text}"
    up2_data = res_up2.json()
    vid2_id = up2_data.get('video_id')
    action2 = up2_data.get('action')

    assert vid2_id == vid1_id, f"UNICITY FAILURE: Expected updated video ID {vid1_id}, but got new ID {vid2_id}"
    assert action2 == 'updated', f"Expected action 'updated', got '{action2}'"
    print(f"  [OK] UNICITY PASSED: Re-uploading for slot 1 + lang 'en' updated existing row in-place (ID {vid1_id})")

    # 5. Test Inactive Video Direct Link Enforcement
    print("\n[TEST 5] Inactive Video Direct Link Enforcement...")
    # Toggle video to inactive
    res_toggle = requests.put(f"{BASE_URL}/admin/videos/{vid1_id}/toggle", headers=headers)
    assert res_toggle.status_code == 200, f"Toggle failed: {res_toggle.status_code}"
    assert res_toggle.json().get('is_active') == 0, "Video did not toggle to inactive"
    print(f"  [OK] Video ID {vid1_id} toggled to INACTIVE")

    # Public unauthenticated request to inactive video -> MUST return 403
    res_play_public = requests.get(f"{BASE_URL}/videos/play/{vid1_id}")
    assert res_play_public.status_code == 403, f"INACTIVE ENFORCEMENT FAILURE: Expected 403 for public request to inactive video, got {res_play_public.status_code}"
    print("  [OK] INACTIVE ENFORCEMENT PASSED: Public request to inactive video returned 403 Forbidden")

    # Admin authenticated request to inactive video -> MUST return 200 (preview allowed)
    res_play_admin = requests.get(f"{BASE_URL}/videos/play/{vid1_id}", headers=headers)
    assert res_play_admin.status_code == 200, f"Admin preview failed: {res_play_admin.status_code}"
    print("  [OK] INACTIVE ENFORCEMENT PASSED: Admin preview request to inactive video allowed (200 OK)")

    # Toggle back to active
    requests.put(f"{BASE_URL}/admin/videos/{vid1_id}/toggle", headers=headers)

    # Test Remove Thumbnail
    res_rem_thumb = requests.put(f"{BASE_URL}/admin/videos/{vid1_id}", data={'remove_thumbnail': '1'}, headers=headers)
    assert res_rem_thumb.status_code == 200, f"Remove thumbnail failed: {res_rem_thumb.status_code}"
    print("  [OK] REMOVE THUMBNAIL PASSED: Custom thumbnail cleared successfully")

    # 6. Test Analytics & Excel Export
    print("\n[TEST 6] Admin Analytics Summary & Excel Export...")
    res_analytics = requests.get(f"{BASE_URL}/admin/analytics/summary", headers=headers)
    assert res_analytics.status_code == 200, f"Analytics summary failed: {res_analytics.status_code}"
    analytics_data = res_analytics.json()
    assert 'summary' in analytics_data, "Summary missing in analytics"
    print(f"  [OK] GET /api/admin/analytics/summary OK (Total views: {analytics_data['summary']['totalViews']})")

    res_export = requests.get(f"{BASE_URL}/admin/analytics/export?token={token}")
    assert res_export.status_code == 200, f"Excel export failed: {res_export.status_code}"
    assert res_export.headers.get('Content-Type') == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', "Content-Type header mismatch"
    assert len(res_export.content) > 1000, "Excel export binary content too small"
    print(f"  [OK] GET /api/admin/analytics/export OK ({len(res_export.content)} bytes downloaded)")

    print("\n====================================================")
    print("ALL ACCEPTANCE TESTS PASSED SUCCESSFULLY!")
    print("====================================================")

if __name__ == '__main__':
    run_tests()
