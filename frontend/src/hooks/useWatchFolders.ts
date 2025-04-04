'use client';

import { useState } from 'react';
import { useMutation } from '@apollo/client';
import { ADD_WATCH_FOLDER, REMOVE_WATCH_FOLDER, UPDATE_WATCH_FOLDER_STATUS, GET_CARD_CONFIG } from '@/lib/graphql/queries';
import { WatchFolder } from '@/hooks/useCardConfig';

export function useWatchFolders(configId: string, cardId: string) {
  const [adding, setAdding] = useState(false);
  const [removing, setRemoving] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  
  const [addWatchFolder] = useMutation(ADD_WATCH_FOLDER, {
    onCompleted: () => {
      setAdding(false);
      setError(null);
    },
    onError: (error) => {
      setAdding(false);
      setError(error);
    },
    refetchQueries: [{ 
      query: GET_CARD_CONFIG, 
      variables: { cardId } 
    }],
  });

  const [removeWatchFolder] = useMutation(REMOVE_WATCH_FOLDER, {
    onCompleted: () => {
      setRemoving(false);
      setError(null);
    },
    onError: (error) => {
      setRemoving(false);
      setError(error);
    },
    refetchQueries: [{ 
      query: GET_CARD_CONFIG, 
      variables: { cardId } 
    }],
  });

  const [updateWatchFolderStatus] = useMutation(UPDATE_WATCH_FOLDER_STATUS, {
    onCompleted: () => {
      setUpdating(false);
      setError(null);
    },
    onError: (error) => {
      setUpdating(false);
      setError(error);
    },
    refetchQueries: [{ 
      query: GET_CARD_CONFIG, 
      variables: { cardId } 
    }],
  });

  const addFolder = async (folderPath: string) => {
    setAdding(true);
    try {
      await addWatchFolder({
        variables: {
          configId,
          folderPath
        }
      });
    } catch (err: any) {
      // Check if this is a unique constraint violation
      if (err instanceof Error && 
          (err.message.includes('watch_folder_config_id_key') || 
          err.message.includes('unique constraint'))) {
        throw new Error('This folder is already being watched. Please choose a different folder.');
      }
      // Re-throw original error for other cases
      throw err;
    }
  };

  const removeFolder = async (watchFolderId: string) => {
    setRemoving(true);
    try {
      await removeWatchFolder({
        variables: {
          watchFolderId
        }
      });
    } catch (err) {
      // Error is handled in onError
    }
  };

  const updateFolderStatus = async (watchFolderId: string, status: string) => {
    setUpdating(true);
    try {
      await updateWatchFolderStatus({
        variables: {
          watchFolderId,
          status
        }
      });
    } catch (err) {
      // Error is handled in onError
      throw err;
    }
  };

  return {
    addFolder,
    removeFolder,
    updateFolderStatus,
    adding,
    removing,
    updating,
    error
  };
} 