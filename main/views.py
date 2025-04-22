from django.shortcuts import render
from django.contrib.auth import authenticate, login
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.pagination import LimitOffsetPagination
from django.conf import settings

from .authentication import CookieJWTAuthentication
from .serializers import PostListSerializer, PostSerializer, UserSimpleSerializer, UserHoverSerializer, UserSerializer, CommentSerializer, HashtagSerializers, StorySerializers, HighlightSerializers, HomeStorySerializer, SavedPostSerializer, SavedFolderSerializer
from django.middleware.csrf import get_token

from . import models
import time
import json
from django.contrib.contenttypes.models import ContentType
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db.models import Count, Q
import base64
import uuid
from django.core.files.base import ContentFile
from django.utils import timezone
from datetime import timedelta
from random import sample


def handle_data_url(data_url):
    format, imgstr = data_url.split(';base64,')  # جدا کردن متادیتا از دیتا
    ext = format.split('/')[-1]  # گرفتن پسوند فایل (مثل png)
    file_name = f"{uuid.uuid4()}.{ext}"  # تولید اسم یونیک برای فایل
    return ContentFile(base64.b64decode(imgstr), name=file_name)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)
        login(request,user)
        if user is not None:
            refresh = RefreshToken.for_user(user)
            response = Response({
                "message": "Login successful"
            })

            response.set_cookie(
                key="access_token",
                value=str(refresh.access_token),
                httponly=True,
                samesite="Lax",
                secure=False
            )
            response.set_cookie(
                "csrftoken", get_token(request), 
                httponly=False,
                secure=False,
                samesite="Lax"
            )
            response.set_cookie(
                key="refresh_token",
                value=str(refresh),
                httponly=True,
                samesite="Lax",
                secure=False
            )

            return response
        return Response({"error": "Invalid credentials"}, status=400)


class ProtectedView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response({"message": "You are authenticated"})


class LogoutView(APIView):
    def post(self, request):
        response = Response({"message": "Logged out"})
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response

class AddPost(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request):
        time.sleep(1)
        user = request.user
        caption = request.data.get("caption") or ""
        postMediaData = request.data.get("post_media")
        try:
            postMedia = json.loads(postMediaData)
        except:
            postMedia = postMediaData
        location = request.data.get("location")
        commentDisabled = request.data.get("comment_disabled") or False
        hideView = request.data.get("view_hide") or False
        newpost = models.Post.objects.create(user=user,caption=caption,location=location,disable_comments=commentDisabled)
        try:
            hashtags = request.data.get('hashtags')
        except Exception as ex:
            print(ex)
            hashtags = []
        for i in hashtags:
            try:
                hashtag = models.Hashtag.objects.get(name=i)
            except:
                hashtag = models.Hashtag.objects.create(name=i)
            newpost.hashtags.add(hashtag.pk)

        for media in postMedia:
            image_file = handle_data_url(media['croppedDataURL'])
            newMedia = models.PostMedia.objects.create(post=newpost,file=image_file,media_type="image")
            if media.get("tagged_user") is not None:
                for tagged in media['tagged_user']:
                    username = tagged['username']
                    user = models.CustomUser.objects.get(username=username)
                    coordinates = tagged['coordinates']
                    newTag = models.Tagged.objects.create(user=user,x=coordinates['x'],y=coordinates['y'])
                    newMedia.tagged_users.add(newTag.pk)
                    print(username,coordinates)
        #     return Response({"message": "The post was successfully liked."}, status=200)
        return Response({"message": "The post was successfully added."}, status=200)



class UserPosts(APIView):
    class Pagination(LimitOffsetPagination):
        default_limit = 12
        max_limit = 100

    def get(self, request, username):
        posts = models.Post.objects.filter(user__username=username).order_by('-created_at')
        paginator = self.Pagination()
        paginated_posts = paginator.paginate_queryset(posts, request)
        serializer = PostListSerializer(paginated_posts,many=True)
        return paginator.get_paginated_response(serializer.data)

class UserStories(APIView):
    time_threshold = timezone.now() - timedelta(days=1)
    def get(self, request, username):
        time_threshold = timezone.now() - timedelta(days=1)
        stories = models.Story.objects.filter(user__username=username,created_at__gte=time_threshold).order_by('-created_at')
        serializer = StorySerializers(stories,many=True)
        # serializer = PostListSerializer(paginated_posts,many=True)
        return Response(serializer.data)

