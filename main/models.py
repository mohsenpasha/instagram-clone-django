from django.db import models

from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser

from PIL import Image
import os
from django.core.files.base import ContentFile
from io import BytesIO
import cv2
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
# Create your models here.

class CustomUser(AbstractUser):
	phone_number = models.CharField(unique=True,max_length=12,blank=True,null=True)
	full_name = models.CharField(max_length=200,blank=True,default='')
	img = models.ImageField(upload_to ='profile/',null=True,blank=True)
	birthday = models.DateField(default='2000-01-01')
	is_private = models.BooleanField(default=False)
	# def get_absolute_url(self):
	# 		if self.img and hasattr(self.img, 'url'):
	# 			return f"{settings.SITE_URL}{self.img.url}"
	# 		return f"{settings.SITE_URL}/media/uploads/user-profile.png"

	def __str__(self):
		return(self.username + ' ' + self.first_name + ' ' + self.last_name)

class Follower(models.Model):
    follower = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="following")
    following = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="followers")

    class Meta:
        unique_together = ('follower', 'following')

    def __str__(self):
        return f"{self.follower} follows {self.following}"

class Hashtag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"#{self.name}"


class Tagged(models.Model):
    user = models.ForeignKey(CustomUser,on_delete=models.CASCADE, related_name="tagged")
    x = models.FloatField(null=True,blank=True)
    y = models.FloatField(null=True,blank=True)

    def __str__(self):
        return f"#{self.user}"


class Post(models.Model):
	user = models.ForeignKey(CustomUser,
		on_delete=models.CASCADE)
	caption = models.TextField(null=True,blank=True,default="")
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	is_pinned = models.BooleanField(default=False)
	shares_count = models.IntegerField(default=0)
	hashtags = models.ManyToManyField(Hashtag,
		blank=True,
		related_name="posts")
	location = models.CharField(max_length=255, blank=True, null=True)
	disable_comments = models.BooleanField(default=False)

	def __str__(self):
		return self.user.username + ' | ' + self.caption or ""


class Notification(models.Model):
    NOTIF_TYPES = [
        ('follow', 'Follow'),
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('mention', 'Mention'),
    ]

    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_notifications')
    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(choices=NOTIF_TYPES, max_length=20)
    message = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")

    def __str__(self):
        return f"{self.sender} → {self.recipient} [{self.type}]"

class DirectMessage(models.Model):
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="sent_messages")
    receiver = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="received_messages")
    message = models.TextField()
    is_read = models.BooleanField(default=False)  # آیا پیام خوانده شده؟
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"From {self.sender} to {self.receiver} at {self.created_at}"


class PostSave(models.Model):
    user = models.ForeignKey(CustomUser,
        on_delete=models.CASCADE)
    post = models.ForeignKey(Post,
        on_delete=models.CASCADE,
        related_name="saves")
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('user', 'post')

class SavedFolder(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=100,unique=True)
    saved_posts = models.ManyToManyField(PostSave,
        blank=True,
        related_name="saved_posts")

    def __str__(self):
        return f"{self.user.username}"

class PostLike(models.Model):
	user = models.ForeignKey(CustomUser,
		on_delete=models.CASCADE)
	post = models.ForeignKey(Post,
		on_delete=models.CASCADE,
		related_name="likes")
	created_at = models.DateTimeField(auto_now_add=True)
	class Meta:
		unique_together = ('user', 'post')


class Comment(models.Model):
	comment = models.TextField()
	user = models.ForeignKey(CustomUser,on_delete=models.CASCADE)
	post = models.ForeignKey(Post,
		on_delete=models.CASCADE)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	replied_to = models.ForeignKey("self",
        on_delete=models.CASCADE,
        null=True,  #
        blank=True,
        related_name="replies")

class CommentLike(models.Model):
	user = models.ForeignKey(CustomUser,
		on_delete=models.CASCADE)
	comment = models.ForeignKey(Comment,
		on_delete=models.CASCADE,
		related_name="comment_likes")
	created_at = models.DateTimeField(auto_now_add=True)



class PostMedia(models.Model):
    MEDIA_TYPES = [
        ('image', 'Image'),
        ('video', 'Video'),
    ]
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="media")
    thumbnail = models.ImageField(upload_to="thumbnails/", null=True, blank=True)
    file = models.FileField(upload_to="posts/")
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    order = models.PositiveIntegerField(default=0)
    tagged_users = models.ManyToManyField(Tagged,
        blank=True,
        related_name="tagged")
    def save(self, *args, **kwargs):
        """ذخیره تامبنیل فقط برای `order = 1`"""
        if self.order == 1:
            if not self.thumbnail:  # اگر تامبنیل نداشت، ایجاد کن
                if self.media_type == "image":
                    self.create_image_thumbnail()
                elif self.media_type == "video":
                    self.create_video_thumbnail()
        else:
            self.thumbnail = None  # اگر `order != 1` بود، تامبنیل را حذف کن

        super().save(*args, **kwargs)

    def __str__(self):
        return self.post.caption

    def create_image_thumbnail(self):
        if not self.file:
            return

        img = Image.open(self.file)
        img.thumbnail((350, 350))
        thumb_io = BytesIO()
        img.save(thumb_io, format="JPEG", quality=80)
        thumb_filename = f"thumb_{os.path.basename(self.file.name)}"
        self.thumbnail.save(thumb_filename, ContentFile(thumb_io.getvalue()), save=False)

    def create_video_thumbnail(self):
        if not self.file:
            return
        
        video_path = self.file.path
        cap = cv2.VideoCapture(video_path)

        success, frame = cap.read()
        cap.release()

        if success:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # تبدیل رنگ از BGR به RGB
            img = Image.fromarray(frame)
            img.thumbnail((350, 350))

            thumb_io = BytesIO()
            img.save(thumb_io, format="JPEG", quality=80)
            thumb_filename = f"thumb_{os.path.basename(self.file.name)}.jpg"
            self.thumbnail.save(thumb_filename, ContentFile(thumb_io.getvalue()), save=False)

    def get_preview_image(self):
        """برگرداندن آدرس تامبنیل، در غیر این صورت تصویر اصلی"""
        return self.thumbnail.url if self.thumbnail else self.file.url


class Story(models.Model):
    MEDIA_TYPES = [
        ('image', 'Image'),
        ('video', 'Video'),
    ]
    user = models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    file = models.FileField(upload_to="stories/",default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Highlight(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    stories = models.ManyToManyField(Story,
        blank=True,
        related_name="highlight")

