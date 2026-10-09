export interface Prediction { available:boolean; model:string; predicted_label:string|null; scores:Record<string,number>; score_kind:string; reason:string|null; frames_processed:number; frames_with_faces:number; ambiguous_frames:number }
export interface Evidence { audio:Prediction; visual:Prediction; transcript:{text:string;language:string|null;segments:{start:number;end:number;text:string}[]}; agreement:string; interpretation:string; uncertain:boolean }
export interface Feedback {id:string;choice:string;user_reported_emotion:string|null;optional_comment:string|null;timestamp:string}
export interface Observation {id:string;message_id:string;timestamp:string;evidence:Evidence;feedback:Feedback|null}
export interface Message {id:string;role:string;text:string;timestamp:string}
export interface Session {id:string;user_id:string;started_at:string;ended_at:string|null;summary:string|null}
export interface SessionDetail extends Session {messages:Message[];observations:Observation[]}
export interface User {id:string;name:string;created_at:string;memory_enabled:boolean}
export interface Memory {id:string;content:string;source:string;confirmed:boolean;created_at:string;updated_at:string}
export interface Profile {user:User;session_count:number;memories:Memory[];recent_sessions:Session[];feedback:Feedback[]}
export interface ModelStatus {state:'configured'|'loading'|'ready'|'unavailable'|'failed';detail:string}
export interface Health {status:string;max_recording_seconds:number;models:Record<string,ModelStatus>}
export interface Turn {session:SessionDetail;agent:{response:string;strategy:string;reason:string};memory_candidate:Memory|null}
export interface Preferences {language:string;cameraId:string;microphoneId:string;speak:boolean}
