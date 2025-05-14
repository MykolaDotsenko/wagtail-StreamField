from django.db import models
from django import forms
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase
from wagtail.models import Page, Orderable
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.search import index
from wagtail.snippets.models import register_snippet
from wagtail.fields import StreamField
from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock
from wagtail.embeds.blocks import EmbedBlock

class BlogIndexPage(Page):
    intro = RichTextField(blank=True)

    def get_context(self, request):
        context = super().get_context(request)
        blogpages = self.get_children().live().order_by('-first_published_at')
        context['blogpages'] = blogpages
        return context

    content_panels = Page.content_panels + [
        "intro",
    ]

class BlogPageTag(TaggedItemBase):
    content_object = ParentalKey(
        'BlogPage',
        related_name='tagged_items',
        on_delete=models.CASCADE
    )

class BlogPage(Page):
    date = models.DateField("Post date")
    intro = models.CharField(max_length=250)
    authors = ParentalManyToManyField('blog.Author', blank=True)
    tags = ClusterTaggableManager(through=BlogPageTag, blank=True)
    body = StreamField([
        ('heading', blocks.CharBlock(form_classname="full title", template="blog/streamfield/blocks/heading_block.html")), # <-- Указали шаблон
        ('paragraph', blocks.RichTextBlock()), # Для RichTextBlock и EmbedBlock стандартные шаблоны Wagtail обычно подходят
        ('image', ImageChooserBlock(template="blog/streamfield/blocks/image_block.html")), # <-- Указали шаблон
        ('quote', blocks.BlockQuoteBlock()),
        ('embed', EmbedBlock()),
    ], use_json_field=True)  # use_json_field=True - это рекомендуемый способ хранения StreamField в новых версиях Wagtail

    def main_image(self):
        gallery_item = self.gallery_images.first()
        if gallery_item:
            return gallery_item.image
        return None

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel("date"),  # Используем FieldPanel для единообразия
            FieldPanel("authors", widget=forms.CheckboxSelectMultiple),
            FieldPanel("tags"),  # Используем FieldPanel для единообразия
        ], heading="Blog information"),
        FieldPanel("intro"),
        FieldPanel("body"),  # Теперь это FieldPanel для StreamField
        # Если ты удалил галерею изображений, удали и соответствующий MultiFieldPanel отсюда
    ]

class BlogPageGalleryImage(Orderable):
    page = ParentalKey(BlogPage, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ForeignKey(
        'wagtailimages.Image', on_delete=models.CASCADE, related_name='+'
    )
    caption = models.CharField(blank=True, max_length=250)

    panels = [
        "image",
        "caption",
    ]

@register_snippet
class Author(models.Model):
    name = models.CharField(max_length=255)
    author_image = models.ForeignKey(
        'wagtailimages.Image', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )

    panels = [
        "name",
        "author_image",
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Authors'

class BlogTagIndexPage(Page):
    def get_context(self, request):
        tag = request.GET.get('tag')
        blogpages = BlogPage.objects.filter(tags__name=tag)
        context = super().get_context(request)
        context['blogpages'] = blogpages
        return context