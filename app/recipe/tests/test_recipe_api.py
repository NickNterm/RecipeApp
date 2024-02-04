"""
Test for recipe API
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient


from core.models import (
    Recipe,
    Tag,
    Ingredient,
)

from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
)

RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    """
    Create and return a recipe detail URL
    """

    return reverse('recipe:recipe-detail', args=[recipe_id])


def create_recipe(user, **params):
    """
    Create and return a sample recipe
    """

    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 22,
        'price': Decimal('5.00'),
        'description': 'Sample description',
        'link': 'http://www.sample.com',
    }

    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


def create_user(**params):
    """
    Create and return a sample user
    """

    return get_user_model().objects.create_user(**params)


class PublicRecipeAPITests(TestCase):
    """
    Test unauthenticated recipe API access
    """

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """
        Test that authentication is required
        """
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    """
    Test authenticated recipe API access
    """

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email='test@example.com',
            password='testpass',
        )

        self.client.force_authenticate(self.user)

    def test_retrive_recipes(self):
        """
        Testing to get a list of recipes
        """

        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')

        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        """
        Test that recipes returned are for the authenticated user
        """

        user2 = create_user(
            email='other@example.com',
            password='testpass',
        )

        create_recipe(user=self.user)
        create_recipe(user=self.user)
        create_recipe(user=user2)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user).order_by('-id')

        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
        self.assertEqual(len(res.data), 2)

    def test_get_recipe_detail(self):
        """
        Test get recipe detail.
        """

        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """
        Test creating recipe
        """

        payload = {
            'title': 'Chocolate cake',
            'time_minutes': 30,
            'price': Decimal('5.00'),
            'description': 'Yummy cake',
            'link': 'http://www.sample.com',
        }

        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])

        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)

        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """
        Test partial update of a recipe
        """

        original_link = 'http://www.sample.com'

        recipe = create_recipe(
            user=self.user,
            title='Chocolate cake',
            link=original_link,
        )

        payload = {'title': 'Chocolate cake updated'}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        """
        Test full update of a recipe
        """

        recipe = create_recipe(
            user=self.user,
            title='Chocolate cake',
            time_minutes=30,
            price=Decimal('5.00'),
            description='Yummy cake',
            link='http://www.sample.com',
        )

        payload = {
            'title': 'Chocolate cake updated',
            'time_minutes': 25,
            'price': Decimal('6.00'),
            'description': 'Yummy cake updated',
            'link': 'http://www.sample.com/updated',
        }

        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()

        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)

        self.assertEqual(recipe.user, self.user)

    def test_update_user_returns_error(self):
        """
        Test changing the recipe user results in an error
        """

        new_user = create_user(
            email='user2@example.com',
            password='testpass',
        )

        recipe = create_recipe(user=self.user)

        payload = {'user': new_user.id}
        url = detail_url(recipe.id)
        self.client.put(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """
        Test deleting a recipe successful
        """

        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_recipe_other_user_recipe_error(self):
        """
        Test deleting a recipe successful
        """

        user2 = create_user(
            email='user2@example.com',
            password='testpass',
        )

        recipe = create_recipe(user=user2)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tags(self):
        """
        Test creating a recipe with a new tag
        """

        payload = {
            'title': 'Chocolate cake',
            'time_minutes': 30,
            'price': Decimal('5.00'),
            'tags': [
                {'name': 'cake'},
                {'name': 'chocolate'}
            ],
        }

        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes.first()
        self.assertEqual(recipe.tags.count(), 2)

        for tag in payload['tags']:
            exitsts = recipe.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exitsts)

    def test_create_recipe_with_existing_tags(self):
        """
        Test creating a recipe with existing tags
        """

        tag1 = Tag.objects.create(user=self.user, name='cake')

        payload = {
            'title': 'Chocolate cake',
            'time_minutes': 30,
            'price': Decimal('5.00'),
            'tags': [
                {'name': 'cake'},
                {'name': 'chocolate'}
            ],
        }

        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes.first()
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag1, recipe.tags.all())

        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """
        Test creating tag when updating a recipe
        """
        recipe = create_recipe(user=self.user)

        payload = {'tags': [{'name': 'cake'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(
            user=self.user,
            name='cake',
        )
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """
        Test assigning tags to recipe
        """

        tag1 = Tag.objects.create(user=self.user, name='cake')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag1)

        tag2 = Tag.objects.create(user=self.user, name='chocolate')
        payload = {'tags': [{'name': 'chocolate'}]}
        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 1)
        self.assertIn(tag2, recipe.tags.all())
        self.assertNotIn(tag1, recipe.tags.all())

    def test_clear_recipe_tags(self):
        """
        Test clearing a recipes tags
        """
        tag = Tag.objects.create(user=self.user, name='cake')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {'tags': []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_new_ingredients(self):
        """
        Test creating a recipe with new ingredients
        """

        payload = {
            'title': 'Chocolate cake',
            'time_minutes': 30,
            'price': Decimal('5.00'),
            'ingredients': [
                {'name': 'flour'},
                {'name': 'sugar'}
            ],
        }

        res = self.client.post(RECIPES_URL, payload, format='json')
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = recipes.first()
        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name=ingredient['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredient(self):
        """
        Test creating a new recipe with ecisting ingredient.
        """
        ingredient = Ingredient.objects.create(user=self.user, name='flour')
        payload = {
            'title': 'Chocolate cake',
            'time_minutes': 30,
            'price': Decimal('5.00'),
            'ingredients': [
                {'name': 'flour'},
                {'name': 'sugar'}
            ],
        }

        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes.first()
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingredient, recipe.ingredients.all())
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name=ingredient['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_ingredient_on_update(self):
        """
        Test create ingredient on update
        """
        recipe = create_recipe(user=self.user)

        payload = {'ingredients': [{'name': 'flour'}]}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_ingredient = Ingredient.objects.get(
            user=self.user,
            name='flour',
        )
        self.assertIn(new_ingredient, recipe.ingredients.all())

    def test_update_recipe_assing_ingredient(self):
        """
        Test assigning ingredients to recipe
        """

        ingredient1 = Ingredient.objects.create(user=self.user, name='flour')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient1)

        self.assertEqual(recipe.ingredients.count(), 1)

        ingredient2 = Ingredient.objects.create(user=self.user, name='sugar')
        payload = {'ingredients': [{'name': 'sugar'}]}
        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient2, recipe.ingredients.all())
        self.assertNotIn(ingredient1, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        """
        Test clearing a recipes ingredients
        """
        ingredient = Ingredient.objects.create(user=self.user, name='flour')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient)

        payload = {'ingredients': []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)
