from django import forms
from .models import Post, Comment, Category, Profile
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm


from ckeditor.widgets import CKEditorWidget # type: ignore
from ckeditor_uploader.widgets import CKEditorUploadingWidget # type: ignore

class PostForm(forms.ModelForm):
    new_category = forms.CharField(required=False, help_text='Create a new category if not listed')
    content = forms.CharField(widget=CKEditorUploadingWidget())

    class Meta:
        model = Post
        fields = ['title', 'slug', 'content', 'featured_image', 'category', 'published']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add Tailwind CSS classes for styling inputs/selects/file inputs
        common_classes = 'border border-gray-300 rounded px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-indigo-500'

        self.fields['title'].widget.attrs.update({'class': common_classes})
        self.fields['slug'].widget.attrs.update({'class': common_classes})
        self.fields['featured_image'].widget.attrs.update({'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 '
                         'file:rounded-full file:border-0 file:text-sm file:font-semibold '
                         'file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100'})
        self.fields['category'].widget.attrs.update({'class': common_classes})
        self.fields['published'].widget.attrs.update({'class': 'mr-2 leading-tight'})

        # You can optionally add custom classes to new_category or content if needed
        self.fields['new_category'].widget.attrs.update({'class': common_classes + ' mt-2'})

    def clean(self):
        cleaned = super().clean()
        new_cat = cleaned.get('new_category')
        if new_cat:
            cat, created = Category.objects.get_or_create(
                name=new_cat.strip(),
                defaults={'slug': new_cat.strip().lower().replace(' ', '-')}
            )
            cleaned['category'] = cat
        return cleaned

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['body']
        widgets = {'body': forms.Textarea(attrs={'rows':3, 'placeholder': 'Write your comment...'})}

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'avatar']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'w-full border border-gray-300 rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-indigo-500',
                'rows': 4,
                'placeholder': 'Write something about yourself...'
            }),
            'avatar': forms.ClearableFileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 '
                         'file:rounded-full file:border-0 file:text-sm file:font-semibold '
                         'file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100'
            }),
        }

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'border border-gray-300 rounded px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-indigo-500'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'border border-gray-300 rounded px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-indigo-500'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add Tailwind classes to password1 and password2 manually:
        self.fields['password1'].widget.attrs.update({
            'class': 'border border-gray-300 rounded px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-indigo-500'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'border border-gray-300 rounded px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-indigo-500'
        })

class CustomLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add Tailwind classes to username field
        self.fields['username'].widget.attrs.update({
            'class': 'border border-gray-300 rounded px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-indigo-500',
            'placeholder': 'Username or Email',
        })

        # Add Tailwind classes to password field
        self.fields['password'].widget.attrs.update({
            'class': 'border border-gray-300 rounded px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-indigo-500',
            'placeholder': 'Password',
        })