import os
import shutil
import sqlite3
import datetime
from django.conf import settings
from django.core.management.base import BaseCommand
from api.models import AdminUser, Language, Category, VideoSlot, Video, ViewEvent, SiteSetting

class Command(BaseCommand):
    help = 'Migrates existing real video data and view events from frontend/server/database.sqlite to Django database'

    def handle(self, *args, **kwargs):
        old_db_path = os.path.join(settings.BASE_DIR.parent, 'frontend', 'server', 'database.sqlite')
        if not os.path.exists(old_db_path):
            self.stdout.write(self.style.WARNING(f"Old SQLite database not found at {old_db_path}. Skipping data migration."))
            return

        self.stdout.write(f"Connecting to old SQLite database at {old_db_path}...")
        conn = sqlite3.connect(old_db_path)
        cursor = conn.cursor()

        # 1. Copy Uploaded Files
        old_uploads_dir = os.path.join(settings.BASE_DIR.parent, 'frontend', 'public', 'uploads')
        new_uploads_dir = settings.MEDIA_ROOT
        os.makedirs(new_uploads_dir, exist_ok=True)

        if os.path.exists(old_uploads_dir):
            files_copied = 0
            for fname in os.listdir(old_uploads_dir):
                src_file = os.path.join(old_uploads_dir, fname)
                dst_file = os.path.join(new_uploads_dir, fname)
                if os.path.isfile(src_file) and not os.path.exists(dst_file):
                    shutil.copy2(src_file, dst_file)
                    files_copied += 1
            self.stdout.write(f"[OK] Copied {files_copied} media upload files to {new_uploads_dir}")

        # 2. Migrate Categories
        cursor.execute("SELECT id, slug, title, description, sort_order FROM categories")
        cat_rows = cursor.fetchall()
        for c in cat_rows:
            Category.objects.update_or_create(
                id=c[0],
                defaults={'slug': c[1], 'title': c[2], 'description': c[3] or '', 'sort_order': c[4] or 99}
            )
        self.stdout.write(f"[OK] Migrated {len(cat_rows)} categories.")

        # 3. Migrate Video Slots
        cursor.execute("SELECT id, category_id, slug, title, description, is_intro, sort_order FROM video_slots")
        slot_rows = cursor.fetchall()
        for s in slot_rows:
            cat_obj = Category.objects.filter(id=s[1]).first()
            if cat_obj:
                VideoSlot.objects.update_or_create(
                    id=s[0],
                    defaults={
                        'category': cat_obj,
                        'slug': s[2],
                        'title': s[3],
                        'description': s[4] or '',
                        'is_intro': bool(s[5]),
                        'sort_order': s[6] or 99
                    }
                )
        self.stdout.write(f"[OK] Migrated {len(slot_rows)} video slots.")

        # 4. Migrate Real Videos
        cursor.execute("SELECT id, slot_id, language_code, video_url, thumbnail_url, created_at, is_active, target_area FROM videos")
        video_rows = cursor.fetchall()
        migrated_vids = 0
        for v in video_rows:
            slot_obj = VideoSlot.objects.filter(id=v[1]).first()
            if slot_obj:
                Video.objects.update_or_create(
                    id=v[0],
                    defaults={
                        'slot': slot_obj,
                        'language_code': v[2] or 'en',
                        'video_url': v[3],
                        'thumbnail_url': v[4] or '',
                        'is_active': bool(v[6]),
                        'target_area': v[7] or ''
                    }
                )
                migrated_vids += 1
        self.stdout.write(f"[OK] Migrated {migrated_vids} real video entries.")

        # 5. Migrate View Events
        cursor.execute("SELECT id, timestamp, language, device_type, ip_address, country, city, video_id, source FROM view_events")
        event_rows = cursor.fetchall()
        migrated_events = 0
        for e in event_rows:
            video_obj = Video.objects.filter(id=e[7]).first() if e[7] else None
            ViewEvent.objects.update_or_create(
                id=e[0],
                defaults={
                    'language': e[2] or 'en',
                    'device_type': e[3] or 'desktop',
                    'ip_address': e[4] or '127.0.0.1',
                    'country': e[5] or 'India',
                    'city': e[6] or 'Mumbai',
                    'video': video_obj,
                    'source': e[8] or 'patient'
                }
            )
            migrated_events += 1
        self.stdout.write(f"[OK] Migrated {migrated_events} view events.")

        conn.close()
        self.stdout.write(self.style.SUCCESS("Data migration completed successfully!"))
