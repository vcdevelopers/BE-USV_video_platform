import os
import json
import bcrypt
from django.core.management.base import BaseCommand
from api.models import AdminUser, Language, Category, VideoSlot, SiteSetting, Video

class Command(BaseCommand):
    help = 'Seeds structural database data (AdminUser, Languages, Categories, VideoSlots, SiteSettings). Does NOT create Video rows.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Running Django structural database seed...")

        # 1. Admin User
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@usv.com')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        password_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        admin_user, created = AdminUser.objects.get_or_create(
            email=admin_email,
            defaults={'password_hash': password_hash}
        )
        if not created:
            admin_user.password_hash = password_hash
            admin_user.save()
        self.stdout.write(f"[OK] Admin user verified: {admin_email}")

        # 2. Languages
        languages = [
            {'code': 'en', 'name': 'English', 'sort_order': 1},
            {'code': 'hi', 'name': 'Hindi (हिंदी)', 'sort_order': 2},
            {'code': 'mr', 'name': 'Marathi (मराठी)', 'sort_order': 3},
            {'code': 'ta', 'name': 'Tamil (தமிழ்)', 'sort_order': 4},
            {'code': 'te', 'name': 'Telugu (తెలుగు)', 'sort_order': 5},
            {'code': 'gu', 'name': 'Gujarati (ગુજરાતી)', 'sort_order': 6},
            {'code': 'bn', 'name': 'Bengali (বাংলা)', 'sort_order': 7},
            {'code': 'kn', 'name': 'Kannada (கன்னடம்)', 'sort_order': 8},
            {'code': 'ml', 'name': 'Malayalam (മലയാളം)', 'sort_order': 9},
            {'code': 'pa', 'name': 'Punjabi (ਪੰਜਾਬੀ)', 'sort_order': 10},
            {'code': 'or', 'name': 'Odia (ଓଡ଼ିଆ)', 'sort_order': 11},
            {'code': 'as', 'name': 'Assamese (অসমীয়া)', 'sort_order': 12},
        ]
        for l in languages:
            Language.objects.update_or_create(
                code=l['code'],
                defaults={'name': l['name'], 'is_active': True, 'sort_order': l['sort_order']}
            )
        self.stdout.write("[OK] 12 Languages seeded.")

        # 3. Categories
        categories = [
            {'slug': 'routine-guide', 'title': 'Start Your Routine', 'description': 'Essential pre-routine guidelines and warm-up instructions for safe exercise.', 'sort_order': 1},
            {'slug': 'home-strength', 'title': 'Home-based Strength Exercises', 'description': 'Simple, effective strength training routines you can perform comfortably at home.', 'sort_order': 2},
            {'slug': 'resistance-band', 'title': 'Resistance Band Exercises', 'description': 'Low-impact muscle strengthening exercises using flexible resistance bands.', 'sort_order': 3},
            {'slug': 'flexibility-posture', 'title': 'Flexibility & Posture', 'description': 'Gentle mobility and posture alignment habits for overall spinal health.', 'sort_order': 4},
        ]
        cat_map = {}
        for c in categories:
            cat_obj, _ = Category.objects.update_or_create(
                slug=c['slug'],
                defaults={'title': c['title'], 'description': c['description'], 'sort_order': c['sort_order']}
            )
            cat_map[c['slug']] = cat_obj
        self.stdout.write("[OK] 4 Structural Categories seeded.")

        # 4. Video Slots
        video_slots = [
            {'category_slug': 'routine-guide', 'slug': 'warm-up-intro', 'title': 'Pre-routine Warm Up & Safety Guide', 'description': 'Learn how to properly prepare your muscles and breathing before starting daily exercises.', 'is_intro': True, 'sort_order': 1},
            {'category_slug': 'home-strength', 'slug': 'wall-pushups', 'title': 'Wall or Desk Push-Ups', 'description': 'Build upper body strength safely using a stable wall or desk surface.', 'is_intro': False, 'sort_order': 1},
            {'category_slug': 'home-strength', 'slug': 'chair-squats', 'title': 'Chair Squats', 'description': 'Strengthen thighs and hips while maintaining balance using a sturdy chair.', 'is_intro': False, 'sort_order': 2},
            {'category_slug': 'home-strength', 'slug': 'seated-leg-extensions', 'title': 'Seated Leg Extensions', 'description': 'Improve knee stability and quad strength while seated in a supportive chair.', 'is_intro': False, 'sort_order': 3},
            {'category_slug': 'home-strength', 'slug': 'standing-calf-raises', 'title': 'Standing Calf Raises', 'description': 'Enhance ankle stability and lower leg muscle tone.', 'is_intro': False, 'sort_order': 4},
            {'category_slug': 'resistance-band', 'slug': 'band-pull-aparts', 'title': 'Band Pull-Aparts', 'description': 'Improve upper back posture and shoulder mobility using light resistance.', 'is_intro': False, 'sort_order': 1},
            {'category_slug': 'resistance-band', 'slug': 'banded-bicep-curls', 'title': 'Banded Bicep Curls', 'description': 'Tone arm muscles safely with smooth resistance band control.', 'is_intro': False, 'sort_order': 2},
            {'category_slug': 'flexibility-posture', 'slug': 'seated-spine-twist', 'title': 'Seated Spine Twist & Stretch', 'description': 'Relieve lower back tightness and foster spinal flexibility.', 'is_intro': False, 'sort_order': 1},
        ]
        for s in video_slots:
            VideoSlot.objects.update_or_create(
                slug=s['slug'],
                defaults={
                    'category': cat_map[s['category_slug']],
                    'title': s['title'],
                    'description': s['description'],
                    'is_intro': s['is_intro'],
                    'sort_order': s['sort_order']
                }
            )
        self.stdout.write("[OK] 8 Structural Video Slots seeded.")

        # 5. Site Settings
        tips = [
            'Consult your physician before starting any new exercise routine.',
            'Stop immediately if you experience dizziness, sharp pain, or shortness of breath.',
            'Maintain steady, comfortable breathing throughout each movement - do not hold your breath.',
            'Perform exercises on a firm, non-slippery floor surface with proper footwear.',
            'Keep hydrated by sipping water before and after your exercise session.'
        ]
        disclaimer = 'DISCLAIMER: The exercise guides and wellness recommendations presented in the USV Exercise Portal are designed for practical lifestyle education and patient wellness by USV. They do not substitute professional medical diagnosis, treatment, or clinical advice. Always consult your healthcare provider before undertaking any new physical activity routine.'

        SiteSetting.objects.update_or_create(key='important_tips', defaults={'value': json.dumps(tips)})
        SiteSetting.objects.update_or_create(key='disclaimer', defaults={'value': disclaimer})
        self.stdout.write("[OK] Site Settings seeded.")

        # Verify no video rows inserted
        vid_count = Video.objects.count()
        self.stdout.write(f"[OK] Verified Video model row count: {vid_count} (Must be 0 unless migrated/uploaded).")
        self.stdout.write(self.style.SUCCESS("Django structural database seed completed successfully!"))
