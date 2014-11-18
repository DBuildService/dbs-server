from __future__ import absolute_import, division, generators, nested_scopes, print_function, unicode_literals, with_statement
from django.core.urlresolvers import reverse
from menu import Menu, MenuItem

Menu.add_item("main", MenuItem("Home",
                               reverse("dbs.web.views.home"),
                               weight=10))

Menu.add_item("main", MenuItem("Tasks",
                               "/tasks",
                               weight=20))

Menu.add_item("main", MenuItem("Images",
                               "/images",
                               weight=30))

Menu.add_item("main", MenuItem("Build a New Image",
                               "/new",
                               weight=40))

Menu.add_item("main", MenuItem("Move Image",
                               "/move",
                               weight=50))
