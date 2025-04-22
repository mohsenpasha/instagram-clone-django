from rest_framework import serializers
from .models import CustomUser, Post, PostMedia, PostLike, Comment, PostSave, Follower, CommentLike, Hashtag, Tagged, Story, Highlight, PostSave, SavedFolder
# import jdatetime
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import os
import cv2
from PIL import Image

class PostListSerializer(serializers.ModelSerializer):
	preview_image = serializers.SerializerMethodField()
	like_count = serializers.SerializerMethodField()
	comment_count = serializers.SerializerMethodField()
	class Meta:
		model = Post
		fields = ['id', 'caption', 'updated_at', 'is_pinned','preview_image','like_count','comment_count','disable_comments']
		depth = 1
	def get_preview_image(self, obj):
		first_media = obj.media.order_by("order").first()
		if first_media:
			if first_media.media_type == "image":
				return f"{settings.SITE_URL}{first_media.thumbnail.url}" if first_media.thumbnail else f"{settings.SITE_URL}{first_media.file.url}"
			elif first_media.media_type == "video" and first_media.thumbnail:
				return f"{settings.SITE_URL}{first_media.thumbnail.url}"
			return f"{settings.SITE_URL}{first_media.file.url}"
		return None

	def get_like_count(self,obj):
		return PostLike.objects.filter(post=obj).count()
	def get_comment_count(self,obj):
		return Comment.objects.filter(post=obj).count()

class UserSimpleSerializer(serializers.ModelSerializer):
	profile_pic = serializers.SerializerMethodField()
	name = serializers.SerializerMethodField()
	is_following = serializers.SerializerMethodField()
	class Meta:
		model = CustomUser
		fields = ['username','profile_pic','name','is_following']
		depth = 1
	def get_profile_pic(self,obj):
		try:
			return f"{settings.SITE_URL}{obj.img.url}"
		except:
			return None
	def get_name(self,obj):
			return obj.first_name + ' ' + obj.last_name
	def get_is_following(self,obj):
		try:
			request = self.context.get('request')
			req_username = request.user.username
		except:
			req_username = self.context.get("current_user")

		return Follower.objects.filter(follower__username=req_username,following__username=obj.username).exists()

class TaggedSerializer(serializers.ModelSerializer):
	user = UserSimpleSerializer('user')
	class Meta:
		model = Tagged
		fields = ['user', 'x', 'y']
		depth = 1
	# def get_user(self, obj):
		# return obj.user.username
class MediaSerializer(serializers.ModelSerializer):
	file = serializers.SerializerMethodField()
	tagged_users = TaggedSerializer('tagged_users',many=True)
	class Meta:
		model = PostMedia
		fields = ['file', 'media_type', 'order','tagged_users']
		depth = 1
	def get_file(self, obj):
		return f"{settings.SITE_URL}{obj.file.url}"


class MediaSerializer(serializers.ModelSerializer):
	file = serializers.SerializerMethodField()
	tagged_users = TaggedSerializer('tagged_users',many=True)
	class Meta:
		model = PostMedia
		fields = ['file', 'media_type', 'order','tagged_users']
		depth = 1
	def get_file(self, obj):
		return f"{settings.SITE_URL}{obj.file.url}"

class UserSerializer(serializers.ModelSerializer):
	profile_pic = serializers.SerializerMethodField()
	name = serializers.SerializerMethodField()
	is_following = serializers.SerializerMethodField()
	post_count = serializers.SerializerMethodField()
	following_count = serializers.SerializerMethodField()
	follower_count = serializers.SerializerMethodField()
	class Meta:
		model = CustomUser
		fields = ['username','profile_pic','name','is_following','follower_count','following_count','post_count','is_private']
		depth = 1
	def get_profile_pic(self,obj):
		try:
			return f"{settings.SITE_URL}{obj.img.url}"
		except:
			return None
	def get_name(self,obj):
			return obj.first_name + ' ' + obj.last_name
	def get_is_following(self,obj):
		request = self.context.get('request')
		return Follower.objects.filter(follower__username=request.user.username,following__username=obj.username).exists()
	def get_follower_count(self,obj):
		return len(Follower.objects.filter(following__username=obj.username))
	def get_following_count(self,obj):
		return len(Follower.objects.filter(follower__username=obj.username))
	def get_post_count(self,obj):
		return len(Post.objects.filter(user=obj))


