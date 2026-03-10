import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import SecretStr

from openhands.core.config.openhands_config import OpenHandsConfig
from openhands.server.settings import Settings
from openhands.storage.data_models.settings import Settings as DataSettings

# Mock the database module before importing
with patch('storage.database.a_session_maker'):
    from server.constants import (
        LITE_LLM_API_URL,
    )
    from storage.saas_settings_store import SaasSettingsStore
    from storage.user_settings import UserSettings


@pytest.fixture
def mock_config():
    config = MagicMock(spec=OpenHandsConfig)
    config.jwt_secret = SecretStr('test_secret')
    config.file_store = 'google_cloud'
    config.file_store_path = 'bucket'
    return config


@pytest.fixture
def settings_store(async_session_maker, mock_config):
    store = SaasSettingsStore('5594c7b6-f959-4b81-92e9-b09c206f5081', mock_config)
    store.a_session_maker = async_session_maker

    # Patch the load method to read from UserSettings table directly (for testing)
    async def patched_load():
        async with store.a_session_maker() as session:
            from sqlalchemy import select

            result = await session.execute(
                select(UserSettings).filter(
                    UserSettings.keycloak_user_id == store.user_id
                )
            )
            user_settings = result.scalars().first()
            if not user_settings:
                # Return default settings
                return Settings(
                    llm_api_key=SecretStr('test_api_key'),
                    llm_base_url='http://test.url',
                    agent='CodeActAgent',
                    language='en',
                )

            # Decrypt and convert to Settings
            kwargs = {}
            for column in UserSettings.__table__.columns:
                if column.name != 'keycloak_user_id':
                    value = getattr(user_settings, column.name, None)
                    if value is not None:
                        kwargs[column.name] = value

            store._decrypt_kwargs(kwargs)
            settings = Settings(**kwargs)
            settings.email = 'test@example.com'
            settings.email_verified = True
            return settings

    # Patch the store method to write to UserSettings table directly (for testing)
    async def patched_store(item):
        if item:
            # Make a copy of the item without email and email_verified
            item_dict = item.model_dump(context={'expose_secrets': True})
            if 'email' in item_dict:
                del item_dict['email']
            if 'email_verified' in item_dict:
                del item_dict['email_verified']
            if 'secrets_store' in item_dict:
                del item_dict['secrets_store']

            # Encrypt the data before storing
            store._encrypt_kwargs(item_dict)

            # Continue with the original implementation
            from sqlalchemy import select

            async with store.a_session_maker() as session:
                result = await session.execute(
                    select(UserSettings).filter(
                        UserSettings.keycloak_user_id == store.user_id
                    )
                )
                existing = result.scalars().first()

                if existing:
                    # Update existing entry
                    for key, value in item_dict.items():
                        if key in existing.__class__.__table__.columns:
                            setattr(existing, key, value)
                    await session.merge(existing)
                else:
                    item_dict['keycloak_user_id'] = store.user_id
                    settings = UserSettings(**item_dict)
                    session.add(settings)
                await session.commit()

    # Replace the methods with our patched versions
    store.store = patched_store
    store.load = patched_load
    return store


@pytest.mark.asyncio
async def test_store_and_load_keycloak_user(settings_store):
    # Set a UUID-like Keycloak user ID
    settings_store.user_id = '550e8400-e29b-41d4-a716-446655440000'
    settings = Settings(
        llm_api_key=SecretStr('secret_key'),
        llm_base_url=LITE_LLM_API_URL,
        agent='smith',
        email='test@example.com',
        email_verified=True,
    )

    await settings_store.store(settings)

    # Load and verify settings
    loaded_settings = await settings_store.load()
    assert loaded_settings is not None
    assert loaded_settings.llm_api_key.get_secret_value() == 'secret_key'
    assert loaded_settings.agent == 'smith'

    # Verify it was stored in user_settings table with keycloak_user_id
    from sqlalchemy import select

    async with settings_store.a_session_maker() as session:
        result = await session.execute(
            select(UserSettings).filter(
                UserSettings.keycloak_user_id == '550e8400-e29b-41d4-a716-446655440000'
            )
        )
        stored = result.scalars().first()
        assert stored is not None
        assert stored.agent == 'smith'


@pytest.mark.asyncio
async def test_load_returns_default_when_not_found(settings_store, async_session_maker):
    file_store = MagicMock()
    file_store.read.side_effect = FileNotFoundError()

    with (
        patch('storage.saas_settings_store.a_session_maker', async_session_maker),
    ):
        loaded_settings = await settings_store.load()
        assert loaded_settings is not None
        assert loaded_settings.language == 'en'
        assert loaded_settings.agent == 'CodeActAgent'
        assert loaded_settings.llm_api_key.get_secret_value() == 'test_api_key'
        assert loaded_settings.llm_base_url == 'http://test.url'


