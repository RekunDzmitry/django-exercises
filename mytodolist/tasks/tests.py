from django.test import TestCase
from .models import Task
from django.urls import reverse
from django.contrib.auth.models import User
from .forms import TaskForm

# Create your tests here.
class TasksTestCase(TestCase):
    def setUp(self):
        self.user   = User.objects.create_user(username='testuser', password='testpass')
        self.task1  = Task.objects.create(description="Task 1")
        self.task2  = Task.objects.create(description="Task 2")
        self.url    = reverse('task_edit', kwargs={'pk': self.task1.pk})
    
    def tearDown(self):
        Task.objects.all().delete()

    def test_task_list_view_with_no_tasks(self):
        Task.objects.all().delete()
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No tasks found.")
        self.assertQuerysetEqual(response.context['tasks'], [])
    
    def test_task_list_view_with_tasks(self):
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(
            [str(task) for task in response.context['tasks']],
            ['Task 1', 'Task 2']
        )

    def test_task_list_view_uses_correct_template(self):
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tasks/task_list.html')

    def test_task_detail_view_with_valid_task(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('task_detail', args=[self.task1.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.task1.description)

    def test_task_detail_view_with_invalid_task(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('task_detail', args=[100]))
        self.assertEqual(response.status_code, 404)

    def test_task_add_view_with_valid_form(self):
        form_data = {'description': 'New task'}
        response = self.client.post(reverse('task_add'), form_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Task.objects.count(), 3)
        task = Task.objects.filter(description='New task').first()
        self.assertEqual(task.description, 'New task')
        self.assertRedirects(response, reverse('task_list'))

    def test_task_add_view_with_invalid_form(self):
        form_data = {'description': ''}
        response = self.client.post(reverse('task_add'), form_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Task.objects.count(), 2)
        self.assertIsInstance(response.context['form'], TaskForm)
        self.assertContains(response, "This field is required.")

    def test_task_add_view_with_get_request(self):
        response = self.client.get(reverse('task_add'))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], TaskForm)

    def test_task_edit_view_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tasks/task_form.html')
        self.assertIsInstance(response.context['form'], TaskForm)
        self.assertEqual(response.context['form'].instance, self.task1)

    def test_task_edit_view_post(self):
        data = {'description': 'Updated Task'}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('task_detail', kwargs={'pk': self.task1.pk}))
        self.task1.refresh_from_db()
        self.assertEqual(self.task1.description, 'Updated Task')
    
    def test_task_delete_view_with_valid_task(self):
        response = self.client.post(reverse('task_delete', args=[self.task1.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('task_list'))
        self.assertFalse(Task.objects.filter(pk=self.task1.pk).exists())

    def test_task_delete_view_with_invalid_task(self):
        response = self.client.post(reverse('task_delete', args=[100]))
        self.assertEqual(response.status_code, 404)

    def test_task_complete_marks_task_as_completed(self):
        url = reverse('task_list')
        response = self.client.get(url)
        self.assertContains(response, self.task1.description)
        self.assertContains(response, '<input type="checkbox"')
        
        # Make a POST request to the url for marking the task as complete
        complete_url = reverse('task_complete', args=[self.task1.pk])
        self.client.post(complete_url)
        self.task1.refresh_from_db()
        self.assertTrue(self.task1.completed)
        response = self.client.get(url)

        self.assertContains(response, '<input type="checkbox" checked')
