from django.db import models
from django.utils.translation import gettext_lazy as _

import mimetypes
from pathlib import Path
from urllib.parse import urlparse
from functools import lru_cache
import weasyprint

from django.conf import settings
from django.contrib.staticfiles.finders import find
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.files.storage import default_storage
from django.urls import get_script_prefix


class BaseModel(models.Model):
    created = models.DateTimeField(
        _("created"), auto_now_add=True, editable=False, db_index=True
    )
    modified = models.DateTimeField(auto_now=True, editable=False)

    # access non deleted data only
    data = models.Manager()
    # fallback for 3rd party libs not respecting the default manager
    objects = models.Manager()

    class Meta:
        abstract = True
        ordering = ["-created"]
        get_latest_by = "created"
        base_manager_name = "data"
        default_manager_name = "data"


@lru_cache(maxsize=None)
def get_reversed_hashed_files():
    return {v: k for k, v in staticfiles_storage.hashed_files.items()}


def django_url_fetcher(url, *args, **kwargs):
    # attempt to load file:// paths to Django MEDIA or STATIC files directly from disk
    if url.startswith('file:'):
        mime_type, encoding = mimetypes.guess_type(url)
        url_path = urlparse(url).path
        data = {
            'mime_type': mime_type,
            'encoding': encoding,
            'filename': Path(url_path).name,
        }

        default_media_url = settings.MEDIA_URL in ('', get_script_prefix())
        if not default_media_url and url_path.startswith(settings.MEDIA_URL):
            cleaned_media_root = str(settings.MEDIA_ROOT)
            if not cleaned_media_root.endswith('/'):
                cleaned_media_root += '/'
            absolute_path = url_path.replace(settings.MEDIA_URL, cleaned_media_root, 1)
            data['file_obj'] = default_storage.open(absolute_path, 'rb')
            data['redirected_url'] = 'file://' + absolute_path
            return data

        # path looks like a static file based on configured STATIC_URL
        elif settings.STATIC_URL and url_path.startswith(settings.STATIC_URL):
            # strip the STATIC_URL prefix to get the relative filesystem path
            relative_path = url_path.replace(settings.STATIC_URL, '', 1)
            # detect hashed files storage and get path with un-hashed filename
            if not settings.DEBUG and hasattr(staticfiles_storage, 'hashed_files'):
                relative_path = get_reversed_hashed_files()[relative_path]
                data['filename'] = Path(relative_path).name
            # find the absolute path using the static file finders
            absolute_path = find(relative_path)
            if absolute_path:
                data['file_obj'] = open(absolute_path, 'rb')  # noqa: PTH123
                data['redirected_url'] = 'file://' + absolute_path
                return data

    # Fall back to weasyprint default fetcher for http/s: and file: paths
    # that did not match MEDIA_URL or STATIC_URL.
    return weasyprint.default_url_fetcher(url, *args, **kwargs)
