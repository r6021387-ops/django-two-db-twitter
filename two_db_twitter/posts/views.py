from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.forms import modelformset_factory
from .models import Post, PostImage, Category
from .forms import PostForm, ImageForm
from .forms import CommentForm
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib.auth import update_session_auth_hash
from .models import Profile
from .forms import ProfileForm
from django.contrib.auth import get_user_model
from .models import Profile, Post

User = get_user_model()

def user_profile(request, username):

    user = get_object_or_404(User.objects.using('default'), username=username)

    try:
        profile = Profile.objects.using('default').get(user=user)
    except Profile.DoesNotExist:
        profile = None

    posts = Post.objects.using('postgres').filter(author_id=user.id).order_by('-created_at').select_related('category').prefetch_related('images')

    posts_data = []
    for post in posts:
        posts_data.append({
            'id': post.id,
            'content': post.content,
            'created_at': post.created_at,
            'category': post.category,
            'images': post.images.all(),
            'author_name': user.username,
        })
    return render(request, 'posts/user_profile.html', {
        'profile_user': user,
        'profile': profile,
        'posts_data': posts_data,
    })

@login_required
def profile_view(request):

    profile, created = Profile.objects.using('default').get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.save(using='default')
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'posts/profile.html', {
        'form': form,
        'profile': profile,
    })

@require_POST
@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post.objects.using('postgres'), pk=post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author_id = request.user.id
        comment.save(using='postgres')
    return redirect('post_detail', pk=post_id)


@login_required
def create_post(request):
    ImageFormSet = modelformset_factory(PostImage, form=ImageForm, extra=3, max_num=5)

    if request.method == 'POST':
        post_form = PostForm(request.POST)
        formset = ImageFormSet(request.POST, request.FILES, queryset=PostImage.objects.none())

        if post_form.is_valid() and formset.is_valid():
            post = post_form.save(commit=False)
            post.author_id = request.user.id
            post.save(using='postgres')

            for form in formset.cleaned_data:
                if form:
                    image = form['image']
                    PostImage.objects.using('postgres').create(post=post, image=image)

            return redirect('post_list')
    else:
        post_form = PostForm()
        formset = ImageFormSet(queryset=PostImage.objects.none())

    categories = Category.objects.using('postgres').all()
    return render(request, 'posts/create_post.html', {
        'post_form': post_form,
        'formset': formset,
        'categories': categories,
    })


def post_list(request):

    posts = Post.objects.using('postgres').all().order_by('-created_at')


    query = request.GET.get('q', '')
    if query:
        posts = posts.filter(content__icontains=query)


    category_id = request.GET.get('category', '')
    if category_id and category_id.isdigit():
        posts = posts.filter(category_id=int(category_id))


    posts = posts.select_related('category').prefetch_related('images')


    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)


    author_ids = [post.author_id for post in page_obj]
    authors = User.objects.using('default').filter(id__in=author_ids).in_bulk()


    posts_data = []
    for post in page_obj:
        author = authors.get(post.author_id)
        author_username = author.username if author else None
        posts_data.append({
            'id': post.id,
            'content': post.content,
            'created_at': post.created_at,
            'category': post.category,
            'images': post.images.all(),
            'author_name': author.username if author else 'Неизвестный пользователь',
            'author_username': author_username,
        })


    categories = Category.objects.using('postgres').all().order_by('name')

    return render(request, 'posts/post_list.html', {
        'posts_data': posts_data,
        'categories': categories,
        'current_query': query,
        'current_category': category_id,
        'page_obj': page_obj,
    })

@login_required
def edit_post(request, pk):
    post = get_object_or_404(Post.objects.using('postgres'), pk=pk)

    if post.author_id != request.user.id and not request.user.is_superuser:
        return HttpResponseForbidden("Вы не можете редактировать этот пост.")

    ImageFormSet = modelformset_factory(PostImage, form=ImageForm, extra=3, max_num=5, can_delete=True)

    if request.method == 'POST':
        post_form = PostForm(request.POST, instance=post)
        formset = ImageFormSet(request.POST, request.FILES, queryset=PostImage.objects.using('postgres').filter(post=post))

        if post_form.is_valid() and formset.is_valid():
            updated_post = post_form.save(commit=False)
            updated_post.save(using='postgres')

            instances = formset.save(commit=False)
            for obj in instances:
                obj.post = updated_post
                obj.save(using='postgres')
            for obj in formset.deleted_objects:
                obj.delete(using='postgres')

            return redirect('post_list')
    else:
        post_form = PostForm(instance=post)
        formset = ImageFormSet(queryset=PostImage.objects.using('postgres').filter(post=post))

    categories = Category.objects.using('postgres').all()
    return render(request, 'posts/edit_post.html', {
        'post_form': post_form,
        'formset': formset,
        'post': post,
        'categories': categories,
    })

@login_required
def delete_post(request, pk):
    post = get_object_or_404(Post.objects.using('postgres'), pk=pk)

    if post.author_id != request.user.id and not request.user.is_superuser:
        return HttpResponseForbidden("Вы не можете удалить этот пост.")

    if request.method == 'POST':
        post.delete(using='postgres')
        return redirect('post_list')

    return render(request, 'posts/confirm_delete.html', {'post': post})


def post_detail(request, pk):
    post = get_object_or_404(Post.objects.using('postgres').select_related('category').prefetch_related('images', 'comments'), pk=pk)
    author = User.objects.using('default').get(pk=post.author_id)

    comments_data = []
    comment_authors_ids = set()
    for comment in post.comments.all():
        comment_authors_ids.add(comment.author_id)
        comments_data.append({
            'id': comment.id,
            'content': comment.content,
            'created_at': comment.created_at,
            'author_id': comment.author_id,
        })
    authors = User.objects.using('default').filter(id__in=comment_authors_ids).in_bulk()
    for c in comments_data:
        c['author_name'] = authors.get(c['author_id']).username if authors.get(c['author_id']) else 'Неизвестный'

    comment_form = CommentForm()
    return render(request, 'posts/post_detail.html', {
        'post': post,
        'author_name': author.username,
        'comments_data': comments_data,
        'comment_form': comment_form
    })
