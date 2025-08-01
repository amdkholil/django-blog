from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from filer.models import Image
from .models import Category, Tag, Post, Comment

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'post_count', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    def post_count(self, obj):
        return obj.posts.count()
    post_count.short_description = 'Jumlah Post'

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'post_count', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
    readonly_fields = ['created_at']
    
    def post_count(self, obj):
        return obj.posts.count()
    post_count.short_description = 'Jumlah Post'

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'category', 'status', 'publish_date', 
        'is_featured', 'view_count', 'featured_image_preview'
    ]
    list_filter = [
        'status', 'category', 'tags', 'is_featured', 
        'allow_comments', 'created_at', 'publish_date'
    ]
    search_fields = ['title', 'content', 'meta_title']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['tags']
    date_hierarchy = 'publish_date'
    
    fieldsets = (
        ('Konten Utama', {
            'fields': ('title', 'slug', 'content'),
            'classes': ('wide',)
        }),
        ('Media', {
            'fields': ('featured_image',),
            'classes': ('collapse',)
        }),
        ('Kategorisasi', {
            'fields': ('category', 'tags'),
            'classes': ('wide',)
        }),
        ('Publikasi', {
            'fields': (
                'status', 'publish_date', 'is_featured', 
                'allow_comments'
            ),
            'classes': ('wide',)
        }),
        ('SEO & Meta', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Informasi Sistem', {
            'fields': ('author', 'view_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['view_count', 'created_at', 'updated_at']
    
    def featured_image_preview(self, obj):
        if obj.featured_image:
            try:
                thumbnail = obj.featured_image.easy_thumbnails_thumbnailer.get_thumbnail({
                    'size': (100, 100),
                    'crop': True,
                    'upscale': True
                })
                return format_html(
                    '<img src="{}" style="max-height: 50px; max-width: 100px; border-radius: 4px;" />',
                    thumbnail.url
                )
            except:
                return format_html(
                    '<img src="{}" style="max-height: 50px; max-width: 100px; border-radius: 4px;" />',
                    obj.featured_image.url
                )
        return "No Image"
    featured_image_preview.short_description = "Preview"
    
    def save_model(self, request, obj, form, change):
        if not obj.author_id:
            obj.author = request.user
        super().save_model(request, obj, form, change)
    
    # Custom actions
    actions = ['make_published', 'make_draft', 'make_featured', 'remove_featured']
    
    def make_published(self, request, queryset):
        updated = queryset.update(status='published')
        self.message_user(request, f'{updated} post(s) berhasil dipublish.')
    make_published.short_description = "Publish selected posts"
    
    def make_draft(self, request, queryset):
        updated = queryset.update(status='draft')
        self.message_user(request, f'{updated} post(s) berhasil dijadikan draft.')
    make_draft.short_description = "Make selected posts draft"
    
    def make_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} post(s) berhasil dijadikan featured.')
    make_featured.short_description = "Make selected posts featured"
    
    def remove_featured(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} post(s) berhasil dihapus dari featured.')
    remove_featured.short_description = "Remove featured from selected posts"

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['name', 'post', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'created_at']
    search_fields = ['name', 'email', 'content', 'post__title']
    readonly_fields = ['created_at']
    actions = ['approve_comments', 'disapprove_comments']
    
    def approve_comments(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} komentar berhasil disetujui.')
    approve_comments.short_description = "Approve selected comments"
    
    def disapprove_comments(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} komentar berhasil ditolak.')
    disapprove_comments.short_description = "Disapprove selected comments"
