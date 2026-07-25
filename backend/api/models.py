from django.db import models

class AdminUser(models.Model):
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

class Language(models.Model):
    code = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=99)

    def __str__(self):
        return f"{self.name} ({self.code})"

class Category(models.Model):
    slug = models.CharField(max_length=150, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    sort_order = models.IntegerField(default=99)

    def __str__(self):
        return self.title

class VideoSlot(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='slots')
    slug = models.CharField(max_length=150, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    is_intro = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=99)

    def __str__(self):
        return self.title

class Video(models.Model):
    slot = models.ForeignKey(VideoSlot, on_delete=models.CASCADE, related_name='videos')
    language_code = models.CharField(max_length=10, default='en')
    video_url = models.CharField(max_length=500)
    thumbnail_url = models.CharField(max_length=500, blank=True, default='')
    target_area = models.CharField(max_length=255, blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('slot', 'language_code')

    def __str__(self):
        return f"Video #{self.id} for {self.slot.title} ({self.language_code})"

class ViewEvent(models.Model):
    language = models.CharField(max_length=10)
    device_type = models.CharField(max_length=50, default='desktop')
    ip_address = models.CharField(max_length=50, default='127.0.0.1')
    country = models.CharField(max_length=100, default='India')
    city = models.CharField(max_length=100, default='Mumbai')
    video = models.ForeignKey(Video, on_delete=models.SET_NULL, null=True, blank=True, related_name='view_events')
    source = models.CharField(max_length=20, default='patient') # 'patient' or 'admin'
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ViewEvent #{self.id} ({self.source}) - {self.language}"

class SiteSetting(models.Model):
    key = models.CharField(max_length=100, primary_key=True)
    value = models.TextField()

    def __str__(self):
        return self.key