@pytest.mark.asyncio
async def test_encryption(settings_store):
    settings_store.user_id = '5594c7b6-f959-4b81-92e9-b09c206f5081'  # GitHub user ID
    settings = Settings(
        llm_api_key=SecretStr('secret_key'),
        agent='smith',
        llm_base_url=LITE_LLM_API_URL,
        email='test@example.com',
        email_verified=True,
    )
    await settings_store.store(settings)
    from sqlalchemy import select

    async with settings_store.a_session_maker() as session:
        result = await session.execute(
            select(UserSettings).filter(
                UserSettings.keycloak_user_id == '5594c7b6-f959-4b81-92e9-b09c206f5081'
            )
        )
        stored = result.scalars().first()
        # The stored key should be encrypted
        assert stored.llm_api_key != 'secret_key'
        # But we should be able to decrypt it when loading
        loaded_settings = await settings_store.load()
        assert loaded_settings.llm_api_key.get_secret_value() == 'secret_key'


@pytest.mark.asyncio
async def test_ensure_api_key_keeps_valid_key(mock_config):
    """When the existing key is valid, it should be kept unchanged."""
    store = SaasSettingsStore('test-user-id-123', mock_config)
    existing_key = 'sk-existing-key'
    item = DataSettings(
        llm_model='openhands/gpt-4', llm_api_key=SecretStr(existing_key)
    )

    with patch(
        'storage.saas_settings_store.LiteLlmManager.verify_existing_key',
        new_callable=AsyncMock,
        return_value=True,
    ):
        await store._ensure_api_key(item, 'org-123', openhands_type=True)

        # Key should remain unchanged when it's valid
        assert item.llm_api_key is not None
        assert item.llm_api_key.get_secret_value() == existing_key


@pytest.mark.asyncio
async def test_ensure_api_key_generates_new_key_when_verification_fails(
    mock_config,
):
    """When verification fails, a new key should be generated."""
    store = SaasSettingsStore('test-user-id-123', mock_config)
    new_key = 'sk-new-key'
    item = DataSettings(
        llm_model='openhands/gpt-4', llm_api_key=SecretStr('sk-invalid-key')
    )

    with (
        patch(
            'storage.saas_settings_store.LiteLlmManager.verify_existing_key',
            new_callable=AsyncMock,
            return_value=False,
        ),
        patch(
            'storage.saas_settings_store.LiteLlmManager.generate_key',
            new_callable=AsyncMock,
            return_value=new_key,
        ),
    ):
        await store._ensure_api_key(item, 'org-123', openhands_type=True)

        assert item.llm_api_key is not None
        assert item.llm_api_key.get_secret_value() == new_key


@pytest.mark.asyncio
async def test_store_propagates_llm_settings_to_all_org_members(mock_config):
    """When admin saves LLM settings, all org members should receive the updated settings.

    This test verifies that the store() method executes a bulk UPDATE statement
    to propagate LLM settings to all organization members.
    """
    # Arrange
    org_id = uuid.UUID('11111111-1111-1111-1111-111111111111')
    admin_user_id = uuid.UUID('22222222-2222-2222-2222-222222222222')

    store = SaasSettingsStore(str(admin_user_id), mock_config)

    new_settings = DataSettings(
        llm_model='new-model/gpt-4',
        llm_base_url='http://new-url.com',
        max_iterations=100,
        llm_api_key=SecretStr('new-shared-api-key'),
    )

    # Create mock user and org_member
    mock_user = MagicMock()
    mock_user.current_org_id = org_id
    mock_org_member = MagicMock()
    mock_org_member.org_id = org_id
    mock_org_member.llm_api_key = SecretStr('existing-key')
    mock_user.org_members = [mock_org_member]

    mock_org = MagicMock()
    mock_org.id = org_id

    # Track all execute calls
    execute_calls = []

    # First execute returns user
    user_result = MagicMock()
    user_result.scalars.return_value.first.return_value = mock_user

    # Second execute returns org
    org_result = MagicMock()
    org_result.scalars.return_value.first.return_value = mock_org

    async def mock_execute(stmt):
        execute_calls.append(stmt)
        if len(execute_calls) == 1:
            return user_result
        elif len(execute_calls) == 2:
            return org_result
        return MagicMock()

    # Create mock session with async context manager
    mock_session = MagicMock()
    mock_session.execute = mock_execute
    mock_session.commit = AsyncMock()

    class MockAsyncContextManager:
        async def __aenter__(self):
            return mock_session

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return None

    mock_session_maker = MagicMock(return_value=MockAsyncContextManager())

    # Act
    with patch('storage.saas_settings_store.a_session_maker', mock_session_maker):
        await store.store(new_settings)

    # Assert - verify that a bulk UPDATE was executed for OrgMember
    # The third execute call should be the bulk UPDATE for all org members
    assert (
        len(execute_calls) >= 3
    ), 'Expected at least 3 execute calls (user query, org query, bulk update)'

    # The last execute call before commit should be the bulk UPDATE
    bulk_update_stmt = execute_calls[-1]

    # Verify it's an UPDATE statement targeting OrgMember
    stmt_str = str(bulk_update_stmt)
    assert (
        'UPDATE' in stmt_str.upper() or 'org_member' in stmt_str.lower()
    ), f'Expected bulk UPDATE on org_member table, got: {stmt_str}'
