"""
Views for the Recipe API
"""

from rest_framework import (
    viewsets,
    mixins,
    status,
)

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import (
    Recipe,
    Tag,
    Ingredient,
)

from . import serializers


class RecipeViewSet(viewsets.ModelViewSet):
    """
    View for manage recipe apis
    """

    serializer_class = serializers.RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Retrieve recipes for authenticated user.
        """

        return self.queryset.filter(user=self.request.user).order_by('-id')

    def get_serializer_class(self):
        """
        Return appropriate serializer class.
        """

        if self.action == 'list':
            return serializers.RecipeSerializer
        elif self.action == 'upload_image':
            return serializers.RecipeImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """
        Create a new recipe.
        """

        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """
        Upload an image to a recipe.
        """

        recipe = self.get_object()
        serializer = self.get_serializer(
            recipe,
            data=request.data,
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


class BaseRecipeAttrViewSet(mixins.ListModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.DestroyModelMixin,
                            viewsets.GenericViewSet):
    authentication_classes = [TokenAuthentication]
    http_method_names = ["get", "patch", "delete"]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return objects for the current authenticated user only.
        """

        return self.queryset.filter(user=self.request.user).order_by('-name')


class TagViewSet(BaseRecipeAttrViewSet):
    """
    Manage tags in the database
    """

    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(BaseRecipeAttrViewSet):
    """
    Manage ingredients in the database
    """

    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()
