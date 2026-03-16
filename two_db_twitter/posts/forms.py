from django import forms
from .models import Post, PostImage, Category, Comment
from django import forms
from .models import Profile


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar', 'bio', 'birth_date']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }

class PostForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=Category.objects.using('postgres').all(),
        required=False
    )

    class Meta:
        model = Post
        fields = ['content', 'category']

class ImageForm(forms.ModelForm):
    class Meta:
        model = PostImage
        fields = ['image']

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Ваш комментарий...'})
        }