class HomeStories(APIView):
    time_threshold = timezone.now() - timedelta(days=1)
    def get(self, request):
        user = request.user
        time_threshold = timezone.now() - timedelta(days=1)
        # stories = models.Story.objects.filter(user__id__in=userFollowers,created_at__gte=time_threshold).order_by('-created_at')
        following_ids = models.Follower.objects.filter(follower=user).values_list('following', flat=True)
        user_ids = list(following_ids)
        users_with_stories = models.CustomUser.objects.filter(
            id__in=user_ids,
            story__created_at__gte=time_threshold
        ).distinct()
        serializer = HomeStorySerializer(users_with_stories,many=True)
        # serializer = PostListSerializer(paginated_posts,many=True)
        return Response(serializer.data)


class UserHighlights(APIView):
    time_threshold = timezone.now() - timedelta(days=1)
    def get(self, request, username):
        time_threshold = timezone.now() - timedelta(days=1)
        stories = models.Highlight.objects.filter(user__username=username).order_by('-created_at')
        serializer = HighlightSerializers(stories,many=True)
        # serializer = PostListSerializer(paginated_posts,many=True)
        return Response(serializer.data)

class UserReels(APIView):
    class Pagination(LimitOffsetPagination):
        default_limit = 12
        max_limit = 100
    def get(self, request, username):
        user = models.CustomUser.objects.get(username=username)
        posts = models.Post.objects.annotate(
            media_count=Count('media')
        ).filter(
            media_count=1,
            media__media_type='video',
            user=user
        ).distinct()
        paginator = self.Pagination()
        paginated_posts = paginator.paginate_queryset(posts, request)
        serializer = PostListSerializer(paginated_posts,many=True)
        return paginator.get_paginated_response(serializer.data)


class GetReels(APIView):
    class Pagination(LimitOffsetPagination):
        default_limit = 12
        max_limit = 100
    def get(self, request):
        posts = models.Post.objects.annotate(
            media_count=Count('media')
        ).filter(
            media_count=1,
            media__media_type='video'
        ).order_by('?').distinct()
        paginator = self.Pagination()
        paginated_posts = paginator.paginate_queryset(posts, request)
        serializer = PostSerializer(paginated_posts,many=True,context={'request': request})
        return paginator.get_paginated_response(serializer.data)

class HastagPosts(APIView):
    class Pagination(LimitOffsetPagination):
        default_limit = 12
        max_limit = 100

    def get(self, request, hashtag):
        time.sleep(1)
        hastag = models.Hashtag.objects.get(name=hashtag)
        posts = hastag.posts.all()
        paginator = self.Pagination()
        paginated_posts = paginator.paginate_queryset(posts, request)
        serializer = PostListSerializer(paginated_posts,many=True)
        return paginator.get_paginated_response(serializer.data)

class GetTaggedPosts(APIView):
    class Pagination(LimitOffsetPagination):
        default_limit = 12
        max_limit = 100

    def get(self, request, username):
        user = models.CustomUser.objects.get(username=username)
        posts = models.Post.objects.filter(media__tagged_users__user=user).distinct().order_by('-created_at')
        print(posts)
        paginator = self.Pagination()
        paginated_posts = paginator.paginate_queryset(posts, request)
        serializer = PostListSerializer(paginated_posts,many=True)
        return paginator.get_paginated_response(serializer.data)



class GetPost(APIView):
    def get(self, request, postId):
        post = models.Post.objects.get(pk=postId)
        serializer = PostSerializer(post,context={'request': request})
        return Response(serializer.data)


def get_preview_image(post):
    first_media = post.media.order_by("order").first()
    if first_media:
        if first_media.media_type == "image":
            return f"{settings.SITE_URL}{first_media.thumbnail.url}" if first_media.thumbnail else f"{settings.SITE_URL}{first_media.file.url}"
        elif first_media.media_type == "video" and first_media.thumbnail:
            return f"{settings.SITE_URL}{first_media.thumbnail.url}"
        return f"{settings.SITE_URL}{first_media.file.url}"
    return None

class GetFirstFewPost(APIView):
    def get(self, request, postId):
        post = models.Post.objects.get(pk=postId)
        latest_posts = models.Post.objects.filter(user=post.user).exclude(id=postId).order_by('-created_at')[:6]
        serializer = PostListSerializer(latest_posts,many=True,context={'request': request})
        return Response(serializer.data)


