from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponseForbidden
from .models import Post, Category, Comment, Follow, Profile, PostView
from .forms import PostForm, CommentForm, ProfileForm, CustomUserCreationForm, CustomLoginForm
from django.contrib.auth.models import User
from django.db.models import Count, F, Q
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.utils.html import strip_tags

class HomeView(ListView):
    model = Post
    template_name = 'blog/home.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        qs = Post.objects.filter(published=True).select_related('author', 'category')
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(content__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        context['categories'] = Category.objects.all()
        context['total_posts'] = Post.objects.filter(published=True).count()
        return context


class SearchResultsView(HomeView):
    template_name = 'blog/search_results.html'

class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['comment_form'] = CommentForm()
        ctx['is_following'] = False
        ctx['stripped_content'] = strip_tags(self.object.content)
        user = self.request.user
        if user.is_authenticated:
            ctx['is_following'] = Follow.objects.filter(follower=user, following=self.object.author).exists()
        return ctx

class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/post_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['type'] = 'create'
        return context

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/post_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['type'] = 'update'
        return context

    def test_func(self):
        return self.get_object().author == self.request.user
    model = Post
    form_class = PostForm
    template_name = 'blog/post_form.html'
    type='update'

    def test_func(self):
        return self.get_object().author == self.request.user

class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    success_url = reverse_lazy('blog:home')
    template_name = 'blog/post_confirm_delete.html'

    def test_func(self):
        return self.get_object().author == self.request.user

class AuthorProfileView(TemplateView):
    template_name = 'blog/author_profile.html'

    def get(self, request, username, *args, **kwargs):
        user = get_object_or_404(User, username=username)
        posts = Post.objects.filter(author=user, published=True)
        followers = Follow.objects.filter(following=user).count()
        following = Follow.objects.filter(follower=user).count()
        is_following = False
        if request.user.is_authenticated:
            is_following = Follow.objects.filter(follower=request.user, following=user).exists()
        return render(request, self.template_name, {
            'author': user, 'posts': posts, 'followers': followers, 'following': following,
            'is_following': is_following
        })
    
class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = ProfileForm
    template_name = 'blog/profile_update.html'

    def get_object(self, queryset=None):
        # Always edit the logged-in user's profile
        return self.request.user.profile

    def get_success_url(self):
        # Redirect to the author's public profile after update
        return reverse_lazy('blog:author_profile', kwargs={'username': self.request.user.username})

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'blog/dashboard.html'

    def get(self, request, *args, **kwargs):
        user = request.user
        posts = Post.objects.filter(author=user)
        total_posts = posts.count()
        total_views = posts.aggregate(total=Count('views'))['total'] or 0
        total_comments = posts.aggregate(total=Count('comments'))['total'] or 0
        total_followers = Follow.objects.filter(following=user).count()
        return render(request, self.template_name, {
            'posts': posts, 'total_posts': total_posts, 'total_views': total_views,
            'total_followers': total_followers,'total_comments':total_comments
        })

# AJAX endpoints
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

@require_POST
def toggle_follow(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error':'login required'}, status=403)
    target_username = request.POST.get('username')
    if not target_username:
        return JsonResponse({'error':'username required'}, status=400)
    target = get_object_or_404(User, username=target_username)
    if target == request.user:
        return JsonResponse({'error':"can't follow yourself"}, status=400)
    obj, created = Follow.objects.get_or_create(follower=request.user, following=target)
    if not created:
        obj.delete()
        return JsonResponse({'status':'unfollowed', 'followers_count': Follow.objects.filter(following=target).count()})
    return JsonResponse({'status':'followed', 'followers_count': Follow.objects.filter(following=target).count()})

@require_POST
def increment_post_view(request):
    slug = request.POST.get('slug')
    if not slug:
        return JsonResponse({'error':'slug required'}, status=400)
    post = get_object_or_404(Post, slug=slug)
    # create PostView record (optional dedupe by user or ip)
    ip = request.META.get('REMOTE_ADDR')
    PostView.objects.create(post=post, user=(request.user if request.user.is_authenticated else None), ip_address=ip)
    post.views = F('views') + 1
    post.save(update_fields=['views'])
    post.refresh_from_db()
    return JsonResponse({'views': post.views})

@require_POST
def ajax_add_comment(request, slug):
    if not request.user.is_authenticated:
        return JsonResponse({'error':'login required'}, status=403)
    post = get_object_or_404(Post, slug=slug)
    body = request.POST.get('body', '').strip()
    if not body:
        return JsonResponse({'error':'empty comment'}, status=400)
    comment = Comment.objects.create(post=post, author=request.user, body=body)
    # respond with basic HTML or JSON
    return JsonResponse({
        'status':'ok',
        'comment': {
            'author': request.user.username,
            'body': comment.body,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M')
        },
        'comments_count': post.comments.count()
    })


@login_required
def author_profile(request):
    return render(request, 'blog/author_profile.html', {'author': request.user})


from django.contrib.auth import login, logout, authenticate
from django.shortcuts import render, redirect
from django.views import View

class SignUpView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('blog:dashboard')
        form = CustomUserCreationForm()
        return render(request, 'blog/signup.html', {'form': form})

    def post(self, request):
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('blog:dashboard')
        return render(request, 'blog/signup.html', {'form': form})

class LoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('blog:dashboard')
        form = CustomLoginForm()
        return render(request, 'blog/login.html', {'form': form})

    def post(self, request):
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('blog:dashboard')
        return render(request, 'blog/login.html', {'form': form})

class LogoutView(View):
    def post(self, request):
        logout(request)
        return redirect('login')