class UserHoverSerializer(serializers.ModelSerializer):
	profile_pic = serializers.SerializerMethodField()
	name = serializers.SerializerMethodField()
	is_following = serializers.SerializerMethodField()
	post_count = serializers.SerializerMethodField()
	following_count = serializers.SerializerMethodField()
	follower_count = serializers.SerializerMethodField()
	recent_posts = serializers.SerializerMethodField()
	class Meta:
		model = CustomUser
		fields = ['username','profile_pic','name','is_following','follower_count','following_count','post_count','recent_posts','is_private']
		depth = 1
	def get_profile_pic(self,obj):
		try:
			return f"{settings.SITE_URL}{obj.img.url}"
		except:
			return None
	def get_name(self,obj):
			return obj.first_name + ' ' + obj.last_name
	def get_is_following(self,obj):
		request = self.context.get('request')
		return Follower.objects.filter(follower__username=request.user.username,following__username=obj.username).exists()
	def get_follower_count(self,obj):
		return len(Follower.objects.filter(following__username=obj.username))
	def get_following_count(self,obj):
		return len(Follower.objects.filter(follower__username=obj.username))
	def get_post_count(self,obj):
		return len(Post.objects.filter(user=obj))

	def get_recent_posts(self, obj):
		recent_posts = Post.objects.filter(user=obj).order_by('-created_at')[:3]
		return PostListSerializer(recent_posts, many=True, context=self.context).data

class PostSerializer(serializers.ModelSerializer):
	like_count = serializers.SerializerMethodField()
	comment_count = serializers.SerializerMethodField()
	is_liked = serializers.SerializerMethodField()
	is_saved = serializers.SerializerMethodField()
	updated_at = serializers.SerializerMethodField()
	preview_image = serializers.SerializerMethodField()
	media = MediaSerializer('media', many=True, read_only=True)
	user = UserSimpleSerializer('post.user')
	class Meta:
		model = Post
		fields = ['id','caption', 'updated_at', 'is_pinned','media','like_count','comment_count','disable_comments','user','is_liked','is_saved','preview_image']
		depth = 1
	def get_like_count(self, obj):
		return PostLike.objects.filter(post=obj).count()
	def get_comment_count(self, obj):
		return Comment.objects.filter(post=obj).count()
	def get_is_liked(self, obj):
		request = self.context.get('request')
		return PostLike.objects.filter(post=obj,user=request.user).exists()
	def get_is_saved(self, obj):
		request = self.context.get('request')
		return PostSave.objects.filter(post=obj,user=request.user).exists()
	def get_updated_at(self, obj):
		now = timezone.now()
		date = obj.updated_at
		delta = now - date
		if(delta.total_seconds() < 60):
			return {'t_ago':f"{int(delta.total_seconds())}", 't': 's'}
		elif(delta.total_seconds() / 60 < 60):
			return {'t_ago':f"{int(delta.total_seconds() / 60)}", 't': 'm'}
		elif(delta.total_seconds() / 60 / 60 < 24):
			return {'t_ago':f"{int(delta.total_seconds() / 60 / 60)}", 't': 'h'}
		elif delta < timedelta(days=7):
			return {'t_ago':f"{delta.days}", 't': 'd'}
		else:
			return {'t_ago':f"{int(delta.days / 7)}", 't': 'w'}
	def get_preview_image(self, obj):
		first_media = obj.media.order_by("order").first()
		if first_media:
			if first_media.media_type == "image":
				return f"{settings.SITE_URL}{first_media.thumbnail.url}" if first_media.thumbnail else f"{settings.SITE_URL}{first_media.file.url}"
			elif first_media.media_type == "video" and first_media.thumbnail:
				return f"{settings.SITE_URL}{first_media.thumbnail.url}"
			return f"{settings.SITE_URL}{first_media.file.url}"
		return None

class CommentSerializer(serializers.ModelSerializer):
	user = UserSimpleSerializer('comment.user',read_only=True)
	is_liked = serializers.SerializerMethodField()
	like_count = serializers.SerializerMethodField()
	reply_count = serializers.SerializerMethodField()
	updated_at = serializers.SerializerMethodField()
	class Meta:
		model = Comment
		fields = ['id','comment', 'user', 'updated_at','like_count','is_liked','reply_count']
		depth = 1
	def get_like_count(self, obj):
		return len(CommentLike.objects.filter(comment=obj))
	def get_is_liked(self, obj):
		request = self.context.get('request')
		return CommentLike.objects.filter(comment=obj,user=request.user).exists()

	def get_reply_count(self, obj):
		def count_all_replies(comment):
			replies = Comment.objects.filter(replied_to=comment)
			total = replies.count()
			for reply in replies:
				total += count_all_replies(reply)
			return total
		return count_all_replies(obj)

	def get_updated_at(self, obj):
		now = timezone.now()
		date = obj.updated_at
		delta = now - date
		if(delta.total_seconds() < 60):
			return {'t_ago':f"{int(delta.total_seconds())}", 't': 's'}
		elif(delta.total_seconds() / 60 < 60):
			return {'t_ago':f"{int(delta.total_seconds() / 60)}", 't': 'm'}
		elif(delta.total_seconds() / 60 / 60 < 24):
			return {'t_ago':f"{int(delta.total_seconds() / 60 / 60)}", 't': 'h'}
		elif delta < timedelta(days=7):
			return {'t_ago':f"{delta.days}", 't': 'd'}
		else:
			return {'t_ago':f"{int(delta.days / 7)}", 't': 'w'}
	def to_representation(self, instance):
		data = super().to_representation(instance)
		if data.get('like_count') == 0:
			data.pop('like_count')
		if data.get('reply_count') == 0:
			data.pop('reply_count')
		print(data.get('updated_at'))
		show_reply_count = self.context.get("show_reply_count", True)

		if not show_reply_count:
			data.pop("reply_count", None)
		return data

