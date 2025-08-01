from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from filer.fields.image import FilerImageField
from mdeditor.fields import MDTextField


class Category(models.Model):
    """Model untuk kategori blog post"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Nama Kategori")
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True, verbose_name="Deskripsi")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Kategori"
        verbose_name_plural = "Kategori"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:category_detail', kwargs={'slug': self.slug})


class Tag(models.Model):
    """Model untuk tag blog post"""
    name = models.CharField(max_length=50, unique=True, verbose_name="Nama Tag")
    slug = models.SlugField(max_length=50, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tag"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:tag_detail', kwargs={'slug': self.slug})


class Post(models.Model):
    """Model untuk blog post"""
    
    # Status choices
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    # Basic fields
    title = models.CharField(max_length=200, verbose_name="Judul")
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    content = MDTextField(verbose_name="Konten")
    
    # Meta fields
    meta_title = models.CharField(max_length=60, blank=True, verbose_name="Meta Title")
    meta_description = models.CharField(max_length=160, blank=True, verbose_name="Meta Description")
    
    # Relations
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='posts',
        verbose_name="Penulis"
    )
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='posts',
        verbose_name="Kategori"
    )
    tags = models.ManyToManyField(
        Tag, 
        blank=True, 
        related_name='posts',
        verbose_name="Tag"
    )
    
    # Status and scheduling
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='draft',
        verbose_name="Status"
    )
    publish_date = models.DateTimeField(
        default=timezone.now,
        verbose_name="Tanggal Publish"
    )
    
    # Featured image with Django Filer
    featured_image = FilerImageField(
        null=True, 
        blank=True, 
        related_name="blog_featured_images",
        on_delete=models.SET_NULL,
        verbose_name="Gambar Utama"
    )
    
    
    # SEO and engagement
    view_count = models.PositiveIntegerField(default=0, verbose_name="Jumlah View")
    allow_comments = models.BooleanField(default=True, verbose_name="Izinkan Komentar")
    is_featured = models.BooleanField(default=False, verbose_name="Artikel Unggulan")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Post"
        verbose_name_plural = "Posts"
        ordering = ['-publish_date', '-created_at']
        indexes = [
            models.Index(fields=['-publish_date']),
            models.Index(fields=['status']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        
            
        # Auto generate meta fields if not provided
        if not self.meta_title:
            self.meta_title = self.title[:60]
        if not self.meta_description:
            self.meta_description = self.title[:160]
            
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:post_detail', kwargs={'slug': self.slug})

    @property
    def is_published(self):
        """Check if post is published and publish date has passed"""
        return (
            self.status == 'published' and 
            self.publish_date <= timezone.now()
        )

    @property
    def is_scheduled(self):
        """Check if post is scheduled for future publication"""
        return (
            self.status == 'published' and 
            self.publish_date > timezone.now()
        )

    def increment_view_count(self):
        """Increment view count"""
        self.view_count += 1
        self.save(update_fields=['view_count'])

    def get_related_posts(self, limit=3):
        """Get related posts based on category and tags"""
        related_posts = Post.objects.filter(
            status='published',
            publish_date__lte=timezone.now()
        ).exclude(id=self.id)
        
        if self.category:
            related_posts = related_posts.filter(category=self.category)
        
        # If we have tags, also filter by tags
        if self.tags.exists():
            related_posts = related_posts.filter(tags__in=self.tags.all()).distinct()
            
        return related_posts[:limit]


class PostManager(models.Manager):
    """Custom manager for Post model"""
    
    def published(self):
        """Return only published posts that are not scheduled"""
        return self.filter(
            status='published',
            publish_date__lte=timezone.now()
        )
    
    def scheduled(self):
        """Return scheduled posts"""
        return self.filter(
            status='published',
            publish_date__gt=timezone.now()
        )
    
    def featured(self):
        """Return featured published posts"""
        return self.published().filter(is_featured=True)


# Add custom manager to Post model
Post.add_to_class('objects', PostManager())


class Comment(models.Model):
    """Model untuk komentar (opsional)"""
    post = models.ForeignKey(
        Post, 
        on_delete=models.CASCADE, 
        related_name='comments'
    )
    name = models.CharField(max_length=100, verbose_name="Nama")
    email = models.EmailField(verbose_name="Email")
    website = models.URLField(blank=True, verbose_name="Website")
    content = models.TextField(verbose_name="Komentar")
    is_approved = models.BooleanField(default=False, verbose_name="Disetujui")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Komentar"
        verbose_name_plural = "Komentar"
        ordering = ['created_at']

    def __str__(self):
        return f'Komentar oleh {self.name} pada {self.post.title}'