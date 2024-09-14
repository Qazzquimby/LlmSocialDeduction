/* tslint:disable */
/* eslint-disable */
/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
/* Do not modify it by hand - just update the pydantic models and then re-run the script
*/

export interface BaseEvent {
  type: string;
}
export interface BaseMessage {
  type: string;
  message: string;
}
export interface GameConnectMessage {
  type?: string;
  message: string;
  gameId: string;
}
export interface GameStartedMessage {
  type?: string;
  players: string[];
}
export interface NextSpeakerMessage {
  type?: string;
  player: string;
}
export interface PhaseMessage {
  type?: string;
  phase: string;
}
export interface PlayerActionMessage {
  type?: string;
  message?: string | null;
  player: string;
  action: string;
}
export interface PromptMessage {
  type?: string;
  message: string;
}
export interface SpeechMessage {
  type?: string;
  message: string;
  username: string;
}