class SavedPostSerializer(serializers.ModelSerializer):
	post = serializers.SerializerMethodField()
	class Meta:
		model = PostSave
		fields = ['post']
		depth = 1
	def get_post(self, obj):
		request = self.context.get('request')
		return PostSerializer(obj.post,context={'request': request}).data


class SavedFolderSerializer(serializers.ModelSerializer):
	posts = serializers.SerializerMethodField()
	class Meta:
		model = SavedFolder
		fields = ['name','posts']
		depth = 1
	def get_posts(self, obj):
		return list(obj.saved_posts.values_list('post__id', flat=True))  


class HashtagSerializers(serializers.ModelSerializer):
	tag = serializers.SerializerMethodField()
	post_count = serializers.SerializerMethodField()
	class Meta:
		model = Hashtag
		fields = ['tag','post_count']
		depth = 1
	def get_tag(self, obj):
		return obj.name
	def get_post_count(self, obj):
		return obj.posts.count()

class StorySerializers(serializers.ModelSerializer):
	created_at = serializers.SerializerMethodField()
	file = serializers.SerializerMethodField()
	class Meta:
		model = Story
		fields = ['file','media_type','created_at']
		depth = 1
	def get_file(self, obj):
		return settings.SITE_URL + obj.file.url
	def get_created_at(self, obj):
		now = timezone.now()
		date = obj.updated_at
		delta = now - date
		if(delta.total_seconds() < 60):
			return {'t_ago':f"{int(delta.total_seconds())}", 't': 's'}
		elif(delta.total_seconds() / 60 < 60):
			return {'t_ago':f"{int(delta.total_seconds() / 60)}", 't': 'm'}
		elif(delta.total_seconds() / 60 / 60 < 24):
			return {'t_ago':f"{int(delta.total_seconds() / 60 / 60)}", 't': 'h'}
		elif delta < timedelta(days=7):
			return {'t_ago':f"{delta.days}", 't': 'd'}
		else:
			return {'t_ago':f"{int(delta.days / 7)}", 't': 'w'}


# class HomeStorySerializer(serializers.ModelSerializer):
#     stories = serializers.SerializerMethodField()
#     username = serializers.CharField(source='user.username')
#     profile_image = serializers.SerializerMethodField()

#     class Meta:
#         model = CustomUser
#         fields = ['username', 'profile_image', 'stories']

#     def get_profile_image(self, obj):
#         profile = getattr(obj.user, 'profile', None)
#         if profile and profile.image:
#             return settings.SITE_URL + profile.image.url
#         return None

#     def get_stories(self, obj):
#         user_stories = self.context.get('user_stories', {}).get(obj.user.id, [])
#         return StorySerializers(user_stories, many=True).data

class HomeStorySerializer(serializers.ModelSerializer):
    stories = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['name', 'thumbnail', 'stories']

    def get_thumbnail(self, obj):
        if obj.img:
            return settings.SITE_URL + obj.img.url
        return None
    def get_name(self, obj):
    	if(obj.username):
	    	return obj.username


    def get_stories(self, obj):
        # فقط استوری‌های ۲۴ ساعت اخیر این کاربر
        time_threshold = timezone.now() - timedelta(days=1)
        stories = obj.story_set.filter(created_at__gte=time_threshold).order_by('-created_at')
        return StorySerializers(stories, many=True).data
