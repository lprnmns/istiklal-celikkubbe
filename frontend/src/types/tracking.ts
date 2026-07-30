/**
 * Tracking Types — Kapalı çevrim hedef takip sistemi TypeScript tipleri.
 */

export type TrackingState =
  | 'IDLE'
  | 'SEARCHING'
  | 'TRACKING'
  | 'LOCKED'
  | 'TARGET_LOST'
  | 'STOPPED'
  | 'ERROR'

export interface TrackingUpdate {
  state: TrackingState
  speed_x: number
  speed_y: number
  error_x_px: number
  error_y_px: number
  raw_pid_x: number
  raw_pid_y: number
  target_center_x: number | null
  target_center_y: number | null
  frame_center_x: number
  frame_center_y: number
  aim_offset_x_px: number
  aim_offset_y_px: number
  target_lost_frames: number
  distance_to_center: number
  deadband_zone: string
  using_kalman_prediction: boolean
  lead_horizon_ms: number
  predicted_target_center_x: number | null
  predicted_target_center_y: number | null
  frame_id: number
  dt: number
  updated_at: number
}

export interface TrackingFireResult {
  accepted: boolean
  command: string
  reason_codes: string[]
  detail: string
  physical_command_generated: boolean
  updated_at: number
}

export interface MultiTargetTrack {
  track_id: number
  detection_id: number | null
  center_x: number
  center_y: number
  velocity_x: number
  velocity_y: number
  age_frames: number
  hits: number
  misses: number
  confidence: number
  predicted: boolean
  fresh: boolean
  updated_at: number
}

export interface MultiTargetTrackingStatus {
  tracker_kind: string
  active_track_count: number
  tracks: MultiTargetTrack[]
  updated_at: number
}

export interface TargetPriorityCandidate {
  balloon_track_id: number
  body_detection_id: number
  score: number
  time_to_exit_s: number | null
  solution_quality: number
  return_cost: number
  reasons: string[]
}

export interface TargetPriorityStatus {
  selected_track_id: number | null
  ranked_candidates: TargetPriorityCandidate[]
  excluded_track_ids: number[]
  updated_at: number
}

export interface TrackingStatus {
  active: boolean
  state: TrackingState
  target_count: number
  lost_count: number
  total_frames: number
  pid_kp_x: number
  pid_ki_x: number
  pid_kd_x: number
  pid_kp_y: number
  pid_ki_y: number
  pid_kd_y: number
  smoothing_alpha: number
  command_rate_hz: number
  max_speed: number
  aim_offset_x_px: number
  aim_offset_y_px: number
  invert_x: boolean
  invert_y: boolean
  lead_enabled: boolean
  lead_latency_multiplier: number
  lead_max_horizon_ms: number
  preferred_target_x?: number | null
  preferred_target_y?: number | null
  last_update: TrackingUpdate | null
  last_fire_result: TrackingFireResult | null
  multi_target_tracker: MultiTargetTrackingStatus
  updated_at: number
}

export interface TrackingConfigUpdate {
  pid_kp_x?: number
  pid_ki_x?: number
  pid_kd_x?: number
  pid_kp_y?: number
  pid_ki_y?: number
  pid_kd_y?: number
  smoothing_alpha?: number
  command_rate_hz?: number
  max_speed?: number
  aim_offset_x_px?: number
  aim_offset_y_px?: number
  invert_x?: boolean
  invert_y?: boolean
  lead_enabled?: boolean
  lead_latency_multiplier?: number
  lead_max_horizon_ms?: number
  max_lost_frames?: number
}
