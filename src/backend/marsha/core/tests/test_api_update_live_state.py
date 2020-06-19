"""Tests for the live update state API of the Marsha project."""
import json
import random

from django.test import TestCase, override_settings

from ..defaults import IDLE, LIVE, LIVE_CHOICES, STOPPED
from ..factories import VideoFactory


class UpdateLiveStateAPITest(TestCase):
    """Test the API that allows to update video live state."""

    @override_settings(UPDATE_STATE_SHARED_SECRETS=["shared secret"])
    def test_update_live_state(self):
        """Confirm update video live state."""
        video = VideoFactory(
            id="a1a21411-bf2f-4926-b97f-3c48a124d528",
            upload_state=LIVE,
            live_state=IDLE,
        )
        data = {
            "key": video.pk,
            "state": "live",
        }
        response = self.client.post(
            "/api/update-live-state",
            data,
            content_type="application/json",
            HTTP_X_MARSHA_SIGNATURE=(
                "5f5698f31efb97df5474f54ccd93319f55a424fbd87b1086696a190dad0daddb"
            ),
        )
        video.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {"success": True})
        self.assertEqual(video.live_state, LIVE)

    @override_settings(UPDATE_STATE_SHARED_SECRETS=["shared secret"])
    def test_update_live_state_invalid_signature(self):
        """Live state update with an invalid signature should fails."""
        video = VideoFactory(
            id="a1a21411-bf2f-4926-b97f-3c48a124d528",
            upload_state=LIVE,
            live_state=IDLE,
        )
        data = {
            "key": video.pk,
            "state": "live",
        }
        response = self.client.post(
            "/api/update-live-state",
            data,
            content_type="application/json",
            HTTP_X_MARSHA_SIGNATURE=("invalid signature"),
        )
        video.refresh_from_db()

        self.assertEqual(response.status_code, 403)
        self.assertEqual(video.live_state, IDLE)

    def test_update_live_state_invalid_state(self):
        """Live state update with an invalid state should fails."""
        video = VideoFactory(
            id="a1a21411-bf2f-4926-b97f-3c48a124d528",
            upload_state=LIVE,
            live_state=IDLE,
        )
        invalid_state = random.choice(
            [s[0] for s in LIVE_CHOICES if s[0] not in [LIVE, STOPPED]]
        )
        data = {
            "key": video.pk,
            "state": invalid_state,
        }
        response = self.client.post(
            "/api/update-live-state",
            data,
            content_type="application/json",
            HTTP_X_MARSHA_SIGNATURE=(
                "5f5698f31efb97df5474f54ccd93319f55a424fbd87b1086696a190dad0daddb"
            ),
        )
        video.refresh_from_db()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(video.live_state, IDLE)
        self.assertEqual(
            json.loads(response.content),
            {"state": [f'"{invalid_state}" is not a valid choice.']},
        )

    @override_settings(UPDATE_STATE_SHARED_SECRETS=["shared secret"])
    def test_update_live_state_unknown_video(self):
        """Confirm update video live state."""
        data = {
            "key": "a1a21411-bf2f-4926-b97f-3c48a124d528",
            "state": "live",
        }
        response = self.client.post(
            "/api/update-live-state",
            data,
            content_type="application/json",
            HTTP_X_MARSHA_SIGNATURE=(
                "5f5698f31efb97df5474f54ccd93319f55a424fbd87b1086696a190dad0daddb"
            ),
        )

        self.assertEqual(response.status_code, 404)
