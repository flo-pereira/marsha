import { Button } from 'grommet';
import React, { useState } from 'react';
import { defineMessages, FormattedMessage } from 'react-intl';
import { Redirect } from 'react-router-dom';
import styled from 'styled-components';

import { stopLive } from '../../data/sideEffects/stopLive';
import { useVideo } from '../../data/stores/useVideo';
import { Video } from '../../types/tracks';
import { Nullable } from '../../utils/types';
import { dashboardButtonStyles } from '../DashboardPaneButtons';
import { ERROR_COMPONENT_ROUTE } from '../ErrorComponent/route';
import { Loader } from '../Loader';

const messages = defineMessages({
  stopLive: {
    defaultMessage: 'stop streaming',
    description: 'Stop a video streaming.',
    id: 'components.DashboardVideoLiveStopButton.startLive',
  },
});

const StartLiveButton = styled(Button)`
  ${dashboardButtonStyles}
`;

type startLiveStatus = 'pending' | 'error';

interface DashboardVideoLiveStartButtonProps {
  video: Video;
}

export const DashboardVideoLiveStopButton = ({
  video,
}: DashboardVideoLiveStartButtonProps) => {
  const [status, setStatus] = useState<Nullable<startLiveStatus>>(null);
  const { updateVideo } = useVideo((state) => ({
    updateVideo: state.addResource,
  }));

  const stopLiveAction = async () => {
    setStatus('pending');
    try {
      const updatedVideo = await stopLive(video);
      updateVideo(updatedVideo);
    } catch (error) {
      setStatus('error');
    }
  };

  if (status === 'error') {
    return <Redirect push to={ERROR_COMPONENT_ROUTE('liveInit')} />;
  }

  return (
    <React.Fragment>
      {status === 'pending' && <Loader />}
      <StartLiveButton
        label={<FormattedMessage {...messages.stopLive} />}
        primary={true}
        onClick={stopLiveAction}
      />
    </React.Fragment>
  );
};
