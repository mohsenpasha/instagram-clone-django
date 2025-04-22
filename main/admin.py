from django.contrib import admin
from . import models
# Register your models here.
admin.site.register(models.CustomUser)

admin.site.register(models.Hashtag)
admin.site.register(models.Post)
admin.site.register(models.PostSave)
admin.site.register(models.SavedFolder)
admin.site.register(models.Story)
admin.site.register(models.Highlight)
admin.site.register(models.PostMedia)
admin.site.register(models.Comment)
admin.site.register(models.CommentLike)
admin.site.register(models.PostLike)
admin.site.register(models.Follower)
admin.site.register(models.Notification)
admin.site.register(models.Tagged)

