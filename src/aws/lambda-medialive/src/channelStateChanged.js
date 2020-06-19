const AWS = require('aws-sdk');
const updateState = require('update-state');

const mediaLive = new AWS.MediaLive({ apiVersion: '2017-10-14' });

module.exports = async (event) => {
  const status = event.detail.state;
  const marshaStatus = {
    RUNNING: "live",
    STOPPED: "stopped"
  }

  if (!["RUNNING", "STOPPED"].includes(status)) {
    throw new Error(`Expected status are RUNNING and STOPPED. ${status} received`);
  }

  const arn_regex = /^arn:aws:medialive:.*:.*:channel:(.*)$/

  const arn = event.detail.channel_arn;
  const matches = arn.match(arn_regex);
  
  const channel = await mediaLive.describeChannel({
    ChannelId: matches[1]
  }).promise();

  const videoId = channel.Name.split("_")[0];

  return await updateState(videoId, marshaStatus[status]);
};

