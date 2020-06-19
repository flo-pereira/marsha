"""Utils to create MediaLive configuration."""
import json
import os

from django.conf import settings

import boto3


# Configure medialive client
medialive_client = boto3.client(
    "medialive",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_S3_REGION_NAME,
)

# Configure mediapackage client
mediapackage_client = boto3.client(
    "mediapackage",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_S3_REGION_NAME,
)

# Configure SSM client
ssm_client = boto3.client(
    "ssm",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_S3_REGION_NAME,
)


def create_mediapackage_channel(key):
    """Create an AWS mediapackage channel.

    An endpoint is created and attached to this channel and password
    are added in SSM service.

    Parameters
    ----------
    key : string
        key representing the video in AWS

    Returns
    -------
    dictionnary
        Dictrionnary returned by the AWS API once a channel created

    """
    # Create mediapackage channel
    channel = mediapackage_client.create_channel(Id=key)

    # Add primary U/P to SSM parameter store
    ssm_client.put_parameter(
        Name=channel["HlsIngest"]["IngestEndpoints"][0]["Username"],
        Description=f"{key} MediaPackage Primary Ingest Username",
        Value=channel["HlsIngest"]["IngestEndpoints"][0]["Password"],
        Type="String",
    )

    # Add Secondary U/P to SSM Parameter store
    ssm_client.put_parameter(
        Name=channel["HlsIngest"]["IngestEndpoints"][1]["Username"],
        Description=f"{key} MediaPackage Secondary Ingest Username",
        Value=channel["HlsIngest"]["IngestEndpoints"][1]["Password"],
        Type="String",
    )

    # Create an endpoint. This endpoint will be used to whatch the stream.
    cmaf_endpoint = mediapackage_client.create_origin_endpoint(
        ChannelId=channel["Id"],
        Id=f"{channel['Id']}-cmaf",
        ManifestName=f"{channel['Id']}-cmaf",
        StartoverWindowSeconds=0,
        TimeDelaySeconds=0,
        CmafPackage={
            "HlsManifests": [
                {
                    "Id": f"{channel['Id']}-cmaf-hls",
                    "AdMarkers": "PASSTHROUGH",
                    "IncludeIframeOnlyStream": False,
                    "ManifestName": key,
                    "PlaylistType": "EVENT",
                    "PlaylistWindowSeconds": 60,
                    "ProgramDateTimeIntervalSeconds": 0,
                },
            ],
            "SegmentDurationSeconds": 6,
            "SegmentPrefix": channel["Id"],
        },
    )

    dash_endpoint = mediapackage_client.create_origin_endpoint(
        ChannelId=channel["Id"],
        Id=f"{channel['Id']}-dash",
        ManifestName=f"{channel['Id']}-dash",
        StartoverWindowSeconds=0,
        TimeDelaySeconds=0,
        DashPackage={
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
    )

    return [channel, cmaf_endpoint, dash_endpoint]


def get_or_create_input_security_group():
    """Create or fetch an existing security group.

    Number of input security group are limited to 5 by default. We create one and after
    we only this one. To identify it we tag it with marsha_live label.

    Returns
    -------
    string
        The input security group to use
    """
    input_security_groups = medialive_client.list_input_security_groups()

    for input_security_group in input_security_groups["InputSecurityGroups"]:
        if input_security_group["Tags"].get("marsha_live"):
            return input_security_group["Id"]

    security_group = medialive_client.create_input_security_group(
        WhitelistRules=[{"Cidr": "0.0.0.0/0"}], Tags={"marsha_live": "1"}
    )

    return security_group["SecurityGroup"]["Id"]


def create_medialive_input(key):
    """Create AWS medialive input.

    The medialive input is created to receive a RTMP stream from OBS for example.
    The security group used accept all incoming traffic, there is no IP restriction.

    Parameters
    ----------
    key : string
        key representing the video in AWS

    Returns
    -------
    dictionnary
        Dictrionnary returned by the AWS API once a medialive input is created
    """
    medialive_input = medialive_client.create_input(
        InputSecurityGroups=[get_or_create_input_security_group()],
        Name=key,
        Type="RTMP_PUSH",
        Destinations=[
            {"StreamName": f"{key}-primary"},
            {"StreamName": f"{key}-secondary"},
        ],
    )

    return medialive_input


def create_medialive_channel(key, medialive_input, mediapackage_channel):
    """Create an AWS medialive channel.

    The medialive channel is the glue between medialive input and mediapackage channel.
    The encoding is also managed here. All encoding parameters come from a json file
    stored in marsha/core/utils/medialive_profiles

    Parameters
    ----------
    key : string
        key representing the video in AWS

    medialive_input: dictionnary
        dictionnary containing newly created medialive input

    mediapackage_channel: dictionnary
        dictionnary containing newly created mediapackage channel

    Returns
    -------
    dictionnary
        Dictrionnary returned by the AWS API once a medialive channel is created
    """
    dir_path = os.path.dirname(os.path.realpath(__file__))
    with open(f"{dir_path}/medialive_profiles/medialive-720p.json") as encoding:
        encoder_settings = json.load(encoding)

    medialive_channel = medialive_client.create_channel(
        InputSpecification={
            "Codec": "AVC",
            "Resolution": "HD",
            "MaximumBitrate": "MAX_10_MBPS",
        },
        InputAttachments=[{"InputId": medialive_input["Input"]["Id"]}],
        Destinations=[
            {
                "Id": "destination1",
                "Settings": [
                    {
                        "PasswordParam": mediapackage_channel["HlsIngest"][
                            "IngestEndpoints"
                        ][0]["Username"],
                        "Url": mediapackage_channel["HlsIngest"]["IngestEndpoints"][0][
                            "Url"
                        ],
                        "Username": mediapackage_channel["HlsIngest"][
                            "IngestEndpoints"
                        ][0]["Username"],
                    },
                    {
                        "PasswordParam": mediapackage_channel["HlsIngest"][
                            "IngestEndpoints"
                        ][1]["Username"],
                        "Url": mediapackage_channel["HlsIngest"]["IngestEndpoints"][1][
                            "Url"
                        ],
                        "Username": mediapackage_channel["HlsIngest"][
                            "IngestEndpoints"
                        ][1]["Username"],
                    },
                ],
            }
        ],
        Name=key,
        RoleArn=settings.AWS_MEDIALIVE_ROLE_ARN,
        EncoderSettings=encoder_settings,
    )

    return medialive_channel


def create_live_stream(key):
    """Create all AWS stack needed to stream a video.

    Parameters
    ----------
    key : string
        key representing the video in AWS

    Returns
    -------
    dictionnary
        Dictrionnary containing all information to store in order to manage
        a live stream life cycle.
    """
    mediapackage_channel, cmaf_endpoint, dash_endpoint = create_mediapackage_channel(
        key
    )
    medialive_input = create_medialive_input(key)

    medialive_channel = create_medialive_channel(
        key, medialive_input, mediapackage_channel
    )

    return {
        "medialive": {
            "input": {
                "id": medialive_input["Input"]["Id"],
                "endpoints": [
                    medialive_input["Input"]["Destinations"][0]["Url"],
                    medialive_input["Input"]["Destinations"][1]["Url"],
                ],
            },
            "channel": {"id": medialive_channel["Channel"]["Id"]},
        },
        "mediapackage": {
            "channel": {"id": mediapackage_channel["Id"]},
            "endpoints": {
                "cmaf": {
                    "id": cmaf_endpoint["Id"],
                    "url": cmaf_endpoint["CmafPackage"]["HlsManifests"][0]["Url"],
                },
                "dash": {"id": dash_endpoint["Id"], "url": dash_endpoint["Url"]},
            },
        },
    }


def start_medialive_channel(channel_id):
    """Start an existing medialive channel."""
    medialive_client.start_channel(ChannelId=channel_id)