class LikePost(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request, postId):
        postLike = models.PostLike.objects.filter(post=postId,user=request.user).exists()
        if(postLike):
            return Response({"error": "The post has already been liked."}, status=400)
        else:
            post = models.Post.objects.get(pk=postId)
            newPostLike = models.PostLike.objects.create(user=request.user,post=post)
            preview_image = get_preview_image(post)
            notif = models.Notification.objects.create(
                sender=request.user,
                recipient=post.user,
                type='like',
                message=f"{request.user.username} پست شما را لایک کرد",
                content_type=ContentType.objects.get_for_model(post),
                object_id=post.id
            )

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"user_{post.user.id}",
                {
                    "type": "notify",
                    "message": notif.message,
                    "notif_type": notif.type,
                    "object_id": notif.object_id,
                    "object_type": notif.content_type.model,
                    "sender": notif.sender,
                    "id": notif.id,
                    "timestamp": str(notif.timestamp),
                    "preview_image": preview_image  # 👈 اضافه شد
                }
            )
            return Response({"message": "The post was successfully liked."}, status=200)

class UnlikePost(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request, postId):
        postLike = models.PostLike.objects.filter(post=postId,user=request.user)
        if(postLike.exists()):
            postLike.delete()
            return Response({"message": "The post was successfully unliked."}, status=200)
        else:
            return Response({"error": "The post has not been liked yet."}, status=400)



class SavePost(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request, postId):
        postsave = models.PostSave.objects.filter(post=postId,user=request.user).exists()
        if(postsave):
            return Response({"error": "The post has already been saved."}, status=400)
        else:
            post = models.Post.objects.get(pk=postId)
            newPostSave = models.PostSave.objects.create(user=request.user,post=post)
            return Response({"message": "The post was successfully saved."}, status=200)

class UnsavePost(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request, postId):
        postLike = models.PostSave.objects.filter(post=postId,user=request.user)
        if(postLike.exists()):
            postLike.delete()
            return Response({"message": "The post was successfully unsaved."}, status=200)
        else:
            return Response({"error": "The post has not been saved yet."}, status=400)


class GetSavedPosts(APIView):
    def get(self, request):
        user = request.user
        savedPosts = models.PostSave.objects.filter(user=user)
        savedFolder = models.SavedFolder.objects.filter(user=user)
        # latest_posts = models.Post.objects.filter(user=post.user).exclude(id=postId).order_by('-created_at')[:6]
        serializer = SavedPostSerializer(savedPosts,many=True,context={'request': request})
        folderSerializer = SavedFolderSerializer(savedFolder,many=True)
        return Response({'posts':serializer.data,'folders':folderSerializer.data})

class AddSavedFolder(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request):
        print(request.data)
        folderName = request.data.get("folder_name")
        posts = request.data.get("post_list")
        print(folderName)
        print(posts)
        user = request.user
        try:
            newSavedFolder = models.SavedFolder.objects.get(name=folderName)
        except:
            newSavedFolder = models.SavedFolder.objects.create(user=user,name=folderName)
        for postId in posts:
            post_save = models.PostSave.objects.get(user=user, post__id=postId)
            newSavedFolder.saved_posts.add(post_save.pk)
        folderSerializer = SavedFolderSerializer(newSavedFolder)
        return Response(folderSerializer.data, status=200)


class GetPostLikes(APIView):
    class Pagination(LimitOffsetPagination):
        default_limit = 12
        max_limit = 100

    def get(self, request, postId):
        postLikes = models.PostLike.objects.filter(post=postId).order_by('-created_at')
        paginator = self.Pagination()
        paginated_likes = paginator.paginate_queryset(postLikes, request)
        users = [like.user for like in paginated_likes] 
        serializer = UserSimpleSerializer(users,many=True,context={'request': request})
        return paginator.get_paginated_response(serializer.data)

