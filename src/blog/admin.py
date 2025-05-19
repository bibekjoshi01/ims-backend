from django.contrib import admin

from .models import Post, PostCategory, PostComment, PostTag

admin.site.register(PostCategory)
admin.site.register(PostTag)
admin.site.register(Post)
admin.site.register(PostComment)
