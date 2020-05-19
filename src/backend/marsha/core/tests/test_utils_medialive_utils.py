"""Test medialive utils functions."""
from unittest import mock

from django.test import TestCase, override_settings

from botocore.stub import ANY, Stubber

from ..utils import medialive_utils


class MediaLiveUtilsTestCase(TestCase):
    """Test medialive utils."""

    maxDiff = None

    def test_get_or_create_input_security_group_create_one(self):
        """Create a security group when no group already exists."""
        list_security_group_response = {"InputSecurityGroups": []}

        created_security_group_response = {
            "SecurityGroup": {
                "Arn": "string",
                "Id": "security_id",
                "Inputs": ["string"],
                "State": "IDLE",
                "Tags": {"marsha_live": "1"},
                "WhitelistRules": [{"Cidr": "0.0.0.0/0"}],
            }
        }

        with Stubber(medialive_utils.medialive_client) as medialive_stubber:
            medialive_stubber.add_response(
                "list_input_security_groups",
                service_response=list_security_group_response,
                expected_params={},
            )
            medialive_stubber.add_response(
                "create_input_security_group",
                service_response=created_security_group_response,
                expected_params={
                    "WhitelistRules": [{"Cidr": "0.0.0.0/0"}],
                    "Tags": {"marsha_live": "1"},
                },
            )

            security_group_id = medialive_utils.get_or_create_input_security_group()

            medialive_stubber.assert_no_pending_responses()

        self.assertEqual("security_id", security_group_id)

    def test_get_or_create_input_security_group_no_matching_tag(self):
        """Create a security group when no matching tag."""
        list_security_group_response = {
            "InputSecurityGroups": [
                {
                    "Arn": "string",
                    "Id": "no_tag_security_group",
                    "Inputs": ["string"],
                    "State": "IDLE",
                    "Tags": {},
                    "WhitelistRules": [{"Cidr": "0.0.0.0/0"}],
                }
            ]
        }

        created_security_group_response = {
            "SecurityGroup": {
                "Arn": "string",
                "Id": "security_id",
                "Inputs": ["string"],
                "State": "IDLE",
                "Tags": {"marsha_live": "1"},
                "WhitelistRules": [{"Cidr": "0.0.0.0/0"}],
            }
        }

        with Stubber(medialive_utils.medialive_client) as medialive_stubber:
            medialive_stubber.add_response(
                "list_input_security_groups",
                service_response=list_security_group_response,
                expected_params={},
            )
            medialive_stubber.add_response(
                "create_input_security_group",
                service_response=created_security_group_response,
                expected_params={
                    "WhitelistRules": [{"Cidr": "0.0.0.0/0"}],
                    "Tags": {"marsha_live": "1"},
                },
            )

            security_group_id = medialive_utils.get_or_create_input_security_group()

            medialive_stubber.assert_no_pending_responses()

        self.assertEqual("security_id", security_group_id)

    def test_get_or_create_input_security_group_matching_tag(self):
        """Return an existing input security group matching marsha_live tag."""
        list_security_group_response = {
            "InputSecurityGroups": [
                {
                    "Arn": "string",
                    "Id": "tagged_security_group",
                    "Inputs": ["string"],
                    "State": "IDLE",
                    "Tags": {"marsha_live": "1"},
                    "WhitelistRules": [{"Cidr": "0.0.0.0/0"}],
                }
            ]
        }

        with Stubber(medialive_utils.medialive_client) as medialive_stubber:
            medialive_stubber.add_response(
                "list_input_security_groups",
                service_response=list_security_group_response,
                expected_params={},
            )

            security_group_id = medialive_utils.get_or_create_input_security_group()

            medialive_stubber.assert_no_pending_responses()

        self.assertEqual("tagged_security_group", security_group_id)

    def test_create_mediapackage_channel(self):
        """Create an AWS mediapackage channel."""
        key = "video-key"

        ssm_response = {"Version": 1, "Tier": "Standard"}
        mediapackage_create_channel_response = {
            "Id": "channel1",
            "HlsIngest": {
                "IngestEndpoints": [
                    {
                        "Id": "ingest1",
                        "Password": "password1",
                        "Url": "https://endpoint1/channel",
                        "Username": "user1",
                    },
                    {
                        "Id": "ingest2",
                        "Password": "password2",
                        "Url": "https://endpoint2/channel",
                        "Username": "user2",
                    },
                ]
            },
        }
        mediapackage_create_cmaf_origin_endpoint_response = {
            "ChannelId": "channel1",
            "CmafPackage": {
                "HlsManifests": [
                    {
                        "Id": "origin_endpoint1",
                        "Url": "https://endpoint1/channel.m3u8",
                    },
                ],
            },
            "Id": "enpoint1",
        }

        mediapackage_create_dash_origin_endpoint_response = {
            "ChannelId": "channel1",
            "Id": "enpoint2",
            "Url": "https://endpoint2/channel-dash.mpd",
        }

        with Stubber(
            medialive_utils.mediapackage_client
        ) as mediapackage_stubber, Stubber(medialive_utils.ssm_client) as ssm_stubber:
            mediapackage_stubber.add_response(
                "create_channel",
                service_response=mediapackage_create_channel_response,
                expected_params={"Id": key},
            )
            ssm_stubber.add_response(
                "put_parameter",
                service_response=ssm_response,
                expected_params={
                    "Name": "user1",
                    "Description": "video-key MediaPackage Primary Ingest Username",
                    "Value": "password1",
                    "Type": "String",
                },
            )
            ssm_stubber.add_response(
                "put_parameter",
                service_response=ssm_response,
                expected_params={
                    "Name": "user2",
                    "Description": "video-key MediaPackage Secondary Ingest Username",
                    "Value": "password2",
                    "Type": "String",
                },
            )
            mediapackage_stubber.add_response(
                "create_origin_endpoint",
                service_response=mediapackage_create_cmaf_origin_endpoint_response,
                expected_params={
                    "ChannelId": "channel1",
                    "Id": "channel1-cmaf",
                    "ManifestName": "channel1-cmaf",
                    "StartoverWindowSeconds": 0,
                    "TimeDelaySeconds": 0,
                    "CmafPackage": {
                        "HlsManifests": [
                            {
                                "Id": "channel1-cmaf-hls",
                                "AdMarkers": "PASSTHROUGH",
                                "IncludeIframeOnlyStream": False,
                                "ManifestName": key,
                                "PlaylistType": "EVENT",
                                "PlaylistWindowSeconds": 60,
                                "ProgramDateTimeIntervalSeconds": 0,
                            },
                        ],
                        "SegmentDurationSeconds": 6,
                        "SegmentPrefix": "channel1",
                    },
                },
            )

            mediapackage_stubber.add_response(
                "create_origin_endpoint",
                service_response=mediapackage_create_dash_origin_endpoint_response,
                expected_params={
                    "ChannelId": "channel1",
                    "Id": "channel1-dash",
                    "ManifestName": "channel1-dash",
                    "StartoverWindowSeconds": 0,
                    "TimeDelaySeconds": 0,
                    "DashPackage": {
                        "SegmentDurationSeconds": 2,
                        "ManifestWindowSeconds": 60,
                        "Profile": "NONE",
                        "MinUpdatePeriodSeconds": 15,
                        "MinBufferTimeSeconds": 30,
                        "SuggestedPresentationDelaySeconds": 25,
                        "PeriodTriggers": [],
                        "ManifestLayout": "FULL",
                        "SegmentTemplateFormat": "NUMBER_WITH_TIMELINE",
                    },
                },
            )

            [
                channel,
                cmaf_endpoint,
                dash_endpoint,
            ] = medialive_utils.create_mediapackage_channel(key)

            mediapackage_stubber.assert_no_pending_responses()
            ssm_stubber.assert_no_pending_responses()

        self.assertEqual(channel, mediapackage_create_channel_response)
        self.assertEqual(
            cmaf_endpoint, mediapackage_create_cmaf_origin_endpoint_response
        )
        self.assertEqual(
            dash_endpoint, mediapackage_create_dash_origin_endpoint_response
        )

    def test_create_medialive_input(self):
        """Create and return an AWS medialive input."""
        key = "video-key"

        medialive_create_input_response = {
            "Input": {
                "Id": "input1",
                "Destinations": [
                    {"Url": "rtmp://destination1/video-key-primary"},
                    {"Url": "rtmp://destination2/video-key-secondary"},
                ],
            },
        }

        with Stubber(
            medialive_utils.medialive_client
        ) as medialive_stubber, mock.patch.object(
            medialive_utils,
            "get_or_create_input_security_group",
            return_value="security_group_1",
        ):
            medialive_stubber.add_response(
                "create_input",
                service_response=medialive_create_input_response,
                expected_params={
                    "InputSecurityGroups": ["security_group_1"],
                    "Name": key,
                    "Type": "RTMP_PUSH",
                    "Destinations": [
                        {"StreamName": "video-key-primary"},
                        {"StreamName": "video-key-secondary"},
                    ],
                },
            )

            response = medialive_utils.create_medialive_input(key)
            medialive_stubber.assert_no_pending_responses()

        self.assertEqual(response, medialive_create_input_response)

    @override_settings(AWS_MEDIALIVE_ROLE_ARN="medialive:role:arn")
    def test_create_medialive_channel(self):
        """Create an AWS medialive channel."""
        key = "video-key"

        medialive_input = {
            "Input": {"Id": "input1"},
        }
        mediapackage_channel = {
            "Id": "channel1",
            "HlsIngest": {
                "IngestEndpoints": [
                    {
                        "Id": "ingest1",
                        "Password": "password1",
                        "Url": "https://endpoint1/channel",
                        "Username": "user1",
                    },
                    {
                        "Id": "ingest2",
                        "Password": "password2",
                        "Url": "https://endpoint2/channel",
                        "Username": "user2",
                    },
                ]
            },
        }
        medialive_channel_response = {"Channel": {"Id": "medialive_channel1"}}

        with Stubber(medialive_utils.medialive_client) as medialive_stubber:
            medialive_stubber.add_response(
                "create_channel",
                service_response=medialive_channel_response,
                expected_params={
                    "InputSpecification": {
                        "Codec": "AVC",
                        "Resolution": "HD",
                        "MaximumBitrate": "MAX_10_MBPS",
                    },
                    "InputAttachments": [{"InputId": "input1"}],
                    "Destinations": [
                        {
                            "Id": "destination1",
                            "Settings": [
                                {
                                    "PasswordParam": "user1",
                                    "Url": "https://endpoint1/channel",
                                    "Username": "user1",
                                },
                                {
                                    "PasswordParam": "user2",
                                    "Url": "https://endpoint2/channel",
                                    "Username": "user2",
                                },
                            ],
                        }
                    ],
                    "Name": key,
                    "RoleArn": "medialive:role:arn",
                    "EncoderSettings": ANY,
                },
            )

            response = medialive_utils.create_medialive_channel(
                key, medialive_input, mediapackage_channel
            )
            medialive_stubber.assert_no_pending_responses()

        self.assertEqual(medialive_channel_response, response)

    def test_create_live_stream(self):
        """Should create all AWS medialive stack."""
        key = "video-key"

        with mock.patch.object(
            medialive_utils, "create_mediapackage_channel"
        ) as mock_mediapackage_channel, mock.patch.object(
            medialive_utils, "create_medialive_input"
        ) as mock_medialive_input, mock.patch.object(
            medialive_utils, "create_medialive_channel"
        ) as mock_medialive_channel:
            mock_mediapackage_channel.return_value = [
                {
                    "Id": "channel1",
                    "HlsIngest": {
                        "IngestEndpoints": [
                            {
                                "Id": "ingest1",
                                "Password": "password1",
                                "Url": "https://endpoint1/channel",
                                "Username": "user1",
                            },
                            {
                                "Id": "ingest2",
                                "Password": "password2",
                                "Url": "https://endpoint2/channel",
                                "Username": "user2",
                            },
                        ]
                    },
                },
                {
                    "ChannelId": "channel1",
                    "CmafPackage": {
                        "HlsManifests": [
                            {
                                "Id": "origin_endpoint1",
                                "Url": "https://endpoint1/channel.m3u8",
                            },
                        ],
                    },
                    "Id": "enpoint1",
                },
                {
                    "ChannelId": "channel1",
                    "Id": "enpoint2",
                    "Url": "https://endpoint2/channel-dash.mpd",
                },
            ]
            mock_medialive_input.return_value = {
                "Input": {
                    "Id": "input1",
                    "Destinations": [
                        {"Url": "rtmp://destination1/video-key-primary"},
                        {"Url": "rtmp://destination2/video-key-secondary"},
                    ],
                },
            }
            mock_medialive_channel.return_value = {
                "Channel": {"Id": "medialive_channel1"}
            }

            response = medialive_utils.create_live_stream(key)

        self.assertEqual(
            response,
            {
                "medialive": {
                    "input": {
                        "id": "input1",
                        "endpoints": [
                            "rtmp://destination1/video-key-primary",
                            "rtmp://destination2/video-key-secondary",
                        ],
                    },
                    "channel": {"id": "medialive_channel1"},
                },
                "mediapackage": {
                    "channel": {"id": "channel1"},
                    "endpoints": {
                        "cmaf": {
                            "id": "enpoint1",
                            "url": "https://endpoint1/channel.m3u8",
                        },
                        "dash": {
                            "id": "enpoint2",
                            "url": "https://endpoint2/channel-dash.mpd",
                        },
                    },
                },
            },
        )
