import { useState, useEffect, useMemo } from 'react';
import { useSubscription, useQuery, gql } from '@apollo/client';
import { SUBSCRIBE_TO_CARD_FRAMES, SUBSCRIBE_TO_CARD_CLIPS, GET_CARD_FRAMES_AGGREGATE } from '@/lib/graphql/subscriptions';
import { Frame as AppFrame, DetectedFace as AppDetectedFace, Clip as AppClip } from '@/types';

interface DetectedFace {
  detection_id: string;
  face_matches: {
    match_id: string;
    consent_face: {
      consent_face_id: string;
      face_image_path: string;
      consent_profile: {
        person_name: string;
      }
    }
  }[];
}

interface Frame {
  frame_id: string;
  timestamp: string;
  raw_frame_image_path: string;
  processed_frame_image_path: string | null;
  status: string;
  clip: {
    clip_id: string;
    filename: string;
    status: string;
  };
  detected_faces_aggregate: {
    aggregate: {
      count: number;
    }
  };
  detected_faces: DetectedFace[];
}

interface Clip {
  clip_id: string;
  filename: string;
  status: string;
}

interface FramesData {
  frames: Frame[];
  frames_aggregate: {
    aggregate: {
      count: number;
    }
  }
}

interface ClipsData {
  clips: Clip[];
}

interface FrameFilters {
  clipId?: string;
  status?: string[];
  resultType?: 'all' | 'detected' | 'matched' | 'unmatched';
}

interface UseFrameResultsProps {
  projectId: string;
  cardId: string;
  limit?: number;
  page?: number;
  refreshKey?: number;
}

interface FramesAggregateData {
  frames_aggregate: {
    aggregate: {
      count: number;
    }
  }
}

export function useFrameResults({ 
  projectId, 
  cardId, 
  limit = 10, 
  page = 0,
  refreshKey = 0 
}: UseFrameResultsProps) {
  // Pagination state
  const [currentPage, setCurrentPage] = useState(page);
  const [rowsPerPage, setRowsPerPage] = useState(limit);
  
  // Filters state
  const [filters, setFilters] = useState<FrameFilters>({
    clipId: undefined,
    status: undefined,
    resultType: 'all',
  });
  
  // Calculate offset for pagination
  const offset = useMemo(() => currentPage * rowsPerPage, [currentPage, rowsPerPage]);
  
  // Common `where` clause used by both subscription and aggregate query
  const commonWhereClause = useMemo(() => {
    const whereConditions: any[] = [
      { clip: { card_id: { _eq: cardId } } } 
    ];

    if (filters.clipId) {
      whereConditions.push({ clip: { clip_id: { _eq: filters.clipId } } });
    }

    if (filters.status && filters.status.length > 0) {
      whereConditions.push({ status: { _in: filters.status } });
    }
    
    // Backend filtering for resultType
    if (filters.resultType === 'detected') {
      whereConditions.push({ detected_faces: { detection_id: { _is_null: false } } });
    }
    if (filters.resultType === 'matched') {
      whereConditions.push({
        detected_faces: {
          face_matches: { match_id: { _is_null: false } }
        }
      });
    }
    if (filters.resultType === 'unmatched') {
      whereConditions.push({
        detected_faces: { detection_id: { _is_null: false } },
        _not: {
          detected_faces: {
            face_matches: { match_id: { _is_null: false } }
          }
        }
      });
    }

    return { _and: whereConditions };
  }, [cardId, filters.clipId, filters.status, filters.resultType]);

  // Variables for the frame subscription
  const frameVariables = useMemo(() => ({
    limit: rowsPerPage,
    offset,
    where: commonWhereClause // Use the common where clause
  }), [rowsPerPage, offset, commonWhereClause]);
  
  // Variables for the aggregate query
  const aggregateVariables = useMemo(() => ({
    where: commonWhereClause // Use the same where clause
  }), [commonWhereClause]);

  // Variables for the clip subscription
  const clipVariables = useMemo(() => ({
    cardId,
  }), [cardId]);
  
  // Subscribe to frames data using Apollo Client's hook
  const { 
    data: framesData, 
    loading: framesLoading, 
    error: framesError 
  } = useSubscription<FramesData>(
    gql(SUBSCRIBE_TO_CARD_FRAMES), 
    { variables: frameVariables }
  );

  // Query for the total count of frames matching the filters
  const { 
    data: aggregateData, 
    loading: aggregateLoading, 
    error: aggregateError,
    refetch: refetchAggregate // Add refetch function
  } = useQuery<FramesAggregateData>(
    GET_CARD_FRAMES_AGGREGATE, 
    { variables: aggregateVariables }
  );
  
  // Refetch aggregate count when filters change
  useEffect(() => {
    refetchAggregate(aggregateVariables);
  }, [aggregateVariables, refetchAggregate]);

  // Subscribe to clips data for filter dropdown using Apollo Client's hook
  const { 
    data: clipsData, 
    loading: clipsLoading, 
    error: clipsError 
  } = useSubscription<ClipsData>(
    gql(SUBSCRIBE_TO_CARD_CLIPS),
    { variables: clipVariables }
  );
  
  // Process frames data - No client-side resultType filtering needed
  const processedFrames = useMemo(() => {
    if (!framesData?.frames) return [];
    return framesData.frames;
  }, [framesData]);
  
  // Get the actual total count from the aggregate query
  const totalCount = aggregateData?.frames_aggregate?.aggregate?.count || 0;
  
  // Available clips for filter dropdown
  const availableClips = clipsData?.clips || [];
  
  // Combine loading states
  const loading = framesLoading || clipsLoading || aggregateLoading;
  // Combine errors
  const error = framesError || clipsError || aggregateError;

  // Handle pagination change
  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage);
  };
  
  // Handle rows per page change
  const handleRowsPerPageChange = (newRowsPerPage: number) => {
    setRowsPerPage(newRowsPerPage);
    setCurrentPage(0);
  };
  
  // Handle filters change
  const handleFiltersChange = (newFilters: Partial<FrameFilters>) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
    setCurrentPage(0);
  };
  
  return {
    frames: processedFrames as unknown as AppFrame[],
    clips: availableClips as unknown as AppClip[],
    loading, // Combined loading state
    error,   // Combined error state
    pagination: {
      currentPage,
      rowsPerPage,
      totalCount, // Use the real total count
      handlePageChange,
      handleRowsPerPageChange,
    },
    filters: {
      current: filters,
      handleFiltersChange,
    },
  };
} 