class GetUserFollowers(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    class Pagination(LimitOffsetPagination):
        default_limit = 12
        max_limit = 100

    def get(self, request, username):
        user = models.CustomUser.objects.get(username=username)
        userFollowers = models.Follower.objects.filter(following=user)
        paginator = self.Pagination()
        paginated_followers = paginator.paginate_queryset(userFollowers, request)
        users = [item.follower for item in paginated_followers]
        serializer = UserSimpleSerializer(users,many=True,context={'request': request})
        return paginator.get_paginated_response(serializer.data)

class GetUserFollowing(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    class Pagination(LimitOffsetPagination):
        default_limit = 12
        max_limit = 100

    def get(self, request, username):
        user = models.CustomUser.objects.get(username=username)
        userFollowers = models.Follower.objects.filter(follower=user)
        paginator = self.Pagination()
        paginated_followers = paginator.paginate_queryset(userFollowers, request)
        users = [item.following for item in paginated_followers]
        serializer = UserSimpleSerializer(users,many=True,context={'request': request})
        return paginator.get_paginated_response(serializer.data)

class AddPostComment(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        post_id = request.data.get('postId', None)
        comment_text = request.data.get('comment')

        try:
            replied_to = models.Comment.objects.get(pk=request.data.get('replied_to'))
        except:
            replied_to = None

        try:
            post = models.Post.objects.get(pk=post_id)
        except:
            return Response({"message": "there ain't no such post boy"}, status=400)

        new_comment = models.Comment.objects.create(
            post=post,
            comment=comment_text,
            user=request.user,
            replied_to=replied_to
        )

        serializer = CommentSerializer(new_comment, context={'request': request})

        # ✅ فقط نوتیف بساز اگه یوزر خودت نبودی
        if post.user != request.user:
            if len(comment_text) < 90:
                notif = models.Notification.objects.create(
                    recipient=post.user,
                    sender=request.user,
                    type='comment',
                    message=f'{request.user.username} commented on your post.',
                    content_type=ContentType.objects.get_for_model(new_comment),  # 🔁 اینجا comment رو ست کن
                    object_id=new_comment.id  # 🔁 آیدی کامنت رو ست کن
                )

                # ارسال از طریق سوکت
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f"user_{post.user.id}",
                    {
                        "type": "notify",
                        "id": notif.id,
                        "notif_type": notif.type,
                        "message": notif.message,
                        "sender": request.user,
                        "object_id": new_comment.id,
                        'comment_text': new_comment.comment,

                    }
                )
        return Response(serializer.data, status=200)
class GetPostComments(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    class Pagination(LimitOffsetPagination):
        default_limit = 5
        max_limit = 100

    def get(self, request, postId):
        time.sleep(1)
        post = models.Post.objects.get(pk=postId)
        comments = models.Comment.objects.filter(post=post,replied_to__isnull=True)
        paginator = self.Pagination()
        paginated_comments = paginator.paginate_queryset(comments, request)
        serializer = CommentSerializer(paginated_comments,many=True,context={'request': request})
        return paginator.get_paginated_response(serializer.data)



class GetCommentReplies(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    class Pagination(LimitOffsetPagination):
        default_limit = 3
        max_limit = 100

    def get_replies_recursive(self, comment, request):
        replies = comment.replies.all()
        serialized_replies = CommentSerializer(replies, many=True, context={'request': request, 'show_reply_count': False}).data
        for reply, serialized_reply in zip(replies, serialized_replies):
            print(len(self.get_replies_recursive(reply, request)))
            if(len(self.get_replies_recursive(reply, request)) != 0):
                serialized_reply["replies"] = self.get_replies_recursive(reply, request)
        return serialized_replies

    def get(self, request, commentId):
        time.sleep(1)
        try:
            comment = models.Comment.objects.get(pk=commentId)
        except models.Comment.DoesNotExist:
            return Response({"error": "کامنت مورد نظر یافت نشد."}, status=404)

        replies = models.Comment.objects.filter(replied_to=comment)

        paginator = self.Pagination()
        paginated_replies = paginator.paginate_queryset(replies, request)
        serialized_replies = CommentSerializer(paginated_replies, many=True, context={'request': request, 'show_reply_count': False}).data

        for reply, serialized_reply in zip(paginated_replies, serialized_replies):
            serialized_reply["replies"] = self.get_replies_recursive(reply, request)

        return paginator.get_paginated_response(serialized_replies)

class LikeComment(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request, commentId):
        commentLike = models.CommentLike.objects.filter(comment=commentId,user=request.user).exists()
        if(commentLike):
            return Response({"error": "The comment has already been liked."}, status=400)
        else:
            comment = models.Comment.objects.get(pk=commentId)
            models.CommentLike.objects.create(user=request.user,comment=comment)
            return Response({"message": "The comment was successfully liked."}, status=200)

class UnlikeComment(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request, commentId):
        commentLike = models.CommentLike.objects.filter(comment=commentId,user=request.user)
        if(commentLike.exists()):
            commentLike.delete()
            return Response({"message": "The comment was successfully unliked."}, status=200)
        else:
            return Response({"error": "The comment has not been liked yet."}, status=400)


class GetCommentLikes(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    class Pagination(LimitOffsetPagination):
        default_limit = 12
        max_limit = 100

    def get(self, request, commentId):
        comment = models.Comment.objects.get(pk=commentId)
        comment_like = models.CommentLike.objects.filter(comment=comment)
        paginator = self.Pagination()
        paginated_comment_likes = paginator.paginate_queryset(comment_like, request)
        users = [item.user for item in paginated_comment_likes]
        serializer = UserSimpleSerializer(users,many=True,context={'request': request})
        print('serializer.data')
        print(serializer.data)
        return paginator.get_paginated_response(serializer.data)


class FollowUser(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request, username):
        time.sleep(1)
        if(username == request.user.username):
            return Response({"error": "sorry you can't follow yourself"}, status=400)
        is_following = models.Follower.objects.filter(follower__username=request.user.username,following__username=username).exists()
        if(is_following):
            return Response({"error": "The user has already been followed."}, status=400)
        else:
            user = models.CustomUser.objects.get(username=username)
            newFollower = models.Follower.objects.create(follower=request.user,following=user)
            notif = models.Notification.objects.create(
                sender=request.user,
                recipient=user,
                type='follow',
                message=f"{request.user.username} شما را فالو کرد",
                content_type=ContentType.objects.get_for_model(user),
                object_id=user.id
            )

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"user_{user.id}",
                {
                    "type": "notify",
                    "id": notif.id,
                    "message": notif.message,
                    "notif_type": notif.type,
                    "timestamp": str(notif.timestamp),
                    "object_id": notif.object_id,
                    "object_type": notif.content_type.model,
                    "sender": notif.sender  # این همون یوزره که توی کانسومر سریالایز می‌کنی
                }
            )
            return Response({"message": "The user was successfully followed."}, status=200)

class UnfollowUser(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request, username):
        time.sleep(1)
        if(username == request.user.username):
            return Response({"error": "sorry you can't unfollow yourself"}, status=400)
        is_following = models.Follower.objects.filter(follower__username=request.user.username,following__username=username)
        if(is_following.exists()):
            is_following.delete()
            return Response({"message": "The user was successfully unfollowed."}, status=200)
        else:
            return Response({"error": "The user is not in your following list."}, status=400)


class GetUserHoverPreview(APIView):
    def get(self, request, username):
        user = models.CustomUser.objects.get(username=username)
        serializer = UserHoverSerializer(user,context={'request': request})
        return Response(serializer.data)

class GetUserInfo(APIView):
    def get(self, request, username):
        user = models.CustomUser.objects.get(username=username)
        serializer = UserSerializer(user,context={'request': request})
        return Response(serializer.data)


class SearchUsersAndTags(APIView):
    authentication_classes = [CookieJWTAuthentication]
    # permission_classes = [IsAuthenticated]
    def post(self, request,searchType):
        time.sleep(1)
        searchInput = request.data.get('s',None)
        if(searchType == 'user'):
            result = models.CustomUser.objects.filter(username__icontains=searchInput)[:5]
            serializer = UserSimpleSerializer(result,many=True,context={'request': request})
        else:
            result = models.Hashtag.objects.filter(name__icontains=searchInput)[:5]
            serializer = HashtagSerializers(result,many=True)

            print('test')

        return Response(serializer.data, status=200)


class MarkNotificationsAsRead(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        notifications = models.Notification.objects.filter(recipient=request.user, is_read=False)
        
        if not notifications.exists():
            return Response({"message": "No unread notifications found."}, status=404)

        # تغییر وضعیت به خوانده شده
        notifications.update(is_read=True)

        return Response({"message": "All notifications marked as read."}, status=200)


class FeedPosts(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        following_users = models.CustomUser.objects.filter(followers__follower=user)
        posts = models.Post.objects.filter(user__in=following_users).order_by('-created_at')

        serializer = PostSerializer(posts, many=True,context={'request': request})
        return Response(serializer.data)


class SuggestedUsersAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # همه‌ی یوزرهایی که فالو نکردی و خودت نیستی
        following_ids = models.Follower.objects.filter(follower=user).values_list('following_id', flat=True)
        not_followed_users = models.CustomUser.objects.exclude(id__in=following_ids).exclude(id=user.id)

        # انتخاب رندوم تا 10 نفر
        users_list = list(not_followed_users)
        random_users = sample(users_list, min(len(users_list), 10))

        serializer = UserSimpleSerializer(random_users, many=True)
        return Response(serializer.data)