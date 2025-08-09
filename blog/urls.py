from django.urls import path
from . import views


app_name = 'blog'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('search/', views.SearchResultsView.as_view(), name='search'),
    path('post/create/', views.PostCreateView.as_view(), name='post_create'),
    path('post/<slug:slug>/', views.PostDetailView.as_view(), name='post_detail'),
    path('post/<slug:slug>/edit/', views.PostUpdateView.as_view(), name='post_edit'),
    path('post/<slug:slug>/delete/', views.PostDeleteView.as_view(), name='post_delete'),
    path('author/<str:username>/', views.AuthorProfileView.as_view(), name='author_profile'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile_edit'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    

    # AJAX endpoints
    path('ajax/toggle-follow/', views.toggle_follow, name='toggle_follow'),
    path('ajax/post-view/', views.increment_post_view, name='increment_post_view'),
    path('ajax/add-comment/<slug:slug>/', views.ajax_add_comment, name='ajax_add_comment'),

   
]
