from django.urls import path
from .views import LoginView, LogoutView, ProtectedView, UserPosts,GetPost, LikePost,UnlikePost, SavePost, UnsavePost,GetPostLikes,FollowUser, UnfollowUser, GetUserHoverPreview, GetUserInfo, GetUserFollowers, GetUserFollowing, GetPostComments, GetCommentLikes, LikeComment, UnlikeComment, GetCommentReplies, AddPostComment, SearchUsersAndTags, MarkNotificationsAsRead, GetFirstFewPost, HastagPosts, GetTaggedPosts, UserReels, GetReels, AddPost, UserStories, UserHighlights, HomeStories, FeedPosts, SuggestedUsersAPIView, GetSavedPosts, AddSavedFolder
from rest_framework_simplejwt.views import TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("protected/", ProtectedView.as_view(), name="protected"),
    path("<str:username>/posts/",UserPosts.as_view() , name="userPosts"),
    path("getpost/<str:postId>",GetPost.as_view() , name="getPost"),
    path("like/<str:postId>/",LikePost.as_view() , name="likePost"),
    path("unlike/<str:postId>/",UnlikePost.as_view() , name="unlikePost"),
    path("save/<str:postId>/",SavePost.as_view() , name="savePost"),
    path("unsave/<str:postId>/",UnsavePost.as_view() , name="unsavePost"),
    path("getpostlikes/<str:postId>",GetPostLikes.as_view() , name="getPost"),
    path("<str:username>/followers",GetUserFollowers.as_view() , name="getFollowers"),
    path("<str:username>/following",GetUserFollowing.as_view() , name="getFollowing"),
    path("follow/<str:username>",FollowUser.as_view() , name="follow"),
    path("unfollow/<str:username>",UnfollowUser.as_view() , name="unfollow"),
    path("getuserhoverinfo/<str:username>",GetUserHoverPreview.as_view() , name="getUserHover"),
    path("getuserinfo/<str:username>",GetUserInfo.as_view() , name="getUserInfo"),
    path("comments/<str:postId>",GetPostComments.as_view() , name="getPostComment"),
    path("comment/<str:commentId>/likes",GetCommentLikes.as_view() , name="getPostCommentLikes"),
    path("comment/like/<str:commentId>/",LikeComment.as_view() , name="likeComment"),
    path("comment/unlike/<str:commentId>/",UnlikeComment.as_view() , name="unlikeComment"),
    path("comment/replies/<str:commentId>",GetCommentReplies.as_view() , name="GetCommentReplies"),
    path("comment/add/",AddPostComment.as_view() , name="AddPostComment"),
    path("search/<str:searchType>/",SearchUsersAndTags.as_view() , name="Search"),
    path("readnotification/",MarkNotificationsAsRead.as_view() , name="ReadNotification"),
    path("getnewfewpost/<str:postId>",GetFirstFewPost.as_view() , name="GetNewPosts"),
    path("hashtag/<str:hashtag>",HastagPosts.as_view() , name="GetHashtagPosts"),
    path("tagged/<str:username>",GetTaggedPosts.as_view() , name="GetTaggedPosts"),
    path("reels/<str:username>",UserReels.as_view() , name="GetReelPosts"),
    path("reels/",GetReels.as_view() , name="GetReels"),
    path("post/add/",AddPost.as_view() , name="AddPost"),
    path("stories/<str:username>",UserStories.as_view() , name="UserStories"),
    path("homestories",HomeStories.as_view() , name="HomeStories"),
    path("highlights/<str:username>",UserHighlights.as_view() , name="UserHighlights"),
    path("feedposts",FeedPosts.as_view() , name="FeedPosts"),
    path("suggestedusers",SuggestedUsersAPIView.as_view() , name="SuggestedUsers"),
    path("savedposts",GetSavedPosts.as_view() , name="GetSavedPosts"),
    path("addsavedfolder/",AddSavedFolder.as_view() , name="AddSavedFolder"),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
