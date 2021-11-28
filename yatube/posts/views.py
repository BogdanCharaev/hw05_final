from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post

User = get_user_model()


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }

    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):

    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    paginator = Paginator(post_list, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    count = author.posts.all().count()
    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=author
        ).exists()
    context = {
        'page_obj': page_obj,
        'author': author,
        'count': count,
        'following': following,

    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):

    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all()
    form = CommentForm(request.POST or None)

    author = post.author
    count = author.posts.all().count()
    context = {
        'form': form,
        'count': count,
        'post': post,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):

    if request.method != 'POST':

        form = PostForm()

        return render(request, 'posts/create_post.html', {'form': form})

    form = PostForm(request.POST or None,
                    files=request.FILES or None)

    if not form.is_valid():

        return render(request, 'posts/create_post.html', {'form': form})

    post = form.save(commit=False)
    post.author = request.user
    form.save()
    return redirect('posts:profile', post.author)


@login_required
def post_edit(request, post_id):

    post = get_object_or_404(Post, id=post_id)
    if post.author == request.user:

        form = PostForm(request.POST or None,
                        files=request.FILES or None, instance=post)

    else:
        return redirect('posts:index')

    if request.method != 'POST':

        return render(request, 'posts/create_post.html', {'form': form,
                                                          'post': post,
                                                          'is_edit': True})

    form = PostForm(request.POST or None,
                    files=request.FILES or None, instance=post)

    if not form.is_valid():

        return render(request, 'posts/create_post.html', {'form': form,
                                                          'post': post,
                                                          'is_edit': True})

    post = form.save(commit=False)
    post.author = request.user
    form.save()
    return redirect('posts:post_detail', post.id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }

    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        object = Follow.objects.filter(user=request.user, author=author)
        if object.exists():
            object.delete()
    return redirect('posts:profile', username)
