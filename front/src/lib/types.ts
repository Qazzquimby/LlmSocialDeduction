/* tslint:disable */
/* eslint-disable */
/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
/* Do not modify it by hand - just update the pydantic models and then re-run the script
*/

export interface BaseMessage {
  type: string;
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
  player: string;
  action: string;
  message?: string | null;
}
export interface PromptMessage {
  type?: string;
  message: string;
}
export interface SpeechMessage {
  type?: string;
  username: string;
  message: string;
}
