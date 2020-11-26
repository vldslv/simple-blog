from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ("text", "group", "image")
        labels = {"text": "Текст", "group": "Группа", "image": "Картинка"}
        help_texts = {
            "text": "Напишите здесь текст нового поста (обязательное поле)",
            "group": "Выберите подходящую группу из списка",
            "image": "Добавьте картинку к посту"
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("text",)
        labels = {"text": "Комментарий"}
        help_texts = {"text": "Напишите здесь текст комментария"}