'use strict';

const mockUpdateState = jest.fn();
jest.doMock('update-state', () => mockUpdateState);

// Mock the AWS SDK calls used in encodeTimedTextTrack
const mockDescribeChannel = jest.fn();
jest.mock('aws-sdk', () => ({
  MediaLive: function() {
    this.describeChannel = mockDescribeChannel;
  },
}));

const channelStateChanged = require('./channelStateChanged');

describe('src/channel_state_changed', () => {
  beforeEach(() => {
    jest.resetAllMocks();
  });

  it('receives an unhandled status and throws an error', async () => {
    const event = {
      "version": "0",
      "id": "0495e5eb-9b99-56f2-7849-96389238fb55",
      "detail-type": "MediaLive Channel State Change",
      "source": "aws.medialive",
      "account": "account_id",
      "time": "2020-06-15T15:18:29Z",
      "region": "eu-west-1",
      "resources": [
        "arn:aws:medialive:eu-west-1:account_id:channel:1234567"
      ],
      "detail": {
        "channel_arn": "arn:aws:medialive:eu-west-1:account_id:channel:1234567",
        "state": "STARTING",
        "message": "Created channel",
        "pipelines_running_count": 0
      }
    };

    try {
      await channelStateChanged(event);
    } catch (error) {
      expect(error.message).toEqual('Expected status are RUNNING and STOPPED. STARTING received');
    }

    expect.assertions(1);
  });

  it('receives a RUNNING event and update live state', async () => {
    const event = {
      "version": "0",
      "id": "0495e5eb-9b99-56f2-7849-96389238fb55",
      "detail-type": "MediaLive Channel State Change",
      "source": "aws.medialive",
      "account": "account_id",
      "time": "2020-06-15T15:18:29Z",
      "region": "eu-west-1",
      "resources": [
        "arn:aws:medialive:eu-west-1:account_id:channel:1234567"
      ],
      "detail": {
        "channel_arn": "arn:aws:medialive:eu-west-1:account_id:channel:1234567",
        "state": 'RUNNING',
        "message": "Created channel",
        "pipelines_running_count": 0
      }
    };

    mockDescribeChannel.mockReturnValue({
      promise: () =>
        new Promise(resolve => resolve({ Name: 'video-id_stamp' })),
    });

    await channelStateChanged(event);

    expect(mockUpdateState).toHaveBeenCalledWith('video-id', 'live');
    expect(mockDescribeChannel).toHaveBeenCalledWith({ ChannelId: '1234567' });

  });

  it('receives a STOPPED event and update live state', async () => {
    const event = {
      "version": "0",
      "id": "0495e5eb-9b99-56f2-7849-96389238fb55",
      "detail-type": "MediaLive Channel State Change",
      "source": "aws.medialive",
      "account": "account_id",
      "time": "2020-06-15T15:18:29Z",
      "region": "eu-west-1",
      "resources": [
        "arn:aws:medialive:eu-west-1:account_id:channel:1234567"
      ],
      "detail": {
        "channel_arn": "arn:aws:medialive:eu-west-1:account_id:channel:1234567",
        "state": 'STOPPED',
        "message": "Created channel",
        "pipelines_running_count": 0
      }
    };

    mockDescribeChannel.mockReturnValue({
      promise: () =>
        new Promise(resolve => resolve({ Name: 'video-id_stamp' })),
    });

    await channelStateChanged(event);

    expect(mockUpdateState).toHaveBeenCalledWith('video-id', 'stopped');
    expect(mockDescribeChannel).toHaveBeenCalledWith({ ChannelId: '1234567' });

  });
});
