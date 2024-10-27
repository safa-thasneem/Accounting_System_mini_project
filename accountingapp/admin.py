from django.contrib import admin
from accountingapp.models import User, Profile, Category, Item, Parties


admin.site.register(Profile)
admin.site.register(Category)
admin.site.register(Item)
admin.site.register(Parties)

