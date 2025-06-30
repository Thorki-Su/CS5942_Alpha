from django.test import RequestFactory
from views import my_view

factory = RequestFactory()
request = factory.get('/my-view/')  # 构造 GET 请求
response = my_view(request)
print(response.content)