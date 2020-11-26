from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from .models import Post, Group, Follow, User

from .forms import PostForm, CommentForm

@cache_page (20)
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
         request,
         "index.html",
         {"page": page, "paginator": paginator}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
        request,
        "group.html",
        {"group": group, "page": page, "paginator": paginator}
    )


@login_required
def new_post(request):
    if request.method != "POST":
        form = PostForm()
        return render(request, "new_post.html", {"form": form})
    form = PostForm(request.POST, files=request.FILES)
    if not form.is_valid():
        return render(request, "new_post.html", {"form": form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect("index")
    

def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    post_count = post_list.count()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    following = False
    obj = Follow.objects.filter(user__id=request.user.id, author=author)
    if obj:
        following = True
    return render(
        request,
        "profile.html",
        {
            "author": author,
            "page": page,
            "paginator": paginator,
            "post_count": post_count,
            "following": following
        }
    )

 
def post_view(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    author = post.author
    comments = post.comments.all()
    post_count = author.posts.all().count()
    form = CommentForm()
    following = False
    obj = Follow.objects.filter(user__id=request.user.id, author=author)
    if obj:
        following = True
    return render(
        request,
        "post.html",
        {
            "author": author,
            "post": post,
            "post_count": post_count,
            "comments": comments,
            "form": form,
            "following": following
        }
    )


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    form = CommentForm(request.POST or None)
    author = post.author
    comments = post.comments.all()
    if not form.is_valid():
        return render(
            request,
            "post.html",
            {
                "author": author,
                "form": form,
                "post": post,
                "comments": comments,
            }
        )
    comment = form.save(commit=False)
    comment.post = post
    comment.author = request.user
    comment.save()
    return redirect("post", username=post.author, post_id=post_id)


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    author = post.author
    if author != request.user:
        return redirect("post", username=username, post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        post.save()
        return redirect("post", username=username, post_id=post_id)           
    else:
        form = PostForm(instance=post)
    return render(
        request,
        "new_post.html",
        {"form": form, "is_editing": True, "post": post}
    )


def page_not_found(request, exception):
    return render(
        request, 
        "misc/404.html", 
        {"path": request.path}, 
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
         request,
         "follow.html",
         {"page": page, "paginator": paginator}
    )


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    obj = author.following.filter(user=request.user).exists()
    if not obj and request.user != author:
        author.following.create(user=request.user)
    return redirect("profile", username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    obj = author.following.filter(user=request.user)
    if obj.exists():
        obj.delete()
    return redirect("profile", username)
