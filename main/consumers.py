import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'instagramClone.settings')
django.setup()

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import json
from .models import Notification, Comment, Post
from . import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

class MyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if self.user.is_anonymous:
            await self.close()
            return

        await self.accept()

        await self.channel_layer.group_add(
            f"user_{self.user.id}",
            self.channel_name
        )

        notifications = await self.get_user_notifications()
        await self.send(text_data=json.dumps({
            'type': 'notification_history',
            'notifications': notifications
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            f"user_{self.user.id}",
            self.channel_name
        )

    async def notify(self, event):
        sender = event['sender']
        sender_data = await self.get_serialized_user(sender)

        timestamp = await self.get_updated_at(event['id'])

        notification_data = {
            "id": event.get('id'),
            "message": event['message'],
            "type": event['notif_type'],
            "timestamp": timestamp,
            "sender": sender_data,
            "is_read": False
        }

        if event['notif_type'] == 'comment':
            comment_id = event['object_id']
            comment = await self.get_comment_object(comment_id)
            if comment:
                notification_data['comment_text'] = comment.comment
                post_data = await self.get_post_data(comment.post.id)
                if post_data:
                    notification_data['post'] = post_data

        elif event['notif_type'] == 'like':
            post_data = await self.get_post_data(event['object_id'])
            if post_data:
                notification_data["post"] = post_data

        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': notification_data
        }))

    @database_sync_to_async
    def get_comment_object(self, comment_id):
        try:
            return Comment.objects.select_related('post').get(pk=comment_id)
        except Comment.DoesNotExist:
            return None

    @database_sync_to_async
    def get_post_data(self, post_id):
        try:
            post = Post.objects.get(id=post_id)
            first_media = post.media.order_by("order").first()
            if first_media:
                if first_media.media_type == "image":
                    preview_image = (
                        f"{settings.SITE_URL}{first_media.thumbnail.url}"
                        if first_media.thumbnail else
                        f"{settings.SITE_URL}{first_media.file.url}"
                    )
                elif first_media.media_type == "video" and first_media.thumbnail:
                    preview_image = f"{settings.SITE_URL}{first_media.thumbnail.url}"
                else:
                    preview_image = f"{settings.SITE_URL}{first_media.file.url}"
            else:
                preview_image = None

            return {
                "id": post.id,
                "preview_image": preview_image
            }
        except Post.DoesNotExist:
            return None

    @database_sync_to_async
    def get_user_notifications(self):
        notifications = Notification.objects.filter(
            recipient=self.user
        ).select_related('sender').order_by('-timestamp')[:20]

        result = []
        now = timezone.now()

        for n in notifications:
            sender = n.sender
            is_following = models.Follower.objects.filter(
                follower=self.user,
                following=sender
            ).exists()

            timestamp = self.format_time_ago(now, n.timestamp)

            notif_data = {
                "id": n.id,
                "message": n.message,
                "type": n.type,
                "timestamp": timestamp,
                "is_read": n.is_read,
                "sender": {
                    "id": sender.id,
                    "username": sender.username,
                    "profile_pic": settings.SITE_URL + sender.img.url if sender.img else None,
                    "is_following": is_following,
                }
            }

            if n.type == 'comment' and isinstance(n.content_object, Comment):
                comment = n.content_object
                notif_data['comment_text'] = comment.comment
                post = comment.post

                first_media = post.media.order_by("order").first()
                if first_media:
                    if first_media.media_type == "image":
                        preview_image = (
                            f"{settings.SITE_URL}{first_media.thumbnail.url}"
                            if first_media.thumbnail else
                            f"{settings.SITE_URL}{first_media.file.url}"
                        )
                    elif first_media.media_type == "video" and first_media.thumbnail:
                        preview_image = f"{settings.SITE_URL}{first_media.thumbnail.url}"
                    else:
                        preview_image = f"{settings.SITE_URL}{first_media.file.url}"
                else:
                    preview_image = None

                notif_data["post"] = {
                    "id": post.id,
                    "preview_image": preview_image
                }

            elif n.type == 'like' and hasattr(n.content_object, 'media'):
                post = n.content_object
                first_media = post.media.order_by("order").first()
                if first_media:
                    if first_media.media_type == "image":
                        preview_image = (
                            f"{settings.SITE_URL}{first_media.thumbnail.url}"
                            if first_media.thumbnail else
                            f"{settings.SITE_URL}{first_media.file.url}"
                        )
                    elif first_media.media_type == "video" and first_media.thumbnail:
                        preview_image = f"{settings.SITE_URL}{first_media.thumbnail.url}"
                    else:
                        preview_image = f"{settings.SITE_URL}{first_media.file.url}"
                else:
                    preview_image = None

                notif_data["post"] = {
                    "id": post.id,
                    "preview_image": preview_image
                }

            result.append(notif_data)
        return result

    async def get_serialized_user(self, user):
        is_following = await self.is_following(self.user, user)
        return {
            "id": user.id,
            "username": user.username,
            "profile_pic": settings.SITE_URL + user.img.url if user.img else None,
            "is_following": is_following,
        }

    @database_sync_to_async
    def is_following(self, current_user, target_user):
        return models.Follower.objects.filter(
            follower=current_user,
            following=target_user
        ).exists()

    @database_sync_to_async
    def get_updated_at(self, notif_id):
        try:
            obj = Notification.objects.get(id=notif_id)
            return self.format_time_ago(timezone.now(), obj.timestamp)
        except Notification.DoesNotExist:
            return None

    def format_time_ago(self, now, date):
        delta = now - date
        if delta.total_seconds() < 60:
            return {'t_ago': f"{int(delta.total_seconds())}", 't': 's'}
        elif delta.total_seconds() / 60 < 60:
            return {'t_ago': f"{int(delta.total_seconds() / 60)}", 't': 'm'}
        elif delta.total_seconds() / 60 / 60 < 24:
            return {'t_ago': f"{int(delta.total_seconds() / 60 / 60)}", 't': 'h'}
        elif delta < timedelta(days=7):
            return {'t_ago': f"{delta.days}", 't': 'd'}
        else:
            return {'t_ago': f"{int(delta.days / 7)}", 't': 'w'}
