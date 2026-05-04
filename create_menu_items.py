import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from menu.models import MenuItem

# Create menu items
home = MenuItem.objects.create(title='Home', url='/', order=1)
about = MenuItem.objects.create(title='About', url='/about/', order=2)
services = MenuItem.objects.create(title='Services', url='/services/', order=3)
contact = MenuItem.objects.create(title='Contact', url='/contact/', order=4)

# Create submenu items under Services
consulting = MenuItem.objects.create(title='Consulting', url='/services/consulting/', order=3, parent=services)

print("Menu items created successfully!")
print(f"Total menu items: {MenuItem.objects.count()}")
