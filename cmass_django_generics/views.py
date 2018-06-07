from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.generic.base import ContextMixin, TemplateResponseMixin, ImproperlyConfigured
from django.views.generic.edit import DeleteView, FormView


class CmassContextMixin(ContextMixin):
    title = None
    navigation_buttons = None
    navigation_template = None
    active_tab = None
    active_link = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.get_title():
            controls = context.get('controls', {})
            controls.update({'form_title': self.get_title()})
            context['controls'] = controls

        if self.get_navigation_buttons():
            controls = context.get('controls', {})
            controls.update({'buttons': self.get_navigation_buttons()})
            context['controls'] = controls

        if self.navigation_template:
            context['navigation_template'] = self.navigation_template

        if self.get_active_tab():
            context['active_tab'] = self.get_active_tab()

        if self.get_active_link():
            context['active_link'] = self.get_active_link()

        return context

    def get_title(self):
        return self.title

    def get_navigation_buttons(self):
        return self.navigation_buttons

    def get_active_tab(self):
        return self.active_tab

    def get_active_link(self):
        return self.active_link


class AjaxTemplateResponseMixin(TemplateResponseMixin):
    modal_id = None
    modal_footer_controls = None
    modal_navigation_template = 'cmass_django_generics/ajax_modal.html'
    modal_redirect_url = None

    def dispatch(self, request, *args, **kwargs):
        if not self.get_modal_id():
            raise ImproperlyConfigured("AjaxTemplateResponseMixin required modal_id attribute")
        self.request = request
        return super().dispatch(request, *args, **kwargs)

    def render_to_response(self, context, **response_kwargs):
        if self.request.is_ajax():
            return self.show_modal(context)
        return super().render_to_response(context, **response_kwargs)

    def get_modal_context_data(self, context):
        context['modal_footer_controls'] = self.get_modal_footer_controls()
        if 'submit_button' in context and context['modal_footer_controls']:
            context.pop('submit_button')

        if 'cancel_url' in context:
            context['modal_footer_controls'].insert(0, {
                'class': 'btn btn-default cancel-modal',
                'link': '#',
                'text': 'Close'
            })
        context['template_id'] = self.get_modal_id()
        context['navigation_template'] = self.get_modal_navigation_template()

        return context

    def get_modal_id(self):
        return self.modal_id

    def get_modal_footer_controls(self):
        controls = []
        if self.modal_footer_controls:
            controls = self.modal_footer_controls
        return controls

    def get_modal_navigation_template(self):
        return self.modal_navigation_template

    def get_modal_redirect_url(self):
        return self.modal_redirect_url

    def render_modal(self, context):
        return JsonResponse({
            'modal': render_to_string(
                template_name=self.template_name,
                context=context,
                request=self.request,
            ),
            'template_selector': "#%s" % self.modal_id
        })

    def show_modal(self, context):
        return self.render_modal(self.get_modal_context_data(context))

    def close_modal(self):
        result = {'close_modal': True}
        if self.get_modal_redirect_url():
            result['redirect'] = self.get_modal_redirect_url()

        return JsonResponse(result)


class CmassFormViewMixin(AjaxTemplateResponseMixin):
    submit_button = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['submit_button'] = self.submit_button
        return context


class CmassDeleteView(AjaxTemplateResponseMixin, DeleteView):
    submit_button = True
    post_url = False
    cancel_url = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['submit_button'] = self.submit_button
        if self.get_post_url():
            context['post_url'] = self.get_post_url()
        if self.get_cancel_url():
            context['cancel_url'] = self.get_cancel_url()
        return context

    def get_post_url(self):
        return self.post_url

    def get_cancel_url(self):
        return self.get_cancel_url()

    def get_modal_redirect_url(self):
        return self.get_success_url()

    def get_modal_footer_controls(self):
        controls = super().get_modal_footer_controls()
        controls.extend([{
            'id': 'deleteButton',
            'class': 'btn btn-danger modal-submit',
            'link': self.get_post_url(),
            'text': 'Delete'
        }])
        return controls

    def delete(self, request, *args, **kwargs):
        result = super().delete(request, *args, **kwargs)
        if request.is_ajax():
            return self.close_modal()
        return result
