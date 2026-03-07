"""Tests for sandbox_router.py.

This module tests the sandbox router endpoints, focusing on:
- Webhook base URL derivation from incoming requests
- Parameter passing to sandbox service
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import Request
from starlette.datastructures import URL

from openhands.app_server.sandbox.sandbox_models import SandboxInfo, SandboxStatus
from openhands.app_server.sandbox.sandbox_router import start_sandbox


class TestStartSandboxEndpoint:
    """Tests for the start_sandbox endpoint."""

    @pytest.mark.asyncio
    async def test_start_sandbox_derives_webhook_base_url_from_request(self):
        """Test that webhook_base_url is derived from the incoming request."""
        # Arrange
        mock_request = MagicMock(spec=Request)
        mock_request.base_url = URL('http://localhost:3030/')

        mock_sandbox_service = AsyncMock()
        mock_sandbox_info = SandboxInfo(
            id='test-sandbox-123',
            created_by_user_id='user-123',
            sandbox_spec_id='test-image:latest',
            status=SandboxStatus.STARTING,
            session_api_key='test-session-key',
            exposed_urls=None,
            created_at=datetime.now(timezone.utc),
        )
        mock_sandbox_service.start_sandbox.return_value = mock_sandbox_info

        # Act
        result = await start_sandbox(
            request=mock_request,
            sandbox_spec_id=None,
            sandbox_service=mock_sandbox_service,
        )

        # Assert
        mock_sandbox_service.start_sandbox.assert_called_once_with(
            sandbox_spec_id=None,
            webhook_base_url='http://localhost:3030',
        )
        assert result == mock_sandbox_info

    @pytest.mark.asyncio
    async def test_start_sandbox_passes_sandbox_spec_id(self):
        """Test that sandbox_spec_id is passed to the service."""
        # Arrange
        mock_request = MagicMock(spec=Request)
        mock_request.base_url = URL('https://app.example.com/')

        mock_sandbox_service = AsyncMock()
        mock_sandbox_info = SandboxInfo(
            id='test-sandbox-456',
            created_by_user_id='user-456',
            sandbox_spec_id='custom-image:v2',
            status=SandboxStatus.STARTING,
            session_api_key='test-session-key',
            exposed_urls=None,
            created_at=datetime.now(timezone.utc),
        )
        mock_sandbox_service.start_sandbox.return_value = mock_sandbox_info

        # Act
        result = await start_sandbox(
            request=mock_request,
            sandbox_spec_id='custom-image:v2',
            sandbox_service=mock_sandbox_service,
        )

        # Assert
        mock_sandbox_service.start_sandbox.assert_called_once_with(
            sandbox_spec_id='custom-image:v2',
            webhook_base_url='https://app.example.com',
        )
        assert result.sandbox_spec_id == 'custom-image:v2'

    @pytest.mark.asyncio
    async def test_start_sandbox_strips_trailing_slash_from_base_url(self):
        """Test that trailing slash is stripped from the webhook base URL."""
        # Arrange
        mock_request = MagicMock(spec=Request)
        mock_request.base_url = URL('http://localhost:8080/')  # Has trailing slash

        mock_sandbox_service = AsyncMock()
        mock_sandbox_info = SandboxInfo(
            id='test-sandbox',
            created_by_user_id=None,
            sandbox_spec_id='test-image',
            status=SandboxStatus.STARTING,
            session_api_key=None,
            exposed_urls=None,
            created_at=datetime.now(timezone.utc),
        )
        mock_sandbox_service.start_sandbox.return_value = mock_sandbox_info

        # Act
        await start_sandbox(
            request=mock_request,
            sandbox_spec_id=None,
            sandbox_service=mock_sandbox_service,
        )

        # Assert - webhook_base_url should not have trailing slash
        call_kwargs = mock_sandbox_service.start_sandbox.call_args[1]
        assert call_kwargs['webhook_base_url'] == 'http://localhost:8080'
        assert not call_kwargs['webhook_base_url'].endswith('/')