class HighlightSerializers(serializers.ModelSerializer):
    thumbnail = serializers.SerializerMethodField()
    stories = StorySerializers('stories',many=True)

    class Meta:
        model = Highlight
        fields = ['name', 'stories', 'thumbnail']

    def get_thumbnail(self, obj):
        first_story = obj.stories.first()
        if not first_story:
            return None
        
        media_path = os.path.join(settings.MEDIA_ROOT, first_story.file.name)
        thumb_path = os.path.join('stories/thumbnails', f"{first_story.pk}_thumb.jpg")
        full_thumb_path = os.path.join(settings.MEDIA_ROOT, thumb_path)

        if not os.path.exists(full_thumb_path):
            os.makedirs(os.path.dirname(full_thumb_path), exist_ok=True)

            if first_story.media_type == 'image':
                try:
                    with Image.open(media_path) as img:
                        img.save(full_thumb_path, "JPEG")
                        img.thumbnail((160, 160))
                except Exception as e:
                    print("Image thumbnail error:", e)
                    return None

            elif first_story.media_type == 'video':
                try:
                    cap = cv2.VideoCapture(media_path)
                    success, frame = cap.read()
                    if success:
                        frame = cv2.resize(frame, (160, 160))
                        cv2.imwrite(full_thumb_path, frame)
                    cap.release()
                except Exception as e:
                    print("Video thumbnail error:", e)
                    return None

        return os.path.join(settings.SITE_URL+settings.MEDIA_URL, thumb_path)
# class BranchSerializer(serializers.ModelSerializer):
# 	image_url = serializers.SerializerMethodField()
# 	class Meta:
# 		model = branch
# 		fields = ['id', 'name', 'location', 'address', 'number','image_url','slug']
        
# 	def get_image_url(self, obj):
# 		return obj.get_absolute_url()

# class FoodSerializer(serializers.ModelSerializer):
# 	image_url = serializers.SerializerMethodField()

# 	class Meta:
# 		model = food
# 		fields = ['id', 'name', 'point', 'point_count', 'content','image_url','price','discount','category','branch']

# 	def get_image_url(self, obj):
# 		return obj.get_absolute_url()


# class FoodCategorySerializer(serializers.ModelSerializer):

# 	class Meta:
# 		model = foodCategory
# 		fields = ['id', 'name']

# class CommentSerializer(serializers.ModelSerializer):
# 	user = ProfileSerializer()
# 	created_at_shamsi = serializers.SerializerMethodField()

# 	class Meta:
# 		model = branchComment
# 		fields = ['id', 'user', 'created_at_shamsi', 'comment', 'point']

# 	def get_created_at_shamsi(self, obj):
# 		if obj.date:
# 			shamsi_date = jdatetime.datetime.fromgregorian(datetime=obj.date)
# 			months = {
# 			    "Farvardin": "فروردین",
# 			    "Ordibehesht": "اردیبهشت",
# 			    "Khordad": "خرداد",
# 			    "Tir": "تیر",
# 			    "Mordad": "مرداد",
# 			    "Shahrivar": "شهریور",
# 			    "Mehr": "مهر",
# 			    "Aban": "آبان",
# 			    "Azar": "آذر",
# 			    "Dey": "دی",
# 			    "Bahman": "بهمن",
# 			    "Esfand": "اسفند"
# 			}
# 			return f"{shamsi_date.day} {months[shamsi_date.strftime('%B')]} {shamsi_date.year}"
# 		return None

# class AddressSerializer(serializers.ModelSerializer):
# 	class Meta:
# 		model = address
# 		fields = ['id', 'title','name','phone_number','address']


# class CouponSerializer(serializers.ModelSerializer):
# 	class Meta:
# 		model = coupon
# 		fields = ['id', 'code','discount']


# class orderSerializer(serializers.ModelSerializer):
# 	food = FoodSerializer()
# 	class Meta:
# 		model = order
# 		fields = ['food','count']

# class OrderListSerializer(serializers.ModelSerializer):
# 	created_at_shamsi = serializers.SerializerMethodField()

# 	def get_created_at_shamsi(self, obj):
# 	    if obj.data_time:
# 	        shamsi_date = jdatetime.datetime.fromgregorian(datetime=obj.data_time)
# 	        months = {
# 	            "Farvardin": "فروردین",
# 	            "Ordibehesht": "اردیبهشت",
# 	            "Khordad": "خرداد",
# 	            "Tir": "تیر",
# 	            "Mordad": "مرداد",
# 	            "Shahrivar": "شهریور",
# 	            "Mehr": "مهر",
# 	            "Aban": "آبان",
# 	            "Azar": "آذر",
# 	            "Dey": "دی",
# 	            "Bahman": "بهمن",
# 	            "Esfand": "اسفند"
# 	        }
# 	        date_part = f"{shamsi_date.day} {months[shamsi_date.strftime('%B')]} {shamsi_date.year}"
# 	        time_part = f"ساعت {shamsi_date.hour:02}:{shamsi_date.minute:02}"
# 	        return f"{date_part} - {time_part}"
# 	    return None
# 	address = AddressSerializer()
# 	order_list = orderSerializer(many=True)
# 	class Meta:
# 		model = orderList
# 		fields = ['id', 'status','created_at_shamsi','address','shiping_way','discount','order_list']