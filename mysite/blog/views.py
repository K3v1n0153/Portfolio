from django.shortcuts import render, get_object_or_404, redirect
from blog.models import Post, Comment
from blog.forms import PostForm, CommentForm, UserForm, UserProfileInfoForm
from django.utils import timezone
from django.urls import reverse, reverse_lazy
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.views.generic import (TemplateView,
								  ListView,
								  DetailView,
								  CreateView,
								  UpdateView,
								  DeleteView)

class AboutView(TemplateView):

	template_name = 'blog/about.html'

class PostListView(ListView):

	model = Post 

	def get_queryset(self):
		return Post.objects.filter(published_date__lte=timezone.now()).order_by('-published_date')

class PostDetailView(DetailView):

	model = Post 

class CreatePostView(LoginRequiredMixin, CreateView):

	model = Post 
	form_class = PostForm
	login_url = '/login/'
	redirect_field_name = 'blog/post_detail.html'

	def form_valid(self, form):

		form.instance.author = self.request.user 
		return super().form_valid(form)

class PostUpdateView(LoginRequiredMixin, UpdateView):

	model = Post 
	form_class = PostForm
	login_url = '/login/'
	redirect_field_name = 'blog/post_detail.html'

class PostDeleteView(LoginRequiredMixin, DeleteView):

	model = Post 
	success_url = reverse_lazy('post_list')

class DraftListView(LoginRequiredMixin, ListView):

	model = Post 
	login_url = '/login/'
	redirect_field_name = 'blog/post_draft_list.html'

	def get_queryset(self):
		return Post.objects.filter(published_date__isnull=True).order_by('created_date')

#######################################
## Functions that require a pk match ##
#######################################

@login_required
def post_publish(request, pk):

	post = get_object_or_404(Post, pk=pk)
	post.publish()
	return redirect('post_detail', pk=pk)

@login_required
def add_comment_to_post(request, pk):

	post = get_object_or_404(Post, pk=pk)

	if request.method == "POST":
		form = CommentForm(request.POST)

		if form.is_valid():

			comment = form.save(commit=False)
			comment.post = post 
			comment.save()
			return redirect('post_detail', pk=post.pk)

	else:
		form = CommentForm()

	return render(request, 'blog/comment_form.html', {'form': form})

@login_required
def comment_approve(request, pk):

	comment = get_object_or_404(Comment, pk=pk)
	comment.approve()
	return redirect('post_detail', pk=comment.post.pk)

@login_required
def comment_remove(request, pk):

	comment = get_object_or_404(Comment, pk=pk)
	post_pk = comment.post.pk 
	comment.delete()
	return redirect('post_detail', pk=post_pk)

#######################################
##  User Registration, Login, Logout ##
#######################################

def register(request):

	registered = False

	if request.method == "POST":

		user_form = UserForm(data=request.POST)
		profile_form = UserProfileInfoForm(data=request.POST)

		if user_form.is_valid() and profile_form.is_valid():

			print("VALIDATION SUCCESS")
			print(f"Username: {user_form.cleaned_data['username']}")
			print(f"First Name: {user_form.cleaned_data['first_name']}")
			print(f"Last Name: {user_form.cleaned_data['last_name']}")
			print(f"Email: {user_form.cleaned_data['email']}")
			print(f"Password: {user_form.cleaned_data['password']}")

			user = user_form.save()
			user.set_password(user.password)
			user.save()

			profile = profile_form.save(commit=False)
			profile.user = user

			if 'profile_picture' in request.FILES:
				profile.profile_picture = request.FILES['profile_picture']

			profile.save()
			registered = True

		else:
			print(user_form.errors, profile_form.errors)

	else:

		user_form = UserForm()
		profile_form = UserProfileInfoForm()

	return render(request, 'registration/registration.html', {'user_form': user_form,
															  'profile_form': profile_form,
															  'registered': registered})

def user_login(request):

	if request.method == "POST":

		username = request.POST.get('username')
		password = request.POST.get('password')

		user = authenticate(username=username, password=password)

		if user:

			if user.is_active:

				login(request, user)
				return HttpResponseRedirect(reverse('post_list'))

			else:
				return HttpResponse("ACCOUNT NOT ACTIVE!")

		else:

			print("Someone tried to access account but it failed")
			print(f"Username: {username} and Password: {password}")
			return HttpResponse("Invalid logged in details supplied")

	else:
		return render(request, 'registration/login.html')

@login_required
def user_logout(request):

	logout(request)
	return HttpResponseRedirect(reverse('post_list'))