from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from apps.users.models import CustomUser
from apps.teams.models import Team, TeamMembership
from apps.channels.models import Channel, ChannelMembership
from django.core.cache import cache

class ChannelTests(APITestCase):
    def setUp(self):
        # 1. Создаем тестовых пользователей
        self.team_owner = CustomUser.objects.create_user(email='owner@test.com', password='password123', first_name='Owner', last_name='User')
        self.team_member = CustomUser.objects.create_user(email='member@test.com', password='password123', first_name='Member', last_name='User')
        self.outsider = CustomUser.objects.create_user(email='outsider@test.com', password='password123', first_name='Outsider', last_name='User')

        # 2. Создаем команду и добавляем участников
        self.team = Team.objects.create(name='Test Team', owner=self.team_owner)
        TeamMembership.objects.create(team=self.team, user=self.team_owner, role='admin')
        TeamMembership.objects.create(team=self.team, user=self.team_member, role='member')

        # 3. Создаем публичный и приватный каналы
        self.public_channel = Channel.objects.create(name='general', team=self.team, is_private=False)
        self.private_channel = Channel.objects.create(name='secret', team=self.team, is_private=True)
        
        # 4. Добавляем владельца в приватный канал
        ChannelMembership.objects.create(channel=self.private_channel, user=self.team_owner)

        # Базовый URL для роутера
        self.list_url = reverse('channel-list') 

    def get_detail_url(self, channel_id):
        return reverse('channel-detail', kwargs={'pk': channel_id})

    def get_members_url(self, channel_id):
        return reverse('channel-members', kwargs={'pk': channel_id})

    # =================================================================
    # GET /api/channels/?team_id={id}
    # =================================================================
    
    def test_list_channels_success(self):
        """Успешное получение списка каналов (пользователь видит публичные + свои приватные)"""
        self.client.force_authenticate(user=self.team_owner)
        response = self.client.get(self.list_url, {'team_id': self.team.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_list_channels_without_team_id(self):
        """Ошибка: запрос списка каналов без team_id"""
        self.client.force_authenticate(user=self.team_owner)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_channels_non_existent_team(self):
        """Запрос для несуществующей команды возвращает пустой список"""
        self.client.force_authenticate(user=self.team_owner)
        response = self.client.get(self.list_url, {'team_id': 9999})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    # =================================================================
    # POST /api/channels/
    # =================================================================

    def test_create_channel_success(self):
        """Успешное создание канала"""
        self.client.force_authenticate(user=self.team_member)
        data = {'name': 'new-channel', 'team': self.team.id, 'is_private': False}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_channel_duplicate_name(self):
        """Ошибка: дубликат имени канала в рамках одной команды"""
        self.client.force_authenticate(user=self.team_owner)
        data = {'name': 'general', 'team': self.team.id} # 'general' уже создан в setUp
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_channel_no_access_to_team(self):
        """Ошибка: создание канала в команде, где пользователь не состоит"""
        self.client.force_authenticate(user=self.outsider)
        data = {'name': 'hacked-channel', 'team': self.team.id}
        response = self.client.post(self.list_url, data, format='json')
        # Ожидаем ошибку валидации
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # =================================================================
    # GET /api/channels/{id}/
    # =================================================================

    def test_retrieve_public_channel(self):
        """Просмотр публичного канала участником команды"""
        self.client.force_authenticate(user=self.team_member)
        response = self.client.get(self.get_detail_url(self.public_channel.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_private_channel_with_access(self):
        """Просмотр приватного канала участником этого канала"""
        self.client.force_authenticate(user=self.team_owner)
        response = self.client.get(self.get_detail_url(self.private_channel.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_private_channel_without_access(self):
        """Ошибка: доступ к приватному каналу без членства в нем"""
        self.client.force_authenticate(user=self.team_member)
        response = self.client.get(self.get_detail_url(self.private_channel.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # =================================================================
    # PATCH /api/channels/{id}/
    # =================================================================

    def test_patch_channel_success(self):
        """Успешное обновление канала"""
        self.client.force_authenticate(user=self.team_owner)
        data = {'name': 'updated-general'}
        response = self.client.patch(self.get_detail_url(self.public_channel.id), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['name'], 'updated-general')

    def test_patch_channel_duplicate_name(self):
        """Ошибка обновления: имя уже занято другим каналом в этой команде"""
        self.client.force_authenticate(user=self.team_owner)
        data = {'name': 'secret'} # 'secret' занято другим каналом
        response = self.client.patch(self.get_detail_url(self.public_channel.id), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_channel_no_rights(self):
        """Ошибка: попытка изменения чужого канала (нет прав)"""
        self.client.force_authenticate(user=self.outsider)
        data = {'name': 'hacked'}
        response = self.client.patch(self.get_detail_url(self.public_channel.id), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # =================================================================
    # DELETE /api/channels/{id}/
    # =================================================================

    def test_delete_channel_success(self):
        """Успешное удаление канала"""
        self.client.force_authenticate(user=self.team_owner)
        response = self.client.delete(self.get_detail_url(self.public_channel.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_channel_non_existent(self):
        """Ошибка: удаление несуществующего канала"""
        self.client.force_authenticate(user=self.team_owner)
        response = self.client.delete(self.get_detail_url(9999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_channel_no_rights(self):
        """Ошибка: удаление канала пользователем без доступа (Outsider)"""
        self.client.force_authenticate(user=self.outsider)
        response = self.client.delete(self.get_detail_url(self.public_channel.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # =================================================================
    # POST /api/channels/{id}/members/
    # =================================================================

    def test_add_member_success(self):
        """Успешное добавление участника в приватный канал"""
        self.client.force_authenticate(user=self.team_owner)
        data = {'user': self.team_member.id}
        response = self.client.post(self.get_members_url(self.private_channel.id), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_add_member_repeated(self):
        """Ошибка: повторное добавление пользователя в канал"""
        self.client.force_authenticate(user=self.team_owner)
        data = {'user': self.team_owner.id} # Пользователь уже добавлен в setUp
        response = self.client.post(self.get_members_url(self.private_channel.id), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_member_not_in_team(self):
        """Ошибка: добавление в канал пользователя, которого нет в команде"""
        self.client.force_authenticate(user=self.team_owner)
        data = {'user': self.outsider.id}
        response = self.client.post(self.get_members_url(self.private_channel.id), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # =================================================================
    # GET /api/channels/{id}/members/
    # =================================================================

    def test_get_members_success(self):
        """Успешное получение списка участников приватного канала"""
        self.client.force_authenticate(user=self.team_owner)
        response = self.client.get(self.get_members_url(self.private_channel.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_get_members_only_private(self):
        """Ошибка: попытка получить список участников для публичного канала"""
        self.client.force_authenticate(user=self.team_owner)
        response = self.client.get(self.get_members_url(self.public_channel.id))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_channel_list_caching(self):
        """Проверка работы кэширования для списка каналов"""
        self.client.force_authenticate(user=self.team_owner)
        
        # 1. Очищаем кэш перед тестом на всякий случай
        cache.clear()

        # 2. Первый запрос: данные берутся из БД. Замеряем количество SQL запросов.
        with self.assertNumQueries(4): # Число 6 может отличаться в зависимости от вашего кода, подгоните его, посмотрев, сколько запросов идет реально
            response1 = self.client.get(self.list_url, {'team_id': self.team.id})
        
        self.assertEqual(response1.status_code, 200)

        # 3. Второй запрос: данные должны взяться из кэша. Количество SQL запросов к таблицам каналов должно быть 0 (или только запросы на авторизацию пользователя/сессию).
        with self.assertNumQueries(0): # В идеале 0, если пользователь тоже закэширован, или 1-2 на проверку сессии/юзера.
            response2 = self.client.get(self.list_url, {'team_id': self.team.id})
        
        self.assertEqual(response1.data, response2.data) # Данные должны совпадать

    def test_channel_cache_invalidation(self):
        """Проверка очистки кэша при обновлении"""
        self.client.force_authenticate(user=self.team_owner)
        cache.clear()

        # 1. Генерируем кэш (передаем параметры запроса)
        self.client.get(self.list_url, {'team_id': self.team.id})
        
        # 2. Формируем правильный ключ, который ожидает кэш
        # Строка запроса будет выглядеть как team_id=1 (или другой ID)
        query_string = f"team_id={self.team.id}"
        cache_key = f"channels_team_{self.team.id}_user_{self.team_owner.id}_params_{query_string}"
        
        # Убеждаемся, что ключ есть в кэше
        self.assertIsNotNone(
            cache.get(cache_key), 
            "Кэш не был создан. Возможно ключ сформирован неправильно."
        )

        # 3. Обновляем канал (это должно вызвать инвалидацию кэша)
        data = {'name': 'new-name'}
        self.client.patch(self.get_detail_url(self.public_channel.id), data)

        # 4. Проверяем, что кэш удален
        self.assertIsNone(
            cache.get(cache_key),
            "Кэш не был очищен после обновления. Проверьте функцию инвалидации кэша."
        )