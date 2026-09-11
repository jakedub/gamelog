# backend/core/urls.py
from django.contrib import admin
from django.urls import path
from strawberry.django.views import GraphQLView
from games.graphql.schema import schema

urlpatterns = [
    path('admin/', admin.site.urls),
    # Sync view: queries/mutations in games/graphql use plain Django ORM
    # calls, which raise SynchronousOnlyOperation under AsyncGraphQLView.
    # Switch to AsyncGraphQLView only once resolvers are async / wrapped
    # in sync_to_async.
    path('graphql/', GraphQLView.as_view(schema=schema, graphql_ide='graphiql')),
]