from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic.edit import CreateView, FormView, UpdateView

from pledgetovote.forms import AddressForm, LocationForm, PledgeForm
from pledgetovote.models import Address, Location, Pledge


"""Renders a form that can be used to either create or update a Pledge."""
class CreateUpdateFormMixin(FormView):
    model = Pledge
    form_class = PledgeForm
    exclude = ['address']
    verb = 'Update'

    def post(self, request, *args, **kwargs):
        self.object = None
        pledge_form = self.get_form()
        address_form = AddressForm(request.POST)

        if address_form.is_valid() and pledge_form.is_valid():
            address = address_form.save(commit=False)
            address.save()
            pledge = pledge_form.save(commit=False)
            pledge.address = address
            pledge.location = Location.objects.get(id=request.session['location_id'])
            pledge.save()

            self.object = pledge

            return HttpResponseRedirect(self.get_success_url())

        return self.render_to_response(self.get_context_data(form=pledge_form))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['verb'] = self.verb

        address_form = AddressForm()
        if self.object:
            address = Address.objects.get(id=self.object.address.id)
            address_form = AddressForm(instance=address)

        context.update(address_form=address_form)

        return context

    def get_success_url(self):
        return reverse('pledgetovote:pledge_edit', kwargs={'pk': self.object.id})


"""The view where new Pledges can be created."""
class CreatePledge(CreateUpdateFormMixin, CreateView):
    verb = 'Create'


"""The view where existing Pledges can be updated."""
class UpdatePledge(CreateUpdateFormMixin, UpdateView):
    verb = 'Update'


"""
Anyone who visits the homepage is rerouted to the SetLocation view if their location_id cookie isn't
set.
"""
def reroute(request):
    location_cookie = request.session.get('location', None)
    if location_cookie:
        return redirect('pledgetovote:pledge_new')
    return redirect('pledgetovote:set_location')


"""
The view where users can set their Location, either by choosing an existing Location or creating a
new one.
"""
class SetLocation(FormView):
    model = Location
    form_class = LocationForm
    template_name = 'pledgetovote/set_location.html'

    def post(self, request, *args, **kwargs):
        self.object = None
        location_form = self.get_form()

        if location_form.is_valid():
            new_location = location_form.cleaned_data.get('new_location')
            selected_location_id = location_form.cleaned_data.get('select_location')

            # If the user entered a new location, create it and point their location_id cookie to it
            if new_location:
                location = Location(name=new_location)
                location.save()
            else:
                location = Location.objects.get(id=selected_location_id)

            request.session['location_id'] = location.id  # Set the location_id cookie
            request.session.set_expiry(60 * 60 * 24)  # Expire in 24 hours
            self.object = location

            return redirect('pledgetovote:pledge_new')

        return self.render_to_response(self.get_context_data(form=location_form))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        location_id = self.request.session.get('location_id')

        # If the user's location_id cookie is set, make that location the default value for the
        # select_location form field
        if location_id:
            context['form'].initial['select_location'] = location_id

        return context