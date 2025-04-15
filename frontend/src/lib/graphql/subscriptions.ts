import { gql } from '@apollo/client';

export const SUBSCRIBE_TO_CARD_FRAMES = `
  subscription SubscribeToCardFrames(
    $limit: Int!, 
    $offset: Int!, 
    $where: frames_bool_exp!
  ) {
    frames(
      where: $where,
      limit: $limit,
      offset: $offset,
      order_by: { timestamp: asc }
    ) {
      frame_id
      timestamp
      raw_frame_image_path
      processed_frame_image_path
      status
      clip {
        clip_id
        filename
        status
      }
      detected_faces_aggregate {
        aggregate {
          count
        }
      }
      detected_faces {
        detection_id
        face_matches {
          match_id
          consent_face {
            consent_face_id
            face_image_path
            consent_profile {
              person_name
            }
          }
        }
      }
    }
  }
`;

export const SUBSCRIBE_TO_CARD_CLIPS = `
  subscription SubscribeToCardClips($cardId: uuid!) {
    clips(where: { card_id: { _eq: $cardId } }) {
      clip_id
      filename
      status
    }
  }
`;

// New Query for fetching the aggregate count
export const GET_CARD_FRAMES_AGGREGATE = gql`
  query GetCardFramesAggregate($where: frames_bool_exp!) {
    frames_aggregate(where: $where) {
      aggregate {
        count
      }
    }
  }
`; 