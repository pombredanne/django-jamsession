from django.contrib.admin.sites import site
from django.core.urlresolvers import reverse
from django.core.exceptions import ImproperlyConfigured

from django.http import Http404

from django.views.generic.edit import CreateView
from django.views.generic.base import View, TemplateView

from jamsession.models import Schema
from jamsession.forms.admin import SchemaAdminForm


class ContextMixin(View):
    """
    get_context_data will update itself from self.extra_context if it exists
    """
    def get_context_data(self, **kwargs):
        context = super(ContextMixin, self).get_context_data(**kwargs)
        if getattr(self, 'extra_context', None):
            context.update(self.extra_context)
        return context


class AdminViewMixin(ContextMixin):
    """Base for all the Jamsession Admin Views"""
    object_types = {
        'schema': (Schema, SchemaAdminForm)
    }

    @classmethod
    def as_view(self, *args, **kwargs):
        view = super(AdminViewMixin, self).as_view(*args, **kwargs)
        view = site.admin_view(view)
        return view


class DashboardView(AdminViewMixin, TemplateView):
    template_name = 'jamsession/admin/dashboard.html'
    extra_context = {'title': "Jamsession Administration"}


class AdminCreateView(AdminViewMixin, CreateView):
    template_name = 'jamsession/admin/create_object.html'

    def _construct_object_dictionary(self, obj):
        """
        Used to access an objection like a dictionary
        Useful for get_success_url
        """
        obj_dict = {}
        keys = [key for key in dir(obj) if not key.startswith('_')]
        for key in keys:
            attr = getattr(obj, key)
            if not callable(attr):
                obj_dict[key] = attr
        return obj_dict

    def get_success_url(self):
        """
        Determines where to redirect to if the form
        successfully saves. Handles:
        * Save
        * Save and continue editing
        * Save and add another

        Falls back to self.success_url and then
        object.get_absolute_url()
        """

        if '_save' in self.request.POST:
            return self.get_save_url()
        if '_continue' in self.request.POST:
            return self.get_continue_url()
        if '_addanother' in self.request.POST:
            return self.get_addanother_url()

        if self.success_url:
            url = self.success_url % \
                self._construct_object_dictionary(self.object)
        else:
            try:
                url = self.object.get_absolute_url()
            except AttributeError:
                raise ImproperlyConfigured(
                    "No URL to redirect to.  Either provide a url or define"
                    " a get_absolute_url method on the Model.")
        return url

    def get_save_url(self):
        """URL for user press of the "Save" button"""
        return self.save_url % self._construct_object_dictionary(self.object)

    def get_continue_url(self):
        """URL for user press of the "Save and Continue Editing" button"""
        return self.continue_url % \
            self._construct_object_dictionary(self.object)

    def get_addanother_url(self):
        """URL for user press of the "Save and Add Another" button"""
        return self.addanother_url % \
            self._construct_object_dictionary(self.object)

    def dispatch(self, request, object_type):
        klass, form_klass = self.object_types.get(object_type, (None, None))
        if not klass:
            raise Http404("Content type %s not found" % object_type)

        self.extra_context = {
            'title': 'Add %s' % klass.verbose_name,
            'klass': klass,
            'add': True,
            'obj': None,
        }

        self.form_class = form_klass
        self.save_url = reverse("jamsession:admin-changelist-object",
                            kwargs=dict(object_type=object_type))
        self.continue_url = reverse("jamsession:admin-edit-object",
                                kwargs=dict(object_type=object_type,
                                            object_id="%(id)s")
                                )
        self.success_url = self.continue_url
        self.addanother_url = reverse("jamsession:admin-create-object",
                                  kwargs=dict(object_type=object_type))
        return super(AdminCreateView, self).dispatch(request, object_type)


@site.admin_view
def edit_object(request, object_type, object_id):
    from django.http import HttpResponse
    return HttpResponse('Hi')


@site.admin_view
def changelist(request, object_type):
    from django.http import HttpResponse
    return HttpResponse('Hi changelist')
